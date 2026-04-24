"""
End-to-end tests for the complete KnowShift pipeline.
Requires a running API server at TEST_API_URL (default: http://localhost:8000).
These tests call the real API over HTTP — no mocks.

Run:
    TEST_API_URL=http://localhost:8000 pytest tests/e2e/ -v -m e2e
"""

import os
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

QUESTIONS = {
    "medical":   "What is the first-line treatment for Type 2 Diabetes?",
    "finance":   "What is the tax rate for income between Rs 10-12 lakhs?",
    "ai_policy": "What obligations do high-risk AI system providers have?",
}


class TestSystemEndpointsE2E:

    def test_health_returns_ok_or_degraded(self, live_client):
        r = live_client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] in ("ok", "degraded")

    def test_health_components_present(self, live_client):
        r = live_client.get("/health")
        comp = r.json().get("components", {})
        assert "supabase" in comp
        assert "gemini" in comp

    def test_stats_endpoint_returns_counts(self, live_client):
        r = live_client.get("/stats")
        assert r.status_code == 200
        d = r.json()
        assert "total_documents" in d
        assert "total_chunks" in d


class TestDomainDashboardsE2E:

    @pytest.mark.parametrize("domain", ["medical", "finance", "ai_policy"])
    def test_dashboard_accessible(self, live_client, domain):
        r = live_client.get(f"/freshness/dashboard/{domain}")
        assert r.status_code == 200
        for field in ("total", "fresh", "aging", "stale", "deprecated"):
            assert field in r.json()

    @pytest.mark.parametrize("domain", ["medical", "finance", "ai_policy"])
    def test_dashboard_totals_consistent(self, live_client, domain):
        d = live_client.get(f"/freshness/dashboard/{domain}").json()
        assert d["total"] == d["fresh"] + d["aging"] + d["stale"] + d["deprecated"]


class TestQueryPipelineE2E:

    @pytest.mark.parametrize("domain", ["medical", "finance", "ai_policy"])
    def test_fresh_query_returns_answer(self, live_client, domain):
        r = live_client.post(
            "/query/ask",
            json={"question": QUESTIONS[domain], "domain": domain, "include_stale": False},
        )
        assert r.status_code == 200
        d = r.json()
        assert len(d.get("answer", "")) > 10
        assert 0.0 <= d.get("freshness_confidence", -1) <= 1.0

    @pytest.mark.parametrize("domain", ["medical", "finance", "ai_policy"])
    def test_stale_query_returns_answer(self, live_client, domain):
        r = live_client.post(
            "/query/ask",
            json={"question": QUESTIONS[domain], "domain": domain, "include_stale": True},
        )
        assert r.status_code == 200
        assert "answer" in r.json()

    def test_sources_is_list(self, live_client):
        r = live_client.post(
            "/query/ask",
            json={
                "question":       QUESTIONS["medical"],
                "domain":         "medical",
                "return_sources": True,
            },
        )
        assert r.status_code == 200
        assert isinstance(r.json().get("sources"), list)

    def test_invalid_domain_returns_422(self, live_client):
        r = live_client.post(
            "/query/ask",
            json={"question": "Some question here", "domain": "cooking"},
        )
        assert r.status_code == 422


class TestCompareEndpointE2E:

    def test_compare_returns_both_answers(self, live_client):
        r = live_client.get(
            "/query/compare",
            params={"question": QUESTIONS["medical"], "domain": "medical"},
        )
        assert r.status_code == 200
        d = r.json()
        assert "stale_answer" in d
        assert "fresh_answer" in d
        assert "difference_detected" in d

    def test_compare_difference_detected_is_bool(self, live_client):
        r = live_client.get(
            "/query/compare",
            params={"question": QUESTIONS["finance"], "domain": "finance"},
        )
        assert isinstance(r.json().get("difference_detected"), bool)


class TestFreshnessE2E:

    def test_stale_scan_completes(self, live_client):
        r = live_client.post("/freshness/scan")
        assert r.status_code == 200
        assert "newly_flagged" in r.json()

    def test_change_log_accessible(self, live_client):
        r = live_client.get("/freshness/change-log/medical")
        assert r.status_code == 200
        d = r.json()
        assert "changes" in d
        assert isinstance(d["changes"], list)
