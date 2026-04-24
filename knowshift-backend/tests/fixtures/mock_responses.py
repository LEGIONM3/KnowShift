"""
Pre-built mock API responses for testing.
Prevents repeated real API calls during test runs.
"""

from datetime import datetime, timezone, timedelta

_now = datetime.now(timezone.utc)
_old = _now - timedelta(days=400)

# ── Query responses ───────────────────────────────────────────────────────────
MOCK_QUERY_RESPONSE_FRESH = {
    "answer": (
        "Based on the 2024 ADA Standards of Care, GLP-1 receptor agonists "
        "are now recommended as first-line therapy for Type 2 Diabetes patients "
        "with established cardiovascular disease. [Source: ADA Standards 2024, "
        "verified Jan 2024]"
    ),
    "freshness_confidence": 0.92,
    "staleness_warning": False,
    "sources": [
        {
            "source_name":    "ADA Standards of Care 2024",
            "last_verified":  _now.isoformat(),
            "freshness_score": 0.92,
            "chunk_preview":  "GLP-1 receptor agonists recommended...",
        }
    ],
    "ranking_conflicts":  [],
    "processing_time_ms": 1250,
}

MOCK_QUERY_RESPONSE_STALE = {
    "answer": (
        "Based on the 2021 ADA Standards, Metformin remains the preferred "
        "initial agent for Type 2 Diabetes. [Source: ADA Standards 2021]"
    ),
    "freshness_confidence": 0.08,
    "staleness_warning": True,
    "sources": [
        {
            "source_name":    "ADA Standards of Care 2021",
            "last_verified":  _old.isoformat(),
            "freshness_score": 0.08,
            "chunk_preview":  "Metformin remains preferred...",
        }
    ],
    "ranking_conflicts": [
        {
            "chunk_id":        "chunk-stale-001",
            "semantic_similarity": 0.91,
            "freshness_score": 0.08,
            "reason":          "High relevance but outdated (400 days)",
            "suggested_action": "Flag for re-indexing",
        }
    ],
    "processing_time_ms": 980,
}

# ── Compare response ──────────────────────────────────────────────────────────
MOCK_COMPARE_RESPONSE = {
    "stale_answer":       MOCK_QUERY_RESPONSE_STALE,
    "fresh_answer":       MOCK_QUERY_RESPONSE_FRESH,
    "difference_detected": True,
}

# ── Dashboard response ────────────────────────────────────────────────────────
MOCK_DASHBOARD_MEDICAL = {
    "total":      150,
    "fresh":       85,
    "aging":       30,
    "stale":       25,
    "deprecated":  10,
}

# ── Upload response ───────────────────────────────────────────────────────────
MOCK_UPLOAD_RESPONSE = {
    "document_id":           "doc-new-001",
    "chunks_ingested":        12,
    "deprecated_old_chunks":   4,
    "self_healing_triggered": True,
}

# ── Change log ────────────────────────────────────────────────────────────────
MOCK_CHANGE_LOG = {
    "domain":        "medical",
    "total_changes":  2,
    "changes": [
        {
            "id":          "log-001",
            "chunk_id":    "chunk-stale-001",
            "document_id": "doc-stale-001",
            "change_type": "deprecated",
            "reason":      "Superseded by doc-new-001 (similarity: 0.91)",
            "changed_at":  _now.isoformat(),
        },
        {
            "id":          "log-002",
            "chunk_id":    None,
            "document_id": "doc-stale-001",
            "change_type": "stale_flagged",
            "reason":      "Exceeded validity horizon of 180 days",
            "changed_at":  (_now - timedelta(hours=2)).isoformat(),
        },
    ],
}

# ── Stale scan ────────────────────────────────────────────────────────────────
MOCK_STALE_SCAN = {"newly_flagged": 2}

# ── Health ────────────────────────────────────────────────────────────────────
MOCK_HEALTH_OK = {
    "status":      "ok",
    "components":  {"supabase": "ok", "gemini": "ok"},
    "version":     "1.0.0",
    "environment": "testing",
    "timestamp":   _now.isoformat(),
}
