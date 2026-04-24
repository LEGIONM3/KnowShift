"""
Integration tests for POST /ingest/upload.
Uses mocked external services — no real Supabase or Gemini calls.
"""

import pytest
from unittest.mock import patch, MagicMock

from tests.fixtures.sample_documents import MEDICAL_FRESH_TEXT


class TestIngestUploadEndpoint:
    """Tests for POST /ingest/upload."""

    @pytest.mark.integration
    def test_upload_returns_200_with_valid_pdf(
        self, app_client, mock_supabase, mock_embed_text, sample_pdf_bytes
    ):
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "doc-test-001"}
        ]
        with patch("app.services.chunker.extract_text_from_pdf", return_value=MEDICAL_FRESH_TEXT):
            r = app_client.post(
                "/ingest/upload",
                data={"domain": "medical", "source_name": "ADA Guidelines 2024"},
                files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            )
        assert r.status_code == 200
        d = r.json()
        assert "document_id" in d
        assert "chunks_ingested" in d
        assert d["chunks_ingested"] > 0

    @pytest.mark.integration
    def test_upload_requires_domain(self, app_client, sample_pdf_bytes):
        r = app_client.post(
            "/ingest/upload",
            data={"source_name": "No Domain Doc"},
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert r.status_code == 422

    @pytest.mark.integration
    def test_upload_requires_source_name(self, app_client, sample_pdf_bytes):
        r = app_client.post(
            "/ingest/upload",
            data={"domain": "medical"},
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert r.status_code == 422

    @pytest.mark.integration
    def test_upload_rejects_invalid_domain(self, app_client, sample_pdf_bytes):
        r = app_client.post(
            "/ingest/upload",
            data={"domain": "cooking_recipes", "source_name": "Test"},
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert r.status_code in (400, 422, 500)

    @pytest.mark.integration
    def test_upload_triggers_self_healing(
        self, app_client, mock_supabase, mock_embed_text, sample_pdf_bytes
    ):
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "doc-test-002"}
        ]
        with patch("app.services.chunker.extract_text_from_pdf", return_value=MEDICAL_FRESH_TEXT):
            with patch(
                "app.services.freshness_engine.selective_reindex",
                return_value={"deprecated_chunks": 3, "deprecated_ids": ["a", "b", "c"]},
            ):
                r = app_client.post(
                    "/ingest/upload",
                    data={"domain": "medical", "source_name": "New Guidelines 2024"},
                    files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
                )
        assert r.status_code == 200
        assert "deprecated_old_chunks" in r.json()

    @pytest.mark.integration
    def test_upload_returns_self_healing_flag(
        self, app_client, mock_supabase, mock_embed_text, sample_pdf_bytes
    ):
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "doc-test-003"}
        ]
        with patch("app.services.chunker.extract_text_from_pdf", return_value=MEDICAL_FRESH_TEXT):
            r = app_client.post(
                "/ingest/upload",
                data={"domain": "medical", "source_name": "Guidelines"},
                files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            )
        assert r.status_code == 200
        assert "self_healing_triggered" in r.json()
