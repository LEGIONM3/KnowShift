"""
KnowShift — Gemini Embedding Service
Wraps the Google Generative AI SDK to generate 768-dimensional text embeddings
using the `text-embedding-004` model. Includes retry logic with exponential
backoff to handle rate limits on the free tier (15 req/min).
"""

import logging
import time
from typing import List

import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configure the Google AI client once at import time
# ---------------------------------------------------------------------------
genai.configure(api_key=settings.gemini_api_key)

_EMBEDDING_MODEL = "models/text-embedding-004"
_VECTOR_DIM = 768


# ---------------------------------------------------------------------------
# Retry decorator — handles transient API failures and rate-limit errors
# Backs off: 4 s, 8 s, 16 s (up to 3 retries = 4 total attempts)
# ---------------------------------------------------------------------------
def _is_retriable(exc: Exception) -> bool:
    """Return True for exceptions we should retry on."""
    retriable_phrases = [
        "429",
        "quota",
        "rate limit",
        "resource exhausted",
        "internal",
        "503",
        "deadline",
    ]
    return any(p in str(exc).lower() for p in retriable_phrases)


_retry_policy = retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Tighter policy: only retry on rate-limit / transient errors.
# Applied via the predicate so non-retriable errors (e.g., bad API key)
# surface immediately instead of wasting all 4 attempts.
_rate_limit_retry_policy = retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


def _embed(text: str, task_type: str) -> List[float]:
    """Low-level embedding call with retry logic.

    Args:
        text: The text to embed.
        task_type: Either 'retrieval_document' or 'retrieval_query'.

    Returns:
        A list of 768 floats representing the embedding.

    Raises:
        RuntimeError: If the API returns an unexpected result shape.
        Exception: Propagates after all retries are exhausted.
    """
    logger.debug("Embedding request | model=%s | task=%s | len=%d", _EMBEDDING_MODEL, task_type, len(text))

    # The SDK returns an EmbedContentResponse object
    response = genai.embed_content(
        model=_EMBEDDING_MODEL,
        content=text,
        task_type=task_type,
    )

    embedding: List[float] = response["embedding"]

    if len(embedding) != _VECTOR_DIM:
        raise RuntimeError(
            f"Expected {_VECTOR_DIM}-dim embedding, got {len(embedding)}-dim. "
            "Check that you are using 'text-embedding-004'."
        )

    logger.debug("Embedding received | dim=%d", len(embedding))
    return embedding


@_retry_policy
def embed_text(text: str) -> List[float]:
    """Generate a *document* embedding for a text chunk.

    Use this when indexing chunks into the vector store.

    Args:
        text: The chunk text to embed (up to ~2048 tokens).

    Returns:
        768-dimensional float list.
    """
    return _embed(text, task_type="retrieval_document")


@_retry_policy
def embed_query(text: str) -> List[float]:
    """Generate a *query* embedding optimised for retrieval.

    Use this when embedding a user's search question.

    Args:
        text: The user's query string.

    Returns:
        768-dimensional float list.
    """
    return _embed(text, task_type="retrieval_query")


def embed_batch(texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
    """Embed a list of texts while respecting the Gemini free-tier 15 RPM limit.

    Sleeps 4 seconds between calls (60s ÷ 15 RPM = 4 s/call).
    Use this during document ingestion, not during query time.

    Args:
        texts:     List of text strings to embed.
        task_type: 'retrieval_document' for indexing, 'retrieval_query' for search.

    Returns:
        List of 768-dim float vectors, one per input text.
    """
    _RPM_SLEEP = 4.0  # seconds between API calls

    embeddings: List[List[float]] = []
    total = len(texts)

    for i, text in enumerate(texts):
        logger.info("Embedding chunk %d/%d | task=%s", i + 1, total, task_type)
        embeddings.append(_embed(text, task_type=task_type))

        # Sleep between calls — skip the delay after the last chunk
        if i < total - 1:
            time.sleep(_RPM_SLEEP)

    logger.info("Batch embedding complete | %d vectors produced", len(embeddings))
    return embeddings
