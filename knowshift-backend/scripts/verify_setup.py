"""
KnowShift — Complete Setup Verification Suite
Run before every demo to confirm the full pipeline is functional.

Usage:
    python scripts/verify_setup.py
    API_URL=https://your-api.onrender.com python scripts/verify_setup.py

Exit code 0 = all tests pass (ready for demo).
Exit code 1 = failures detected (fix before demo).
"""

import os
import sys
from datetime import datetime

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Console colours
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"{GREEN}  ✅ {msg}{RESET}")
def fail(msg): print(f"{RED}  ❌ {msg}{RESET}")
def warn(msg): print(f"{YELLOW}  ⚠️  {msg}{RESET}")
def info(msg): print(f"{BLUE}  ℹ️  {msg}{RESET}")
def section(t): print(f"\n{BOLD}{'='*52}\n{t}\n{'='*52}{RESET}")

PASSED = 0
FAILED = 0


def run_test(name: str, fn) -> bool:
    global PASSED, FAILED
    try:
        ok_result = fn()
        if ok_result:
            ok(name)
            PASSED += 1
            return True
        fail(name)
        FAILED += 1
        return False
    except Exception as exc:
        fail(f"{name}  ({exc})")
        FAILED += 1
        return False


# ---------------------------------------------------------------------------
# Individual test functions
# ---------------------------------------------------------------------------

def _get(path, **params):
    return requests.get(f"{API_URL}{path}", params=params, timeout=15)

def _post(path, **json_body):
    return requests.post(f"{API_URL}{path}", json=json_body, timeout=45)


def test_api_health():
    r = _get("/health")
    return r.status_code == 200 and r.json().get("status") in ("ok", "degraded")

def test_supabase_ok():
    r = _get("/health")
    return r.json().get("components", {}).get("supabase") == "ok"

def test_gemini_ok():
    r = _get("/health")
    return r.json().get("components", {}).get("gemini") == "ok"

def test_stats_endpoint():
    r = _get("/stats")
    return r.status_code == 200 and "total_documents" in r.json()

def test_medical_dashboard():
    r = _get("/freshness/dashboard/medical")
    return r.status_code == 200 and "total" in r.json()

def test_finance_dashboard():
    return _get("/freshness/dashboard/finance").status_code == 200

def test_ai_policy_dashboard():
    return _get("/freshness/dashboard/ai_policy").status_code == 200

def test_query_medical():
    r = _post(
        "/query/ask",
        question="What is the first-line treatment for Type 2 Diabetes?",
        domain="medical",
        include_stale=False,
    )
    if r.status_code != 200:
        return False
    d = r.json()
    return "answer" in d and "freshness_confidence" in d

def test_query_finance():
    r = _post(
        "/query/ask",
        question="What is the tax rate for income between 10 and 12 lakhs?",
        domain="finance",
        include_stale=False,
    )
    return r.status_code == 200

def test_query_ai_policy():
    r = _post(
        "/query/ask",
        question="What obligations do high-risk AI system providers have?",
        domain="ai_policy",
        include_stale=False,
    )
    return r.status_code == 200

def test_compare_endpoint():
    r = _get(
        "/query/compare",
        question="What is the first-line treatment for Type 2 Diabetes?",
        domain="medical",
    )
    if r.status_code != 200:
        return False
    d = r.json()
    return "stale_answer" in d and "fresh_answer" in d

def test_stale_detection():
    r = requests.post(f"{API_URL}/freshness/scan", timeout=30)
    return r.status_code == 200 and "newly_flagged" in r.json()

def test_change_log():
    r = _get("/freshness/change-log/medical")
    return r.status_code == 200 and "changes" in r.json()

def test_stale_vs_fresh_diverge():
    """The killer test: stale and fresh must produce different answers or scores."""
    fresh_r = _post(
        "/query/ask",
        question="What is the first-line treatment for Type 2 Diabetes?",
        domain="medical",
        include_stale=False,
    )
    stale_r = _post(
        "/query/ask",
        question="What is the first-line treatment for Type 2 Diabetes?",
        domain="medical",
        include_stale=True,
    )
    if fresh_r.status_code != 200 or stale_r.status_code != 200:
        return False

    fresh_score = fresh_r.json().get("freshness_confidence", 0)
    stale_score = stale_r.json().get("freshness_confidence", 0)
    fresh_ans   = fresh_r.json().get("answer", "")
    stale_ans   = stale_r.json().get("answer", "")

    return fresh_score != stale_score or fresh_ans != stale_ans


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------

def run_all_tests():
    print(f"\n{BOLD}🔬 KnowShift Phase 4 Verification Suite{RESET}")
    print(f"   API: {API_URL}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    section("1. INFRASTRUCTURE")
    run_test("API health check",    test_api_health)
    run_test("Supabase connection", test_supabase_ok)
    run_test("Gemini API config",   test_gemini_ok)
    run_test("Stats endpoint",      test_stats_endpoint)

    section("2. DEMO DATA")
    run_test("Medical domain has data",   test_medical_dashboard)
    run_test("Finance domain has data",   test_finance_dashboard)
    run_test("AI Policy domain has data", test_ai_policy_dashboard)

    section("3. QUERY PIPELINE")
    run_test("Medical query",    test_query_medical)
    run_test("Finance query",    test_query_finance)
    run_test("AI Policy query",  test_query_ai_policy)

    section("4. KNOWSHIFT CORE FEATURES")
    run_test("Compare endpoint works",                  test_compare_endpoint)
    run_test("Stale detection / freshness scan",        test_stale_detection)
    run_test("Change log returns data",                 test_change_log)
    run_test("Stale vs fresh gives different results",  test_stale_vs_fresh_diverge)

    section("RESULTS SUMMARY")
    total = PASSED + FAILED
    pct   = round((PASSED / total) * 100) if total else 0

    print(f"\n  Passed: {GREEN}{PASSED}/{total}{RESET}   Failed: {RED}{FAILED}/{total}{RESET}   Score: {BOLD}{pct}%{RESET}")

    if FAILED == 0:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED — Demo ready!{RESET}\n")
    elif FAILED <= 2:
        print(f"\n{YELLOW}{BOLD}⚠️  Minor issues — review failures above{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}❌ Multiple failures — fix before demo!{RESET}\n")
        sys.exit(1)

    return FAILED == 0


if __name__ == "__main__":
    run_all_tests()
