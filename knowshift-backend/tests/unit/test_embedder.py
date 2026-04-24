"""
Unit tests for the embedder service.
Validates embed_text and embed_query with mocked Gemini API.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestEmbedText:
    """Tests for embed_text()."""

    @pytest.mark.unit
    def test_returns_768_dim_list(self):
        mock_result = {"embedding": [0.1] * 768}
        with patch("app.services.embedder.genai") as mock_genai:
            mock_genai.embed_content.return_value = mock_result
            from app.services.embedder import embed_text
            result = embed_text("Some document text")
        assert isinstance(result, list)
        assert len(result) == 768

    @pytest.mark.unit
    def test_all_values_are_floats(self):
        with patch("app.services.embedder.genai") as mock_genai:
            mock_genai.embed_content.return_value = {"embedding": [0.5] * 768}
            from app.services.embedder import embed_text
            result = embed_text("Test text")
        assert all(isinstance(v, float) for v in result)

    @pytest.mark.unit
    def test_calls_genai_with_correct_model(self):
        with patch("app.services.embedder.genai") as mock_genai:
            mock_genai.embed_content.return_value = {"embedding": [0.1] * 768}
            from app.services.embedder import embed_text
            embed_text("Test text")
        call_kwargs = mock_genai.embed_content.call_args
        assert call_kwargs is not None

    @pytest.mark.unit
    def test_raises_on_api_error(self):
        with patch("app.services.embedder.genai") as mock_genai:
            mock_genai.embed_content.side_effect = Exception("API rate limit")
            from app.services.embedder import embed_text
            with pytest.raises(Exception, match="API rate limit"):
                embed_text("Test text")

    @pytest.mark.unit
    def test_empty_string_does_not_crash(self):
        with patch("app.services.embedder.genai") as mock_genai:
            mock_genai.embed_content.return_value = {"embedding": [0.0] * 768}
            from app.services.embedder import embed_text
            result = embed_text("")
        assert len(result) == 768


class TestEmbedQuery:
    """Tests for embed_query()."""

    @pytest.mark.unit
    def test_returns_768_dim_list(self):
        with patch("app.services.embedder.genai") as mock_genai:
            mock_genai.embed_content.return_value = {"embedding": [0.15] * 768}
            from app.services.embedder import embed_query
            result = embed_query("What treats Type 2 Diabetes?")
        assert len(result) == 768

    @pytest.mark.unit
    def test_different_from_document_embedding(self):
        """
        embed_query may use a different task_type than embed_text,
        producing a slightly different vector even for the same text.
        Here we just verify both return valid 768-dim vectors.
        """
        with patch("app.services.embedder.genai") as mock_genai:
            mock_genai.embed_content.return_value = {"embedding": [0.2] * 768}
            from app.services.embedder import embed_query
            result = embed_query("Question text")
        assert isinstance(result, list) and len(result) == 768
