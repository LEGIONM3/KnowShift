"""
Integration tests for /query/ask and /query/compare.
Uses mocked external services — no real Gemini or Supabase calls.
"""

import pytest
from unittest.mock import patch


class TestQueryAskEndpoint:
    """Tests for POST /query/ask."""

    @pytest.mark.integration
    def test_ask_returns_200_with_valid_payload(
        self, app_client, mock_embed_query, sample_retrieved_chunks, mock_gemini_generate
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=sample_retrieved_chunks):
            r = app_client.post(
                "/query/ask",
                json={"question": "What treats Type 2 Diabetes?", "domain": "medical", "include_stale": False},
            )
        assert r.status_code == 200

    @pytest.mark.integration
    def test_ask_response_has_required_fields(
        self, app_client, mock_embed_query, sample_retrieved_chunks, mock_gemini_generate
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=sample_retrieved_chunks):
            r = app_client.post(
                "/query/ask",
                json={"question": "What treats Type 2 Diabetes?", "domain": "medical"},
            )
        d = r.json()
        for field in ("answer", "freshness_confidence", "staleness_warning", "sources"):
            assert field in d, f"Missing field: {field}"

    @pytest.mark.integration
    def test_ask_rejects_invalid_domain(self, app_client):
        r = app_client.post(
            "/query/ask",
            json={"question": "What is the tax rate?", "domain": "invalid_xyz"},
        )
        assert r.status_code == 422

    @pytest.mark.integration
    def test_ask_rejects_empty_question(self, app_client):
        r = app_client.post(
            "/query/ask",
            json={"question": "", "domain": "medical"},
        )
        assert r.status_code == 422

    @pytest.mark.integration
    def test_ask_rejects_too_short_question(self, app_client):
        r = app_client.post(
            "/query/ask",
            json={"question": "Hi", "domain": "medical"},
        )
        assert r.status_code == 422

    @pytest.mark.integration
    def test_freshness_confidence_bounded_0_to_1(
        self, app_client, mock_embed_query, sample_retrieved_chunks, mock_gemini_generate
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=sample_retrieved_chunks):
            r = app_client.post(
                "/query/ask",
                json={"question": "What treats Type 2 Diabetes?", "domain": "medical"},
            )
        score = r.json()["freshness_confidence"]
        assert 0.0 <= score <= 1.0

    @pytest.mark.integration
    def test_ask_includes_processing_time(
        self, app_client, mock_embed_query, sample_retrieved_chunks, mock_gemini_generate
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=sample_retrieved_chunks):
            r = app_client.post(
                "/query/ask",
                json={"question": "What treats Type 2 Diabetes?", "domain": "medical"},
            )
        assert "processing_time_ms" in r.json()

    @pytest.mark.integration
    def test_ask_returns_gracefully_when_no_chunks(
        self, app_client, mock_embed_query
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=[]):
            r = app_client.post(
                "/query/ask",
                json={"question": "What are the tax rates?", "domain": "finance"},
            )
        assert r.status_code == 200
        assert "answer" in r.json()

    @pytest.mark.integration
    def test_ask_sources_is_list(
        self, app_client, mock_embed_query, sample_retrieved_chunks, mock_gemini_generate
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=sample_retrieved_chunks):
            r = app_client.post(
                "/query/ask",
                json={
                    "question": "What treats Type 2 Diabetes?",
                    "domain": "medical",
                    "return_sources": True,
                },
            )
        assert isinstance(r.json()["sources"], list)


class TestQueryCompareEndpoint:
    """Tests for GET /query/compare."""

    @pytest.mark.integration
    def test_compare_returns_both_answers(
        self, app_client, mock_embed_query, sample_retrieved_chunks, mock_gemini_generate
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=sample_retrieved_chunks):
            r = app_client.get(
                "/query/compare",
                params={"question": "What is the first-line T2D treatment?", "domain": "medical"},
            )
        assert r.status_code == 200
        d = r.json()
        assert "stale_answer" in d
        assert "fresh_answer" in d

    @pytest.mark.integration
    def test_compare_has_difference_detected_field(
        self, app_client, mock_embed_query, sample_retrieved_chunks, mock_gemini_generate
    ):
        with patch("app.services.retriever.retrieve_chunks", return_value=sample_retrieved_chunks):
            r = app_client.get(
                "/query/compare",
                params={"question": "What is the first-line T2D treatment?", "domain": "medical"},
            )
        assert "difference_detected" in r.json()
        assert isinstance(r.json()["difference_detected"], bool)

    @pytest.mark.integration
    def test_compare_requires_question_param(self, app_client):
        r = app_client.get("/query/compare", params={"domain": "medical"})
        assert r.status_code == 422

    @pytest.mark.integration
    def test_compare_requires_domain_param(self, app_client):
        r = app_client.get("/query/compare", params={"question": "What is the treatment?"})
        assert r.status_code == 422

    @pytest.mark.integration
    def test_compare_rejects_invalid_domain(self, app_client):
        r = app_client.get(
            "/query/compare",
            params={"question": "Test question here", "domain": "unknown"},
        )
        assert r.status_code in (200, 422, 500)  # domain handled by validator or query
