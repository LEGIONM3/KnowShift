"""
Integration tests for /freshness/* endpoints.
Uses mocked Supabase — no live database needed.
"""

import pytest
from unittest.mock import patch


class TestFreshnessScanEndpoint:
    """Tests for POST /freshness/scan."""

    @pytest.mark.integration
    def test_scan_returns_200(self, app_client):
        with patch(
            "app.services.freshness_engine.detect_and_flag_stale",
            return_value={"newly_flagged": 2},
        ):
            r = app_client.post("/freshness/scan")
        assert r.status_code == 200

    @pytest.mark.integration
    def test_scan_returns_newly_flagged_int(self, app_client):
        with patch(
            "app.services.freshness_engine.detect_and_flag_stale",
            return_value={"newly_flagged": 3},
        ):
            d = app_client.post("/freshness/scan").json()
        assert isinstance(d.get("newly_flagged"), int)

    @pytest.mark.integration
    def test_scan_returns_zero_when_all_fresh(self, app_client):
        with patch(
            "app.services.freshness_engine.detect_and_flag_stale",
            return_value={"newly_flagged": 0},
        ):
            d = app_client.post("/freshness/scan").json()
        assert d["newly_flagged"] == 0


class TestFreshnessDashboardEndpoint:
    """Tests for GET /freshness/dashboard/{domain}."""

    @pytest.mark.integration
    def test_dashboard_returns_200(self, app_client, mock_supabase):
        r = app_client.get("/freshness/dashboard/medical")
        assert r.status_code == 200

    @pytest.mark.integration
    def test_dashboard_has_required_fields(self, app_client, mock_supabase):
        d = app_client.get("/freshness/dashboard/medical").json()
        for field in ("total", "fresh", "aging", "stale", "deprecated"):
            assert field in d, f"Missing dashboard field: {field}"

    @pytest.mark.integration
    def test_dashboard_totals_are_consistent(self, app_client, mock_supabase):
        d = app_client.get("/freshness/dashboard/finance").json()
        assert d["total"] == d["fresh"] + d["aging"] + d["stale"] + d["deprecated"]

    @pytest.mark.integration
    @pytest.mark.parametrize("domain", ["medical", "finance", "ai_policy"])
    def test_dashboard_works_for_all_domains(self, app_client, mock_supabase, domain):
        r = app_client.get(f"/freshness/dashboard/{domain}")
        assert r.status_code == 200


class TestChangeLogEndpoint:
    """Tests for GET /freshness/change-log/{domain}."""

    @pytest.mark.integration
    def test_change_log_returns_200(self, app_client, mock_supabase):
        r = app_client.get("/freshness/change-log/medical")
        assert r.status_code == 200

    @pytest.mark.integration
    def test_change_log_has_changes_list(self, app_client, mock_supabase):
        d = app_client.get("/freshness/change-log/medical").json()
        assert "changes" in d
        assert isinstance(d["changes"], list)

    @pytest.mark.integration
    def test_change_log_has_domain_field(self, app_client, mock_supabase):
        d = app_client.get("/freshness/change-log/finance").json()
        assert d.get("domain") == "finance"

    @pytest.mark.integration
    def test_change_log_has_total_changes(self, app_client, mock_supabase):
        d = app_client.get("/freshness/change-log/ai_policy").json()
        assert "total_changes" in d


class TestReindexCandidatesEndpoint:
    """Tests for GET /freshness/reindex-candidates/{domain}."""

    @pytest.mark.integration
    def test_reindex_candidates_returns_200(self, app_client, mock_supabase):
        r = app_client.get("/freshness/reindex-candidates/medical")
        assert r.status_code == 200
