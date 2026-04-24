"""
Unit tests for PDF text extraction and text chunking (chunker.py).
Both pdfplumber and langchain_text_splitters are stubbed in sys.modules
by conftest.py + additional stubs here, so no packages need to be installed.
"""

import io
import sys
import types
import pytest
from unittest.mock import MagicMock, patch


# ── Stub pdfplumber (may not be installed in the test environment) ────────────
if "pdfplumber" not in sys.modules:
    _pdfplumber_stub = types.ModuleType("pdfplumber")

    class _FakePdfContext:
        def __init__(self, pages):
            self.pages = pages
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    _pdfplumber_stub.open = MagicMock(
        return_value=_FakePdfContext(pages=[]),
    )
    sys.modules["pdfplumber"] = _pdfplumber_stub

# ── Stub langchain_text_splitters (may not be installed) ────────────────────
if "langchain_text_splitters" not in sys.modules:
    _lts_stub = types.ModuleType("langchain_text_splitters")

    class _FakeTextSplitter:
        def __init__(self, chunk_size=800, chunk_overlap=150,
                     separators=None, length_function=None):
            self.chunk_size    = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text: str):
            if not text or not text.strip():
                return []
            # Simulate chunking by slicing at chunk_size boundaries
            chunks = []
            step = max(self.chunk_size - self.chunk_overlap, 1)
            for i in range(0, len(text), step):
                chunk = text[i:i + self.chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
            return chunks

    _lts_stub.RecursiveCharacterTextSplitter = _FakeTextSplitter
    sys.modules["langchain_text_splitters"] = _lts_stub

# Import the actual module now that deps are stubbed
from app.services.chunker import extract_text_from_pdf, chunk_text


# ── extract_text_from_pdf ─────────────────────────────────────────────────────

class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf()."""

    @pytest.mark.unit
    def test_extracts_text_from_valid_pdf(self, sample_pdf_bytes):
        page = MagicMock()
        page.extract_text.return_value = "Sample medical text"

        with patch("pdfplumber.open") as mock_open:
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=MagicMock(pages=[page]))
            ctx.__exit__  = MagicMock(return_value=False)
            mock_open.return_value = ctx

            result = extract_text_from_pdf(sample_pdf_bytes)

        assert "Sample medical text" in result

    @pytest.mark.unit
    def test_handles_empty_pages_gracefully(self, sample_pdf_bytes):
        p1 = MagicMock(); p1.extract_text.return_value = "Page 1 content"
        p2 = MagicMock(); p2.extract_text.return_value = None  # empty page

        with patch("pdfplumber.open") as mock_open:
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=MagicMock(pages=[p1, p2]))
            ctx.__exit__  = MagicMock(return_value=False)
            mock_open.return_value = ctx

            result = extract_text_from_pdf(sample_pdf_bytes)

        assert "Page 1 content" in result
        assert result is not None

    @pytest.mark.unit
    def test_returns_string(self, sample_pdf_bytes):
        page = MagicMock(); page.extract_text.return_value = "text"

        with patch("pdfplumber.open") as mock_open:
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=MagicMock(pages=[page]))
            ctx.__exit__  = MagicMock(return_value=False)
            mock_open.return_value = ctx

            result = extract_text_from_pdf(sample_pdf_bytes)

        assert isinstance(result, str)

    @pytest.mark.unit
    def test_raises_value_error_on_empty_bytes(self):
        with pytest.raises(ValueError, match="empty"):
            extract_text_from_pdf(b"")

    @pytest.mark.unit
    def test_joins_pages_with_newline(self, sample_pdf_bytes):
        p1 = MagicMock(); p1.extract_text.return_value = "Page One"
        p2 = MagicMock(); p2.extract_text.return_value = "Page Two"

        with patch("pdfplumber.open") as mock_open:
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=MagicMock(pages=[p1, p2]))
            ctx.__exit__  = MagicMock(return_value=False)
            mock_open.return_value = ctx

            result = extract_text_from_pdf(sample_pdf_bytes)

        assert "Page One" in result
        assert "Page Two" in result


# ── chunk_text ────────────────────────────────────────────────────────────────

class TestChunkText:
    """Tests for chunk_text() — uses the stubbed RecursiveCharacterTextSplitter."""

    @pytest.mark.unit
    def test_returns_list_of_strings(self):
        chunks = chunk_text("This is a long text. " * 100)
        assert isinstance(chunks, list)
        assert all(isinstance(c, str) for c in chunks)

    @pytest.mark.unit
    def test_no_empty_chunks(self):
        chunks = chunk_text("Medical information. " * 100)
        assert all(len(c) > 0 for c in chunks)

    @pytest.mark.unit
    def test_short_text_single_chunk(self):
        text = "Short medical note about diabetes."
        chunks = chunk_text(text)
        assert len(chunks) >= 1
        assert text in "".join(chunks)

    @pytest.mark.unit
    def test_long_text_multiple_chunks(self):
        text = "Medical guidelines. " * 200
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        assert len(chunks) > 1

    @pytest.mark.unit
    def test_empty_text_returns_empty_list(self):
        assert chunk_text("") == []

    @pytest.mark.unit
    def test_whitespace_only_returns_empty_list(self):
        assert chunk_text("   \n\n  ") == []

    @pytest.mark.unit
    def test_custom_chunk_size_produces_more_chunks(self):
        text = "Word " * 500
        small = chunk_text(text, chunk_size=100, overlap=10)
        large = chunk_text(text, chunk_size=800, overlap=10)
        assert len(small) >= len(large)
