"""
KnowShift — Freshness Engine  (Phase 2 — enhanced with three new functions)
Core temporal logic for the self-healing RAG system.

Phase 1 functions (unchanged):
  - compute_freshness_score()
  - get_validity_horizon()
  - detect_and_flag_stale()

Phase 2 additions:
  - selective_reindex()        — deprecate semantically overlapping old chunks
  - batch_update_freshness()   — bulk freshness score refresh (for Celery tasks)
  - get_reindex_candidates()   — identify documents that need manual re-ingestion
"""

import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config import settings
from app.database import supabase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain-specific decay constants (λ).
# Freshness decays as: score = exp(−λ × days_elapsed)
# Higher λ → faster decay.
# ---------------------------------------------------------------------------
DOMAIN_DECAY: Dict[str, float] = {
    "medical":   0.015,    # Aggressive: drug guidelines update frequently
    "finance":   0.025,    # Very aggressive: market regs change rapidly
    "ai_policy": 0.005,    # Slow: long-lived policy documents
}

_DEFAULT_DECAY = 0.01

# Similarity threshold for selective re-indexing (>= this → deprecate old chunk)
_REINDEX_SIMILARITY_THRESHOLD = 0.85


# ===========================================================================
# Phase 1 — kept intact
# ===========================================================================

def compute_freshness_score(last_verified: datetime, domain: str) -> float:
    """Calculate the freshness score of a document/chunk.

    Applies exponential decay: score = exp(−λ × days_elapsed).

    Args:
        last_verified: The timestamp of the last freshness verification.
        domain: One of 'medical', 'finance', 'ai_policy'.

    Returns:
        A float in [0.0, 1.0] rounded to 4 decimal places.
        1.0 = completely fresh, approaching 0.0 = very stale.
    """
    if last_verified.tzinfo is None:
        last_verified = last_verified.replace(tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)
    days_elapsed = max((now_utc - last_verified).total_seconds() / 86400, 0.0)

    lam = DOMAIN_DECAY.get(domain, _DEFAULT_DECAY)
    score = math.exp(-lam * days_elapsed)

    return round(min(max(score, 0.0), 1.0), 4)


def get_validity_horizon(domain: str) -> int:
    """Return the validity horizon in days for the given domain.

    Args:
        domain: One of 'medical', 'finance', 'ai_policy'.

    Returns:
        Integer number of days.
    """
    return settings.get_validity_days(domain)


def detect_and_flag_stale() -> Dict[str, int]:
    """Sweep all documents and flag those past their validity horizon.

    For each document:
      - Recalculates freshness_score.
      - Sets stale_flag = True if days_old > validity_horizon.
      - Updates freshness_score on all associated chunks.
      - Writes a 'stale_flagged' entry to change_log for newly stale docs.

    Returns:
        {"newly_flagged": count}
    """
    logger.info("Starting stale detection sweep…")
    now_utc = datetime.now(timezone.utc)
    newly_flagged = 0

    docs_resp = supabase.table("documents").select("*").execute()
    documents = docs_resp.data or []
    logger.info("Sweep: checking %d documents.", len(documents))

    for doc in documents:
        doc_id: str           = doc["id"]
        domain: str           = doc["domain"]
        stale_flag_prev: bool = doc.get("stale_flag", False)

        lv_str: str = doc.get("last_verified")
        if not lv_str:
            logger.warning("Document %s has no last_verified; skipping.", doc_id)
            continue

        last_verified   = datetime.fromisoformat(lv_str.replace("Z", "+00:00"))
        days_old        = (now_utc - last_verified).days
        validity_horizon = doc.get("validity_horizon") or get_validity_horizon(domain)

        new_freshness   = compute_freshness_score(last_verified, domain)
        is_stale        = days_old > validity_horizon
        is_newly_stale  = is_stale and not stale_flag_prev

        supabase.table("documents").update({"stale_flag": is_stale}).eq("id", doc_id).execute()
        supabase.table("chunks").update({"freshness_score": new_freshness}).eq("document_id", doc_id).execute()

        if is_newly_stale:
            newly_flagged += 1
            supabase.table("change_log").insert({
                "document_id": doc_id,
                "change_type": "stale_flagged",
                "reason": (
                    f"Document exceeded validity horizon of {validity_horizon} days "
                    f"({days_old} days since last verification)."
                ),
                "old_value": "false",
                "new_value": "true",
            }).execute()
            logger.info(
                "Document %s NEWLY STALE | domain=%s | days_old=%d | horizon=%d",
                doc_id, domain, days_old, validity_horizon,
            )
        else:
            logger.debug(
                "Document %s | stale=%s | days_old=%d | freshness=%.4f",
                doc_id, is_stale, days_old, new_freshness,
            )

    logger.info("Stale sweep complete | newly_flagged=%d", newly_flagged)
    return {"newly_flagged": newly_flagged}


# ===========================================================================
# Phase 2 — new functions
# ===========================================================================

def selective_reindex(
    new_doc_id: str,
    domain: str,
    new_chunk_embeddings: List[List[float]],
) -> Dict:
    """Deprecate existing chunks that semantically overlap with new content.

    For each new chunk's embedding, queries the ``find_overlapping_chunks()``
    SQL function to find existing (non-deprecated) chunks with cosine
    similarity >= 0.85. Those old chunks are marked deprecated and logged
    in ``change_log`` with change_type='re-indexed'.

    Args:
        new_doc_id: UUID of the newly ingested document (excluded from search).
        domain: Domain to search within.
        new_chunk_embeddings: List of 768-dim embedding vectors for the new chunks.

    Returns:
        {"deprecated_chunks": int, "deprecated_ids": [str, ...]}
    """
    logger.info(
        "selective_reindex START | new_doc_id=%s | domain=%s | new_chunks=%d",
        new_doc_id, domain, len(new_chunk_embeddings),
    )

    deprecated_ids: List[str] = []

    for idx, new_emb in enumerate(new_chunk_embeddings):
        try:
            result = supabase.rpc(
                "find_overlapping_chunks",
                {
                    "query_embedding":      new_emb,
                    "domain_filter":        domain,
                    "similarity_threshold": _REINDEX_SIMILARITY_THRESHOLD,
                    "exclude_doc_id":       new_doc_id,
                },
            ).execute()

            overlapping = result.data or []

            for old_chunk in overlapping:
                # The RPC returns 'chunk_id' based on the SQL function signature
                chunk_id = old_chunk.get("chunk_id") or old_chunk.get("id")
                if not chunk_id or chunk_id in deprecated_ids:
                    continue  # Skip already-processed chunks

                # Mark deprecated
                supabase.table("chunks").update({
                    "is_deprecated": True,
                }).eq("id", chunk_id).execute()

                # Audit log
                similarity = old_chunk.get("similarity", 0.0)
                supabase.table("change_log").insert({
                    "chunk_id":    chunk_id,
                    "document_id": new_doc_id,
                    "change_type": "re-indexed",
                    "reason": (
                        f"Superseded by newer document {new_doc_id} "
                        f"(cosine similarity: {similarity:.3f} >= {_REINDEX_SIMILARITY_THRESHOLD})"
                    ),
                    "old_value": "active",
                    "new_value": "deprecated",
                }).execute()

                deprecated_ids.append(chunk_id)
                logger.debug(
                    "Deprecated chunk %s | similarity=%.3f | new_doc=%s",
                    chunk_id, similarity, new_doc_id,
                )

        except Exception as exc:
            # Don't abort the entire re-index if one chunk query fails
            logger.error(
                "selective_reindex error on chunk %d | new_doc=%s | error=%s",
                idx, new_doc_id, exc,
            )
            continue

    logger.info(
        "selective_reindex DONE | deprecated=%d | new_doc_id=%s",
        len(deprecated_ids), new_doc_id,
    )
    return {
        "deprecated_chunks": len(deprecated_ids),
        "deprecated_ids": deprecated_ids,
    }


def batch_update_freshness(domain: Optional[str] = None) -> Dict[str, int]:
    """Recompute freshness scores for all chunks, optionally filtered by domain.

    This is the heavy-lifting counterpart to ``detect_and_flag_stale()``.
    Where the staleness sweep flips the ``stale_flag``, this function
    continuously updates the numeric ``freshness_score`` on every chunk
    — useful as a periodic Celery Beat task (every 6 hours).

    Args:
        domain: If provided, restrict updates to that domain. If None, all domains.

    Returns:
        {"documents_updated": int}
    """
    logger.info("batch_update_freshness START | domain=%s", domain or "all")

    query = supabase.table("documents").select("id, domain, last_verified")
    if domain:
        query = query.eq("domain", domain)

    docs_resp = query.execute()
    docs = docs_resp.data or []
    updated_count = 0

    for doc in docs:
        doc_id      = doc["id"]
        doc_domain  = doc["domain"]
        lv_str      = doc.get("last_verified")

        if not lv_str:
            continue

        try:
            last_verified = datetime.fromisoformat(lv_str.replace("Z", "+00:00"))
            new_score = compute_freshness_score(last_verified, doc_domain)

            supabase.table("chunks").update({
                "freshness_score": new_score,
            }).eq("document_id", doc_id).execute()

            updated_count += 1
        except Exception as exc:
            logger.error(
                "batch_update_freshness failed for doc %s: %s", doc_id, exc
            )

    logger.info("batch_update_freshness DONE | documents_updated=%d", updated_count)
    return {"documents_updated": updated_count}


def get_reindex_candidates(
    domain: str,
    staleness_threshold: float = 0.4,
) -> List[Dict]:
    """Find stale documents whose average chunk freshness falls below a threshold.

    Intended as a decision-support tool: surfaces the documents most in need
    of a fresh source fetch and re-ingestion.

    Args:
        domain: Domain to inspect.
        staleness_threshold: Average freshness_score below which a doc qualifies.

    Returns:
        List of candidate dicts sorted by avg_freshness ascending (worst first):
            document_id, source_name, last_verified, avg_freshness,
            active_chunks, recommended_action
    """
    logger.info(
        "get_reindex_candidates | domain=%s | threshold=%.2f",
        domain, staleness_threshold,
    )

    docs_resp = (
        supabase.table("documents")
        .select("id, source_name, last_verified")
        .eq("domain", domain)
        .eq("stale_flag", True)
        .execute()
    )
    docs = docs_resp.data or []
    candidates: List[Dict] = []

    for doc in docs:
        doc_id = doc["id"]

        chunks_resp = (
            supabase.table("chunks")
            .select("freshness_score")
            .eq("document_id", doc_id)
            .eq("is_deprecated", False)
            .execute()
        )
        chunks = chunks_resp.data or []

        if not chunks:
            continue

        avg_freshness = sum(c["freshness_score"] for c in chunks) / len(chunks)

        if avg_freshness < staleness_threshold:
            candidates.append({
                "document_id":         doc_id,
                "source_name":         doc.get("source_name", "Unknown"),
                "last_verified":       doc.get("last_verified", ""),
                "avg_freshness":       round(avg_freshness, 3),
                "active_chunks":       len(chunks),
                "recommended_action":  "Re-index with updated source document",
            })

    # Sort worst freshness first so consumers know where to prioritise
    candidates_sorted = sorted(candidates, key=lambda x: x["avg_freshness"])
    logger.info(
        "get_reindex_candidates | found %d candidates | domain=%s",
        len(candidates_sorted), domain,
    )
    return candidates_sorted
