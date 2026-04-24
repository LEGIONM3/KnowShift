"""
KnowShift — PDF Chunking Service
Handles two concerns:
  1. Extracting raw text from PDF byte streams (via pdfplumber).
  2. Splitting long text into semantically coherent chunks (via LangChain).
"""

import io
import logging
from typing import List

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default chunking parameters (override at call site if needed)
# ---------------------------------------------------------------------------
_DEFAULT_CHUNK_SIZE = 800       # characters per chunk
_DEFAULT_CHUNK_OVERLAP = 150    # overlap between consecutive chunks
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF provided as raw bytes.

    Args:
        file_bytes: Raw bytes of a PDF file (e.g., from UploadFile.read()).

    Returns:
        A single string with all page texts joined by newlines.
        Returns an empty string if no text could be extracted.

    Raises:
        ValueError: If the bytes do not appear to be a valid PDF.
    """
    if not file_bytes:
        raise ValueError("PDF file_bytes is empty.")

    text_pages: List[str] = []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            logger.debug("PDF opened | pages=%d", len(pdf.pages))
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_pages.append(page_text.strip())
                    else:
                        logger.debug("Page %d is empty or image-only, skipping.", page_num)
                except Exception as page_err:
                    # Don't abort on a single bad page — just skip it
                    logger.warning("Failed to extract page %d: %s", page_num, page_err)
    except Exception as pdf_err:
        raise ValueError(f"Failed to open/parse PDF: {pdf_err}") from pdf_err

    full_text = "\n".join(text_pages)
    logger.info("PDF text extracted | pages_with_text=%d | total_chars=%d", len(text_pages), len(full_text))
    return full_text


def chunk_text(
    text: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Split a long text string into overlapping chunks for embedding.

    Uses LangChain's RecursiveCharacterTextSplitter which tries to split on
    paragraph breaks, then sentence boundaries, then words, before resorting
    to character-level splits — preserving as much semantic coherence as possible.

    Args:
        text: The full document text to split.
        chunk_size: Maximum characters per chunk (default 800).
        overlap: Number of characters of overlap between consecutive chunks (default 150).

    Returns:
        A list of chunk strings. Returns an empty list if `text` is blank.
    """
    if not text or not text.strip():
        logger.warning("chunk_text called with an empty string — returning []")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=_SEPARATORS,
        length_function=len,
    )

    chunks: List[str] = splitter.split_text(text)
    logger.info("Text chunked | total_chunks=%d | chunk_size=%d | overlap=%d", len(chunks), chunk_size, overlap)
    return chunks
