"""
KnowShift — Freshness Router  (Phase 2 — enhanced with change-log endpoints)
Endpoints:

Phase 1 (unchanged):
    POST /freshness/scan                    — trigger stale detection sweep
    GET  /freshness/dashboard/{domain}      — chunk freshness breakdown

Phase 2 additions:
    GET  /freshness/change-log/{domain}     — paginated change audit trail
    GET  /freshness/reindex-candidates/{domain} — documents needing re-ingestion
    POST /freshness/trigger-reindex/{document_id} — queue manual re-index
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.database import supabase
from app.services import freshness_engine

logger = logging.getLogger(__name__)

router = APIRouter()

_VALID_DOMAINS = {"medical", "finance", "ai_policy"}
_VALID_CHANGE_TYPES = {"deprecated", "updated", "re-indexed", "stale_flagged"}


# ===========================================================================
# Phase 1 endpoints — kept intact
# ===========================================================================

@router.post("/scan", status_code=status.HTTP_200_OK)
async def scan_for_stale() -> Dict[str, Any]:
    """Trigger a full freshness sweep across all documents.

    Iterates every document, recalculates freshness scores, sets stale_flag,
    propagates scores to chunks, and writes change_log entries for newly
    stale documents.

    Returns:
        {"newly_flagged": int}
    """
    try:
        return freshness_engine.detect_and_flag_stale()
    except Exception as exc:
        logger.error("Stale sweep failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("/dashboard/{domain}", status_code=status.HTTP_200_OK)
async def domain_dashboard(
    domain: str = Path(..., description="Knowledge domain: medical | finance | ai_policy"),
) -> Dict[str, Any]:
    """Return a freshness summary for the given domain.

    Categories:
    - **fresh**:      freshness_score >= 0.7 AND not deprecated
    - **aging**:      0.4 <= freshness_score < 0.7 AND not deprecated
    - **stale**:      freshness_score < 0.4 AND not deprecated
    - **deprecated**: is_deprecated = TRUE
    """
    if domain not in _VALID_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain '{domain}'. Must be one of: {sorted(_VALID_DOMAINS)}",
        )

    try:
        docs_resp = supabase.table("documents").select("id").eq("domain", domain).execute()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    doc_ids = [d["id"] for d in (docs_resp.data or [])]
    if not doc_ids:
        return {"domain": domain, "total": 0, "fresh": 0, "aging": 0, "stale": 0, "deprecated": 0}

    try:
        chunks_resp = (
            supabase.table("chunks")
            .select("freshness_score, is_deprecated")
            .in_("document_id", doc_ids)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    chunks = chunks_resp.data or []
    fresh = aging = stale = deprecated = 0

    for chunk in chunks:
        score: float = chunk.get("freshness_score", 1.0)
        is_dep: bool = chunk.get("is_deprecated", False)

        if is_dep:
            deprecated += 1
        elif score >= 0.7:
            fresh += 1
        elif score >= 0.4:
            aging += 1
        else:
            stale += 1

    return {
        "domain":     domain,
        "total":      len(chunks),
        "fresh":      fresh,
        "aging":      aging,
        "stale":      stale,
        "deprecated": deprecated,
    }


# ===========================================================================
# Phase 2 endpoints — new
# ===========================================================================

@router.get("/change-log/{domain}", status_code=status.HTTP_200_OK)
async def get_change_log(
    domain: str = Path(..., description="Knowledge domain"),
    limit:  int = Query(default=50, ge=1, le=200, description="Max entries to return"),
    change_type: Optional[str] = Query(
        default=None,
        description="Filter by type: deprecated | updated | re-indexed | stale_flagged",
    ),
) -> Dict[str, Any]:
    """Return the change audit trail for a domain.

    Uses a join on documents so we can filter by domain even though
    change_log itself does not have a domain column.  The Supabase Python
    SDK supports nested select syntax for this.

    Args:
        domain: Domain filter.
        limit: Maximum rows to return (default 50, max 200).
        change_type: Optional filter on the change_type field.

    Returns:
        {"domain": str, "total_changes": int, "changes": [...]}}
    """
    if domain not in _VALID_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain '{domain}'. Must be one of: {sorted(_VALID_DOMAINS)}",
        )
    if change_type and change_type not in _VALID_CHANGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid change_type '{change_type}'. Must be one of: {sorted(_VALID_CHANGE_TYPES)}",
        )

    try:
        # Fetch change_log rows with related document info for domain filtering
        query = (
            supabase.table("change_log")
            .select("*, documents(source_name, domain)")
            .order("changed_at", desc=True)
            .limit(limit * 3)   # over-fetch to account for domain filtering
        )

        if change_type:
            query = query.eq("change_type", change_type)

        resp = query.execute()
        all_logs = resp.data or []

    except Exception as exc:
        logger.error("change-log query failed | domain=%s | error=%s", domain, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    # Filter to the requested domain via the joined documents record
    filtered = [
        log for log in all_logs
        if (log.get("documents") or {}).get("domain") == domain
    ][:limit]

    return {
        "domain":        domain,
        "total_changes": len(filtered),
        "changes":       filtered,
    }


@router.get("/reindex-candidates/{domain}", status_code=status.HTTP_200_OK)
async def get_reindex_candidates_endpoint(
    domain: str = Path(..., description="Knowledge domain"),
    staleness_threshold: float = Query(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Avg freshness_score below which a doc is a candidate",
    ),
) -> Dict[str, Any]:
    """List documents that are stale and have low average chunk freshness.

    Returns them sorted worst-first so operators know where to act first.
    """
    if domain not in _VALID_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain '{domain}'. Must be one of: {sorted(_VALID_DOMAINS)}",
        )

    try:
        candidates = freshness_engine.get_reindex_candidates(domain, staleness_threshold)
    except Exception as exc:
        logger.error("get_reindex_candidates failed | domain=%s | error=%s", domain, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {
        "domain":            domain,
        "staleness_threshold": staleness_threshold,
        "candidates_count":  len(candidates),
        "candidates":        candidates,
    }


@router.post("/trigger-reindex/{document_id}", status_code=status.HTTP_200_OK)
async def trigger_manual_reindex(
    document_id: str = Path(..., description="UUID of the document to queue for re-indexing"),
) -> Dict[str, Any]:
    """Queue a manual re-index request for a specific document.

    In Phase 2 this writes an 'updated' change_log entry as a signal to
    operators (or a future Celery task) that the document needs a fresh
    source fetch and re-ingestion.

    In Phase 3 this will dispatch a Celery task that actually fetches the
    URL, re-ingests the PDF, and runs selective re-indexing automatically.
    """
    try:
        # Verify the document exists
        doc_resp = supabase.table("documents").select("id, source_name").eq("id", document_id).execute()
        if not doc_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found.",
            )

        source_name = doc_resp.data[0].get("source_name", "Unknown")

        supabase.table("change_log").insert({
            "document_id": document_id,
            "change_type": "updated",
            "reason":      f"Manual re-index triggered via API for '{source_name}'",
        }).execute()

        logger.info("Manual re-index queued | document_id=%s", document_id)
        return {"status": "Re-index queued", "document_id": document_id, "source_name": source_name}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("trigger_manual_reindex failed | document_id=%s | error=%s", document_id, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
