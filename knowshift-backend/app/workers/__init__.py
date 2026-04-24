"""
KnowShift — Workers Package  (Phase 2)
Exports the Celery app and all tasks for easy import from other modules.
"""

from .tasks import (
    celery_app,
    scan_stale_documents,
    update_freshness_scores,
    generate_freshness_report,
)

__all__ = [
    "celery_app",
    "scan_stale_documents",
    "update_freshness_scores",
    "generate_freshness_report",
]
