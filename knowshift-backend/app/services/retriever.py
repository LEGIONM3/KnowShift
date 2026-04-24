"""
KnowShift — pgvector Retrieval Service  (Phase 2 — enhanced)
Two retrieval modes:
  1. retrieve_chunks()          — semantic ANN search via match_chunks() RPC
  2. retrieve_by_document_id()  — fetch all chunks belonging to one document
"""

import logging
from typing import Any, Dict, List, Optional

from app.database import supabase
from app.services.embedder import embed_query

logger = logging.getLogger(__name__)


def retrieve_chunks(
    query_embedding: List[float],
    domain: str,
    top_k: int = 10,
    include_stale: bool = False,
) -> List[Dict[str, Any]]:
    """Vector-search the chunks table using the pre-built query embedding.

    Calls the ``match_chunks()`` SQL function (defined in supabase_schema.sql)
    which performs an IVFFlat ANN search with cosine distance.

    Phase 2 signature change: accepts a pre-computed embedding vector instead
    of raw text so the caller controls when/how the embedding is generated.
    This avoids double-embedding in the query router.

    Args:
        query_embedding: 768-dimensional float list from ``embed_query()``.
        domain: One of 'medical', 'finance', 'ai_policy'.
        top_k: Maximum number of chunks to return (default 10).
        include_stale: Whether to include stale-flagged document chunks.

    Returns:
        List of dicts — each with:
            chunk_id, chunk_text, freshness_score, similarity,
            published_at, last_verified, source_name, document_id
        Returns ``[]`` on failure so the query pipeline degrades gracefully.
    """
    logger.info(
        "retrieve_chunks | domain=%s | top_k=%d | include_stale=%s",
        domain, top_k, include_stale,
    )

    try:
        response = supabase.rpc(
            "match_chunks",
            {
                "query_embedding": query_embedding,
                "domain_filter": domain,
                "match_count": top_k,
                "include_stale": include_stale,
            },
        ).execute()

        results: List[Dict[str, Any]] = response.data or []
        logger.info("Retrieved %d chunks | domain=%s", len(results), domain)
        return results

    except Exception as exc:
        logger.error(
            "retrieve_chunks FAILED | domain=%s | error=%s",
            domain, exc,
        )
        return []


def retrieve_by_document_id(
    document_id: str,
    include_deprecated: bool = False,
) -> List[Dict[str, Any]]:
    """Fetch all chunk records for a specific document.

    Used by the re-indexing pipeline and the change-map UI to inspect
    what chunks a document currently has.

    Args:
        document_id: UUID of the parent document.
        include_deprecated: If False (default), filters out deprecated chunks.

    Returns:
        List of dicts — each with:
            chunk_id (aliased from id), chunk_text, freshness_score, is_deprecated
        Returns ``[]`` on failure.
    """
    logger.info(
        "retrieve_by_document_id | document_id=%s | include_deprecated=%s",
        document_id, include_deprecated,
    )

    try:
        query = (
            supabase.table("chunks")
            .select("id, chunk_text, freshness_score, is_deprecated")
            .eq("document_id", document_id)
        )

        if not include_deprecated:
            query = query.eq("is_deprecated", False)

        response = query.execute()
        rows: List[Dict[str, Any]] = response.data or []

        # Normalise primary key name to match the rest of the pipeline
        for row in rows:
            row["chunk_id"] = row.pop("id", None)

        logger.info(
            "Fetched %d chunks for document_id=%s (include_deprecated=%s)",
            len(rows), document_id, include_deprecated,
        )
        return rows

    except Exception as exc:
        logger.error(
            "retrieve_by_document_id FAILED | document_id=%s | error=%s",
            document_id, exc,
        )
        return []
