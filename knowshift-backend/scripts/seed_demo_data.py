"""
KnowShift — Demo Data Seeder
Uploads all 6 demo PDFs to the running FastAPI backend.

Usage:
    API_URL=http://localhost:8000 python scripts/seed_demo_data.py
    # or just:
    python scripts/seed_demo_data.py
"""

import os
import time
from pathlib import Path

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")

DEMO_DOCUMENTS = [
    # ── Medical ───────────────────────────────────────────────────────────────
    {
        "filename":     "demo_data/medical_2021_guidelines.pdf",
        "domain":       "medical",
        "source_name":  "ADA Standards of Care 2021",
        "source_url":   "https://diabetesjournals.org/care",
        "published_at": "2021-01-01T00:00:00",
    },
    {
        "filename":     "demo_data/medical_2024_guidelines.pdf",
        "domain":       "medical",
        "source_name":  "ADA Standards of Care 2024",
        "source_url":   "https://diabetesjournals.org/care",
        "published_at": "2024-01-01T00:00:00",
    },
    # ── Finance ───────────────────────────────────────────────────────────────
    {
        "filename":     "demo_data/finance_tax_2021.pdf",
        "domain":       "finance",
        "source_name":  "Income Tax Rates FY 2021-22",
        "source_url":   "https://incometaxindia.gov.in",
        "published_at": "2021-02-01T00:00:00",
    },
    {
        "filename":     "demo_data/finance_tax_2024.pdf",
        "domain":       "finance",
        "source_name":  "Income Tax Rates FY 2024-25",
        "source_url":   "https://incometaxindia.gov.in",
        "published_at": "2024-07-01T00:00:00",
    },
    # ── AI Policy ─────────────────────────────────────────────────────────────
    {
        "filename":     "demo_data/ai_policy_draft_2022.pdf",
        "domain":       "ai_policy",
        "source_name":  "EU AI Act Draft 2022",
        "source_url":   "https://eur-lex.europa.eu",
        "published_at": "2022-04-01T00:00:00",
    },
    {
        "filename":     "demo_data/ai_policy_enacted_2024.pdf",
        "domain":       "ai_policy",
        "source_name":  "EU AI Act Final 2024",
        "source_url":   "https://eur-lex.europa.eu",
        "published_at": "2024-07-01T00:00:00",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_api_health() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=10)
        if r.status_code == 200:
            print(f"  ✅ API is online at {API_URL}")
            return True
        print(f"  ❌ API returned HTTP {r.status_code}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Cannot connect to {API_URL}")
        print("     Start the API first:  uvicorn app.main:app --reload")
        return False


def upload_document(cfg: dict) -> dict | None:
    path = Path(cfg["filename"])
    if not path.exists():
        print(f"  ❌ File not found: {path}")
        print("     Generate first:  python scripts/generate_test_pdfs.py")
        return None

    print(f"\n📤 Uploading:  {cfg['source_name']}")
    print(f"   domain:     {cfg['domain']}")
    print(f"   file:       {path}")

    with open(path, "rb") as fh:
        files = {"file": (path.name, fh, "application/pdf")}
        data  = {
            "domain":       cfg["domain"],
            "source_name":  cfg["source_name"],
            "source_url":   cfg.get("source_url", ""),
            "published_at": cfg.get("published_at", ""),
        }
        try:
            r = requests.post(
                f"{API_URL}/ingest/upload",
                files=files,
                data=data,
                timeout=120,
            )
        except requests.exceptions.Timeout:
            print("  ❌ Upload timed out after 2 minutes")
            return None
        except Exception as exc:
            print(f"  ❌ Request error: {exc}")
            return None

    if r.status_code in (200, 201):
        result = r.json()
        print(f"  ✅ {result.get('chunks_ingested', '?')} chunks indexed")
        deprecated = result.get("deprecated_old_chunks", 0)
        if deprecated:
            print(f"  🔄 Self-healing: {deprecated} old chunks deprecated")
        return result

    print(f"  ❌ HTTP {r.status_code}: {r.text[:200]}")
    return None


def run_stale_scan():
    print("\n🔍 Running freshness scan…")
    try:
        r = requests.post(f"{API_URL}/freshness/scan", timeout=30)
        if r.status_code == 200:
            newly = r.json().get("newly_flagged", 0)
            print(f"  ✅ Scan done — {newly} documents flagged stale")
        else:
            print(f"  ❌ Scan returned HTTP {r.status_code}")
    except Exception as exc:
        print(f"  ❌ Scan error: {exc}")


def verify_seeding():
    print("\n📊 Verifying seeded data…")
    for domain in ("medical", "finance", "ai_policy"):
        try:
            r = requests.get(f"{API_URL}/freshness/dashboard/{domain}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                print(
                    f"  {domain.upper():12s} | "
                    f"total={d.get('total',0):3d}  "
                    f"fresh={d.get('fresh',0):3d}  "
                    f"aging={d.get('aging',0):3d}  "
                    f"stale={d.get('stale',0):3d}  "
                    f"deprecated={d.get('deprecated',0):3d}"
                )
        except Exception as exc:
            print(f"  ❌ {domain}: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed_all() -> bool:
    print("=" * 60)
    print("KnowShift — Demo Data Seeder")
    print("=" * 60)

    if not check_api_health():
        return False

    results = []
    for i, doc in enumerate(DEMO_DOCUMENTS):
        result = upload_document(doc)
        if result:
            results.append(result)
        # Respect Gemini free-tier: ~15 embeds/min → wait 3 s between uploads
        if i < len(DEMO_DOCUMENTS) - 1:
            print("  ⏳ Waiting 3 s (Gemini rate limit)…")
            time.sleep(3)

    print(f"\n✅ Uploaded {len(results)} / {len(DEMO_DOCUMENTS)} documents")

    run_stale_scan()
    verify_seeding()

    print("\n" + "=" * 60)
    print("✅ Seeding complete!  Next: python scripts/backdate_documents.py")
    print("=" * 60)
    return True


if __name__ == "__main__":
    seed_all()
