"""
KnowShift — Freshness Engine Unit Tests (Phase 4)
Pure-Python tests for the mathematical and logic functions in freshness_engine.py.
No API calls; no Supabase connection required.
"""

import math
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Import the module under test
# (runs without supabase if the import-time client is mocked)
# ---------------------------------------------------------------------------

# Patch supabase at import time so tests run without credentials.
with patch("app.database.supabase", MagicMock()):
    from app.services.freshness_engine import compute_freshness_score


# ---------------------------------------------------------------------------
# compute_freshness_score
# ---------------------------------------------------------------------------

class TestComputeFreshnessScore:
    """
    freshness = exp(-λ × days)
    Domain decay rates (must match freshness_engine.py):
      medical   → 0.015  (180-day ~7.3% threshold)
      finance   → 0.025
      ai_policy → 0.005
    """

    def test_score_is_one_when_just_verified(self):
        now = datetime.now(timezone.utc)
        score = compute_freshness_score(now, "medical")
        assert abs(score - 1.0) < 0.01

    def test_score_decreases_with_age(self):
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=180)
        score_new = compute_freshness_score(now, "medical")
        score_old = compute_freshness_score(old, "medical")
        assert score_new > score_old

    def test_medical_180_days_below_threshold(self):
        old = datetime.now(timezone.utc) - timedelta(days=180)
        score = compute_freshness_score(old, "medical")
        # exp(-0.015 × 180) ≈ 0.0672 → clearly stale
        assert score < 0.4

    def test_finance_decays_faster_than_ai_policy(self):
        ts = datetime.now(timezone.utc) - timedelta(days=90)
        score_finance   = compute_freshness_score(ts, "finance")
        score_ai_policy = compute_freshness_score(ts, "ai_policy")
        assert score_finance < score_ai_policy

    def test_score_bounded_zero_to_one(self):
        ts = datetime.now(timezone.utc) - timedelta(days=1000)
        score = compute_freshness_score(ts, "medical")
        assert 0.0 <= score <= 1.0

    def test_unknown_domain_uses_default_decay(self):
        ts = datetime.now(timezone.utc) - timedelta(days=50)
        # Should not raise; uses fallback λ=0.01
        score = compute_freshness_score(ts, "unknown_domain")
        expected = math.exp(-0.01 * 50)
        assert abs(score - expected) < 0.05  # within 5 %

    @pytest.mark.parametrize("domain,days,expected_approx", [
        ("medical",   0,   1.00),
        ("medical",   90,  0.26),   # exp(-0.015 × 90)
        ("finance",   30,  0.47),   # exp(-0.025 × 30)
        ("ai_policy", 365, 0.16),   # exp(-0.005 × 365)
    ])
    def test_parametrized_scores(self, domain, days, expected_approx):
        ts = datetime.now(timezone.utc) - timedelta(days=days)
        score = compute_freshness_score(ts, domain)
        assert abs(score - expected_approx) < 0.05


# ---------------------------------------------------------------------------
# Staleness threshold tests
# ---------------------------------------------------------------------------

class TestStalenessThreshold:
    """Every document older than validity horizon should be < 0.4."""

    HORIZONS = {
        "medical":   180,
        "finance":    90,
        "ai_policy": 365,
    }

    @pytest.mark.parametrize("domain,days", [
        ("medical",   260),
        ("finance",   150),
        ("ai_policy", 500),
    ])
    def test_beyond_horizon_is_stale(self, domain, days):
        ts = datetime.now(timezone.utc) - timedelta(days=days)
        score = compute_freshness_score(ts, domain)
        assert score < 0.4, (
            f"Expected stale score for {domain} at {days} days, got {score:.3f}"
        )

    @pytest.mark.parametrize("domain,days", [
        ("medical",   10),
        ("finance",   10),
        ("ai_policy", 10),
    ])
    def test_fresh_documents_above_threshold(self, domain, days):
        ts = datetime.now(timezone.utc) - timedelta(days=days)
        score = compute_freshness_score(ts, domain)
        assert score >= 0.7
