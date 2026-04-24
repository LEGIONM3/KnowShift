"""
KnowShift — Celery Background Workers  (Phase 2)
Three periodic tasks managed by Celery Beat:

  scan_stale_documents      — daily:    flag stale documents
  update_freshness_scores   — 6-hourly: recompute chunk freshness scores
  generate_freshness_report — weekly:   system-wide health report
"""

import logging
from typing import Optional

from celery import Celery

from app.config import settings
from app.services.freshness_engine import (
    detect_and_flag_stale,
    batch_update_freshness,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Celery application
# ---------------------------------------------------------------------------
celery_app = Celery(
    "knowshift",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Prevent tasks from running indefinitely
    task_soft_time_limit=300,   # 5 minutes soft limit
    task_time_limit=600,        # 10 minutes hard limit
    # Retry on connection failure during startup
    broker_connection_retry_on_startup=True,
)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@celery_app.task(
    name="tasks.scan_stale_documents",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def scan_stale_documents(self) -> dict:
    """Daily task: flag documents that have exceeded their validity horizon.

    Runs detect_and_flag_stale() which:
    - Calculates days_elapsed for each document
    - Sets stale_flag = True when days_elapsed > validity_horizon
    - Updates chunk freshness_score
    - Logs newly stale documents to change_log

    Returns:
        {"newly_flagged": int}
    """
    logger.info("Celery task START: scan_stale_documents")
    try:
        result = detect_and_flag_stale()
        logger.info(
            "Celery task DONE: scan_stale_documents | newly_flagged=%d",
            result["newly_flagged"],
        )
        return result
    except Exception as exc:
        logger.error("scan_stale_documents failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="tasks.update_freshness_scores",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def update_freshness_scores(self, domain: Optional[str] = None) -> dict:
    """6-hourly task: recompute freshness scores for all (or one domain's) chunks.

    Args:
        domain: Restrict to a specific domain, or None for all domains.

    Returns:
        {"documents_updated": int}
    """
    logger.info("Celery task START: update_freshness_scores | domain=%s", domain or "all")
    try:
        result = batch_update_freshness(domain)
        logger.info(
            "Celery task DONE: update_freshness_scores | documents_updated=%d",
            result["documents_updated"],
        )
        return result
    except Exception as exc:
        logger.error("update_freshness_scores failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="tasks.generate_freshness_report",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def generate_freshness_report(self) -> dict:
    """Weekly task: produce a system-wide freshness health report.

    Queries each domain independently and computes:
    - total_chunks, fresh, aging, stale, deprecated counts
    - health_score = (fresh / total) * 100

    Returns:
        A dict keyed by domain with health metrics.
    """
    logger.info("Celery task START: generate_freshness_report")
    from app.database import supabase

    domains = ["medical", "finance", "ai_policy"]
    report: dict = {}

    try:
        for domain in domains:
            # Get document IDs for this domain
            docs_resp = (
                supabase.table("documents")
                .select("id")
                .eq("domain", domain)
                .execute()
            )
            doc_ids = [d["id"] for d in (docs_resp.data or [])]

            if not doc_ids:
                report[domain] = {
                    "total_chunks": 0, "fresh": 0, "aging": 0,
                    "stale": 0, "deprecated": 0, "health_score": 0.0,
                }
                continue

            chunks_resp = (
                supabase.table("chunks")
                .select("freshness_score, is_deprecated")
                .in_("document_id", doc_ids)
                .execute()
            )
            chunks = chunks_resp.data or []
            total = len(chunks)

            fresh      = sum(1 for c in chunks if c["freshness_score"] >= 0.7 and not c["is_deprecated"])
            aging      = sum(1 for c in chunks if 0.4 <= c["freshness_score"] < 0.7 and not c["is_deprecated"])
            stale      = sum(1 for c in chunks if c["freshness_score"] < 0.4  and not c["is_deprecated"])
            deprecated = sum(1 for c in chunks if c["is_deprecated"])

            report[domain] = {
                "total_chunks": total,
                "fresh":        fresh,
                "aging":        aging,
                "stale":        stale,
                "deprecated":   deprecated,
                "health_score": round((fresh / total * 100) if total > 0 else 0.0, 2),
            }

        logger.info("Celery task DONE: generate_freshness_report | %s", report)
        return report

    except Exception as exc:
        logger.error("generate_freshness_report failed: %s", exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Celery Beat periodic schedule
# ---------------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    "scan-stale-daily": {
        "task":     "tasks.scan_stale_documents",
        "schedule": 86400.0,    # Every 24 hours
    },
    "update-freshness-6h": {
        "task":     "tasks.update_freshness_scores",
        "schedule": 21600.0,    # Every 6 hours
    },
    "weekly-report": {
        "task":     "tasks.generate_freshness_report",
        "schedule": 604800.0,   # Every 7 days
    },
}
