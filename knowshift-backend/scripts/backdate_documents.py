"""
KnowShift — Document Backdating Script
Simulates document aging by setting last_verified timestamps to the past,
then recalculates all chunk freshness scores.

Run AFTER seed_demo_data.py to create the stale-vs-fresh contrast for the demo.

Usage:
    python scripts/backdate_documents.py
"""

import math
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

# ---------------------------------------------------------------------------
# Which documents to backdate (matched by source_name keyword)
# ---------------------------------------------------------------------------
BACKDATE_CONFIG = {
    "medical": {
        "keywords":  ["2021", "ADA Standards of Care 2021"],
        "days_back": 400,
        "reason":    "Demo: simulate 400-day-old medical guidelines",
    },
    "finance": {
        "keywords":  ["2021-22", "FY 2021"],
        "days_back": 500,
        "reason":    "Demo: simulate 500-day-old tax regulations",
    },
    "ai_policy": {
        "keywords":  ["Draft 2022", "Proposal"],
        "days_back": 600,
        "reason":    "Demo: simulate 600-day-old AI policy drafts",
    },
}

# Domain-specific exponential decay constants (must match freshness_engine.py)
DOMAIN_DECAY = {
    "medical":   0.015,
    "finance":   0.025,
    "ai_policy": 0.005,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _should_backdate(source_name: str, keywords: list[str]) -> bool:
    name_lower = source_name.lower()
    return any(kw.lower() in name_lower for kw in keywords)


def _freshness_score(days_elapsed: int, domain: str) -> float:
    lam = DOMAIN_DECAY.get(domain, 0.01)
    return round(math.exp(-lam * days_elapsed), 4)


# ---------------------------------------------------------------------------
# Core steps
# ---------------------------------------------------------------------------

def backdate_documents() -> int:
    total = 0

    for domain, cfg in BACKDATE_CONFIG.items():
        print(f"\n📅 Domain: {domain}")
        docs = supabase.table("documents").select("*").eq("domain", domain).execute().data or []
        print(f"   {len(docs)} document(s) found")

        for doc in docs:
            if not _should_backdate(doc["source_name"], cfg["keywords"]):
                print(f"   ⏭  Kept fresh: {doc['source_name']}")
                continue

            past_dt = datetime.now(timezone.utc) - timedelta(days=cfg["days_back"])

            supabase.table("documents").update({
                "last_verified": past_dt.isoformat(),
                "stale_flag":    True,
            }).eq("id", doc["id"]).execute()

            supabase.table("change_log").insert({
                "document_id": doc["id"],
                "change_type": "stale_flagged",
                "reason":      cfg["reason"],
                "old_value":   "current",
                "new_value":   f"{cfg['days_back']} days old",
            }).execute()

            print(f"   ✅ Backdated: {doc['source_name']}")
            print(f"      new date:  {past_dt.strftime('%Y-%m-%d')}  ({cfg['days_back']} days ago)")
            total += 1

    return total


def update_chunk_freshness_scores():
    """Recompute freshness_score for every chunk based on its document's last_verified."""
    print("\n🔄 Recalculating chunk freshness scores…")
    docs = supabase.table("documents").select("*").execute().data or []
    updated = 0

    for doc in docs:
        try:
            last_verified = datetime.fromisoformat(
                doc["last_verified"].replace("Z", "+00:00")
            )
        except (KeyError, ValueError):
            continue

        days = (datetime.now(timezone.utc) - last_verified).days
        new_score = _freshness_score(days, doc["domain"])

        supabase.table("chunks").update({
            "freshness_score": new_score
        }).eq("document_id", doc["id"]).execute()

        print(f"   {doc['source_name'][:45]:45s}  score={new_score}  (days={days})")
        updated += 1

    return updated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("KnowShift — Document Backdating Tool")
    print("=" * 60)

    n_backdated = backdate_documents()
    print(f"\n✅ {n_backdated} document(s) backdated")

    n_updated = update_chunk_freshness_scores()
    print(f"✅ {n_updated} documents' chunk scores recalculated")

    print("\nNext step: python scripts/verify_setup.py")
