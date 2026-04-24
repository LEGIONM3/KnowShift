"""
Demo validation tests for KnowShift hackathon submission.
Mirrors every step in DEMO_SCRIPT.md — run before every demo.

Pass = System is demo-ready.
Fail = Fix the indicated issue before presenting.

Run:
    TEST_API_URL=http://localhost:8000 pytest tests/demo/ -v -s -m demo
"""

import pytest

pytestmark = [pytest.mark.demo, pytest.mark.slow]

DIABETES_Q  = "What is the first-line treatment for Type 2 Diabetes?"
TAX_Q       = "What is the tax rate for income between Rs 10-12 lakhs?"
AI_POLICY_Q = "What obligations do high-risk AI system providers have?"


class TestDemoReadiness:
    """Master readiness gate — each test maps to a demo script step."""

    # ── Step 1: Domain loads ──────────────────────────────────────────────────
    def test_step1_medical_domain_accessible(self, live_client):
        """Demo Step 1: Medical domain tile loads."""
        d = live_client.get("/freshness/dashboard/medical").json()
        assert d.get("total", 0) > 0, (
            "❌ Medical domain has NO data! Run: python scripts/seed_demo_data.py"
        )
        print(f"\n✅ Medical chunks: {d['total']}")

    # ── Step 2: Stale index answer ────────────────────────────────────────────
    def test_step2_stale_answer_has_content(self, live_client):
        """Demo Step 2: Stale mode returns a meaningful (but outdated) answer."""
        r = live_client.post(
            "/query/ask",
            json={"question": DIABETES_Q, "domain": "medical", "include_stale": True},
        )
        assert r.status_code == 200
        ans = r.json().get("answer", "")
        assert len(ans) > 50, "Stale answer too short for demo"
        print(f"\n⚠️  Stale freshness: {r.json()['freshness_confidence']:.2f}")

    # ── Step 3: Fresh index answer ────────────────────────────────────────────
    def test_step3_fresh_answer_has_content(self, live_client):
        """Demo Step 3: Fresh mode returns up-to-date answer."""
        r = live_client.post(
            "/query/ask",
            json={"question": DIABETES_Q, "domain": "medical", "include_stale": False},
        )
        assert r.status_code == 200
        ans = r.json().get("answer", "")
        assert len(ans) > 50, "Fresh answer too short for demo"
        print(f"\n✅ Fresh freshness: {r.json()['freshness_confidence']:.2f}")

    # ── Step 4: Change Map ────────────────────────────────────────────────────
    def test_step4_change_map_returns_both_panels(self, live_client):
        """Demo Step 4: Change Map shows stale/fresh side-by-side."""
        r = live_client.get(
            "/query/compare",
            params={"question": DIABETES_Q, "domain": "medical"},
        )
        assert r.status_code == 200
        d = r.json()
        stale = d.get("stale_answer", {}).get("answer", "")
        fresh = d.get("fresh_answer", {}).get("answer", "")
        assert len(stale) > 50, "Stale answer too short for Change Map"
        assert len(fresh) > 50, "Fresh answer too short for Change Map"
        print(f"\n🗺️  Difference detected: {d.get('difference_detected')}")

    # ── Step 5: Finance domain ────────────────────────────────────────────────
    def test_step5_finance_query_works(self, live_client):
        """Demo Step 5: Finance domain answers tax question."""
        r = live_client.post(
            "/query/ask",
            json={"question": TAX_Q, "domain": "finance", "include_stale": False},
        )
        assert r.status_code == 200
        assert len(r.json().get("answer", "")) > 50

    # ── Step 6: AI Policy domain ──────────────────────────────────────────────
    def test_step6_ai_policy_query_works(self, live_client):
        r = live_client.post(
            "/query/ask",
            json={"question": AI_POLICY_Q, "domain": "ai_policy", "include_stale": False},
        )
        assert r.status_code == 200
        assert len(r.json().get("answer", "")) > 50


class TestAllDomainsHaveData:
    """CRITICAL: All three domains must have data before the demo."""

    @pytest.mark.parametrize("domain", ["medical", "finance", "ai_policy"])
    def test_domain_has_chunks(self, live_client, domain):
        d = live_client.get(f"/freshness/dashboard/{domain}").json()
        assert d.get("total", 0) > 0, (
            f"❌ {domain} has no data! Run: python scripts/seed_demo_data.py"
        )
        print(f"\n✅ {domain}: {d['total']} chunks")


class TestSelfHealingDemoProof:
    """Prove the core KnowShift value proposition before the demo."""

    def test_fresh_score_gte_stale_score(self, live_client):
        stale = live_client.post(
            "/query/ask",
            json={"question": DIABETES_Q, "domain": "medical", "include_stale": True},
        ).json()
        fresh = live_client.post(
            "/query/ask",
            json={"question": DIABETES_Q, "domain": "medical", "include_stale": False},
        ).json()
        ss = stale["freshness_confidence"]
        fs = fresh["freshness_confidence"]
        print(f"\n🎯 Stale={ss:.2f}  Fresh={fs:.2f}")
        assert fs >= ss, (
            "Fresh index should ≥ stale. Run backdate_documents.py first."
        )


class TestMasterDemoGate:
    """
    MASTER CHECK — run this first before starting the demo.
    All sub-checks must pass.
    """

    def test_api_ready_for_demo(self, live_client):
        checks: dict[str, bool] = {}

        # Infrastructure
        h = live_client.get("/health")
        checks["api_health"] = h.status_code == 200

        # All domains have data
        for domain in ["medical", "finance", "ai_policy"]:
            d = live_client.get(f"/freshness/dashboard/{domain}").json()
            checks[f"{domain}_has_data"] = d.get("total", 0) > 0

        # Query works
        q = live_client.post(
            "/query/ask",
            json={"question": DIABETES_Q, "domain": "medical"},
        )
        checks["query_works"] = q.status_code == 200

        # Compare works
        c = live_client.get(
            "/query/compare",
            params={"question": DIABETES_Q, "domain": "medical"},
        )
        checks["compare_works"] = c.status_code == 200

        # Print summary
        print("\n🚀 DEMO READINESS CHECK:")
        all_pass = True
        for check, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"   {icon} {check}")
            if not passed:
                all_pass = False

        assert all_pass, "❌ System not ready for demo! Fix failing checks above."
