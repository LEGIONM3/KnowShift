"""
Unit tests for the vector retriever service (retriever.py).
Uses mocked Supabase — no real DB calls.
NOTE: retrieve_chunks() catches exceptions and returns [] (graceful degradation).
Tests are written to match that documented behaviour.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestRetrieveChunks:
    """Tests for retrieve_chunks()."""

    @pytest.mark.unit
    def test_returns_list(self):
        with patch("app.services.retriever.supabase") as mock_db:
            mock_db.rpc.return_value.execute.return_value.data = []
            from app.services.retriever import retrieve_chunks
            result = retrieve_chunks([0.1] * 768, "medical", top_k=5, include_stale=False)
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_calls_match_chunks_rpc(self):
        with patch("app.services.retriever.supabase") as mock_db:
            mock_db.rpc.return_value.execute.return_value.data = []
            from app.services.retriever import retrieve_chunks
            retrieve_chunks([0.1] * 768, "medical", top_k=5, include_stale=False)
        mock_db.rpc.assert_called_once_with(
            "match_chunks",
            {
                "query_embedding": [0.1] * 768,
                "domain_filter":   "medical",
                "match_count":     5,
                "include_stale":   False,
            },
        )

    @pytest.mark.unit
    def test_passes_correct_top_k(self):
        with patch("app.services.retriever.supabase") as mock_db:
            mock_db.rpc.return_value.execute.return_value.data = []
            from app.services.retriever import retrieve_chunks
            retrieve_chunks([0.1] * 768, "medical", top_k=3, include_stale=False)
        call_kwargs = mock_db.rpc.call_args[0][1]
        assert call_kwargs["match_count"] == 3

    @pytest.mark.unit
    def test_returns_empty_list_when_no_results(self):
        with patch("app.services.retriever.supabase") as mock_db:
            mock_db.rpc.return_value.execute.return_value.data = []
            from app.services.retriever import retrieve_chunks
            result = retrieve_chunks([0.1] * 768, "finance", top_k=5, include_stale=False)
        assert result == []

    @pytest.mark.unit
    def test_returns_data_from_rpc(self):
        expected = [{"chunk_id": "c-1", "chunk_text": "test", "freshness_score": 0.9}]
        with patch("app.services.retriever.supabase") as mock_db:
            mock_db.rpc.return_value.execute.return_value.data = expected
            from app.services.retriever import retrieve_chunks
            result = retrieve_chunks([0.1] * 768, "medical", top_k=5, include_stale=False)
        assert result == expected

    @pytest.mark.unit
    def test_returns_empty_list_on_error_graceful_degradation(self):
        """retrieve_chunks catches exceptions and returns [] — this is its documented behaviour."""
        with patch("app.services.retriever.supabase") as mock_db:
            mock_db.rpc.return_value.execute.side_effect = Exception("DB error")
            from app.services.retriever import retrieve_chunks
            result = retrieve_chunks([0.1] * 768, "medical", top_k=5, include_stale=False)
        assert result == []  # graceful degradation, not a raise

    @pytest.mark.unit
    def test_include_stale_flag_passed_through(self):
        with patch("app.services.retriever.supabase") as mock_db:
            mock_db.rpc.return_value.execute.return_value.data = []
            from app.services.retriever import retrieve_chunks
            retrieve_chunks([0.1] * 768, "medical", top_k=5, include_stale=True)
        call_kwargs = mock_db.rpc.call_args[0][1]
        assert call_kwargs["include_stale"] is True
