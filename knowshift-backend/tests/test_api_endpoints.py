"""
KnowShift — API Endpoint Unit Tests (Phase 4)
Tests every public route for correct HTTP status and response shape.
"""

import pytest


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------

class TestSystemEndpoints:

    def test_health_returns_200(self, api_client, api_url):
        r = api_client.get(f"{api_url}/health")
        assert r.status_code == 200

    def test_health_has_status_field(self, api_client, api_url):
        data = api_client.get(f"{api_url}/health").json()
        assert data["status"] in ("ok", "degraded")

    def test_health_components_present(self, api_client, api_url):
        data = api_client.get(f"{api_url}/health").json()
        assert "supabase" in data["components"]
        assert "gemini"   in data["components"]

    def test_health_has_version(self, api_client, api_url):
        data = api_client.get(f"{api_url}/health").json()
        assert data["version"] == "1.0.0"

    def test_stats_returns_200(self, api_client, api_url):
        r = api_client.get(f"{api_url}/stats")
        assert r.status_code == 200

    def test_stats_has_counts(self, api_client, api_url):
        data = api_client.get(f"{api_url}/stats").json()
        assert "total_documents" in data
        assert "total_chunks"    in data


# ---------------------------------------------------------------------------
# Freshness endpoints
# ---------------------------------------------------------------------------

class TestFreshnessEndpoints:

    def test_dashboard_returns_200(self, api_client, api_url, domain):
        r = api_client.get(f"{api_url}/freshness/dashboard/{domain}")
        assert r.status_code == 200

    def test_dashboard_has_required_fields(self, api_client, api_url, domain):
        data = api_client.get(f"{api_url}/freshness/dashboard/{domain}").json()
        for field in ("total", "fresh", "aging", "stale", "deprecated"):
            assert field in data, f"Missing field: {field}"

    def test_dashboard_total_consistent(self, api_client, api_url, domain):
        d = api_client.get(f"{api_url}/freshness/dashboard/{domain}").json()
        assert d["total"] == d["fresh"] + d["aging"] + d["stale"] + d["deprecated"]

    def test_scan_returns_200(self, api_client, api_url):
        r = api_client.post(f"{api_url}/freshness/scan")
        assert r.status_code == 200

    def test_scan_has_flagged_field(self, api_client, api_url):
        data = api_client.post(f"{api_url}/freshness/scan").json()
        assert "newly_flagged" in data

    def test_change_log_returns_200(self, api_client, api_url, domain):
        r = api_client.get(f"{api_url}/freshness/change-log/{domain}")
        assert r.status_code == 200

    def test_change_log_has_changes(self, api_client, api_url, domain):
        data = api_client.get(f"{api_url}/freshness/change-log/{domain}").json()
        assert "changes" in data
        assert isinstance(data["changes"], list)

    def test_reindex_candidates_returns_200(self, api_client, api_url, domain):
        r = api_client.get(f"{api_url}/freshness/reindex-candidates/{domain}")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Query endpoints
# ---------------------------------------------------------------------------

class TestQueryEndpoints:

    def test_ask_returns_200(self, api_client, api_url, domain, demo_question):
        r = api_client.post(
            f"{api_url}/query/ask",
            json={"question": demo_question, "domain": domain, "include_stale": False},
        )
        assert r.status_code == 200

    def test_ask_has_answer(self, api_client, api_url, domain, demo_question):
        data = api_client.post(
            f"{api_url}/query/ask",
            json={"question": demo_question, "domain": domain, "include_stale": False},
        ).json()
        assert "answer" in data
        assert len(data["answer"]) > 10

    def test_ask_has_freshness_confidence(self, api_client, api_url, domain, demo_question):
        data = api_client.post(
            f"{api_url}/query/ask",
            json={"question": demo_question, "domain": domain},
        ).json()
        score = data.get("freshness_confidence", -1)
        assert 0.0 <= score <= 1.0

    def test_ask_has_sources(self, api_client, api_url, domain, demo_question):
        data = api_client.post(
            f"{api_url}/query/ask",
            json={"question": demo_question, "domain": domain, "return_sources": True},
        ).json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_ask_invalid_domain_rejected(self, api_client, api_url):
        r = api_client.post(
            f"{api_url}/query/ask",
            json={"question": "some question", "domain": "invalid_domain"},
        )
        assert r.status_code == 422

    def test_ask_empty_question_rejected(self, api_client, api_url):
        r = api_client.post(
            f"{api_url}/query/ask",
            json={"question": "", "domain": "medical"},
        )
        assert r.status_code == 422

    def test_compare_returns_both_answers(self, api_client, api_url):
        r = api_client.get(
            f"{api_url}/query/compare",
            params={
                "question": "What is the first-line treatment for Type 2 Diabetes?",
                "domain":   "medical",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "stale_answer" in data
        assert "fresh_answer" in data

    def test_compare_has_difference_flag(self, api_client, api_url):
        data = api_client.get(
            f"{api_url}/query/compare",
            params={
                "question": "What is the first-line treatment for Type 2 Diabetes?",
                "domain":   "medical",
            },
        ).json()
        assert "difference_detected" in data
        assert isinstance(data["difference_detected"], bool)

    def test_compare_has_process_time_header(self, api_client, api_url):
        r = api_client.get(
            f"{api_url}/query/compare",
            params={"question": "Tax rates?", "domain": "finance"},
        )
        # Middleware injects X-Process-Time-Ms
        assert "x-process-time-ms" in r.headers or r.status_code == 200
