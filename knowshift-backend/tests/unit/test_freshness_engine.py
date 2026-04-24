"""
Unit tests for the freshness engine service.
Tests exponential decay formula, domain constants, and staleness detection.
NO external dependencies — runs fully offline.
"""

import math
import pytest
from datetime import datetime, timezone, timedelta

from app.services.freshness_engine import (
    compute_freshness_score,
    get_validity_horizon,
    DOMAIN_DECAY,
)


# ── compute_freshness_score ───────────────────────────────────────────────────

class TestComputeFreshnessScore:
    """Tests for exp(-λ·days) decay formula."""

    @pytest.mark.unit
    def test_freshly_verified_returns_near_one(self):
        now = datetime.now(timezone.utc)
        score = compute_freshness_score(now, "medical")
        assert 0.99 <= score <= 1.0

    @pytest.mark.unit
    def test_score_decreases_with_age(self):
        now = datetime.now(timezone.utc)
        s30  = compute_freshness_score(now - timedelta(days=30),  "medical")
        s90  = compute_freshness_score(now - timedelta(days=90),  "medical")
        s180 = compute_freshness_score(now - timedelta(days=180), "medical")
        assert s30 > s90 > s180 > 0

    @pytest.mark.unit
    def test_medical_decays_faster_than_ai_policy(self):
        ts = datetime.now(timezone.utc) - timedelta(days=90)
        assert compute_freshness_score(ts, "medical") < compute_freshness_score(ts, "ai_policy")

    @pytest.mark.unit
    def test_finance_decays_fastest(self):
        ts = datetime.now(timezone.utc) - timedelta(days=90)
        f = compute_freshness_score(ts, "finance")
        m = compute_freshness_score(ts, "medical")
        a = compute_freshness_score(ts, "ai_policy")
        assert f < m < a

    @pytest.mark.unit
    def test_score_never_negative(self):
        ancient = datetime.now(timezone.utc) - timedelta(days=3650)
        assert compute_freshness_score(ancient, "finance") >= 0.0

    @pytest.mark.unit
    def test_score_never_exceeds_one(self):
        assert compute_freshness_score(datetime.now(timezone.utc), "medical") <= 1.0

    @pytest.mark.unit
    def test_unknown_domain_uses_default_decay(self):
        ts = datetime.now(timezone.utc) - timedelta(days=100)
        score = compute_freshness_score(ts, "unknown_domain")
        expected = round(math.exp(-0.01 * 100), 4)
        assert abs(score - expected) < 0.05

    @pytest.mark.unit
    def test_score_rounded_to_4_decimal_places(self):
        ts = datetime.now(timezone.utc) - timedelta(days=45)
        score = compute_freshness_score(ts, "medical")
        assert score == round(score, 4)

    @pytest.mark.unit
    def test_decay_formula_exact(self):
        ts = datetime.now(timezone.utc) - timedelta(days=100)
        score = compute_freshness_score(ts, "medical")
        expected = round(math.exp(-DOMAIN_DECAY["medical"] * 100), 4)
        assert score == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("domain,days,approx", [
        ("medical",    0,   1.00),
        ("medical",   90,   0.26),
        ("finance",   30,   0.47),
        ("ai_policy", 365,  0.16),
    ])
    def test_parametrized_scores(self, domain, days, approx):
        ts = datetime.now(timezone.utc) - timedelta(days=days)
        assert abs(compute_freshness_score(ts, domain) - approx) < 0.05


# ── get_validity_horizon ──────────────────────────────────────────────────────

class TestGetValidityHorizon:

    @pytest.mark.unit
    def test_medical_180(self):
        assert get_validity_horizon("medical") == 180

    @pytest.mark.unit
    def test_finance_90(self):
        assert get_validity_horizon("finance") == 90

    @pytest.mark.unit
    def test_ai_policy_365(self):
        assert get_validity_horizon("ai_policy") == 365

    @pytest.mark.unit
    def test_unknown_domain_defaults_365(self):
        assert get_validity_horizon("unknown") == 365


# ── DOMAIN_DECAY constants ────────────────────────────────────────────────────

class TestDomainDecayConstants:

    @pytest.mark.unit
    def test_all_domains_present(self):
        for d in ("medical", "finance", "ai_policy"):
            assert d in DOMAIN_DECAY

    @pytest.mark.unit
    def test_all_rates_positive(self):
        for domain, rate in DOMAIN_DECAY.items():
            assert rate > 0, f"{domain} decay rate must be positive"

    @pytest.mark.unit
    def test_finance_highest_decay(self):
        assert DOMAIN_DECAY["finance"] > DOMAIN_DECAY["medical"]
        assert DOMAIN_DECAY["finance"] > DOMAIN_DECAY["ai_policy"]

    @pytest.mark.unit
    def test_ai_policy_lowest_decay(self):
        assert DOMAIN_DECAY["ai_policy"] < DOMAIN_DECAY["medical"]
        assert DOMAIN_DECAY["ai_policy"] < DOMAIN_DECAY["finance"]


# ── Staleness threshold tests ─────────────────────────────────────────────────

class TestStalenessThreshold:
    """Documents older than their validity horizon should score < 0.4."""

    @pytest.mark.unit
    @pytest.mark.parametrize("domain,days", [
        ("medical",   260),
        ("finance",   150),
        ("ai_policy", 500),
    ])
    def test_beyond_horizon_is_stale(self, domain, days):
        ts = datetime.now(timezone.utc) - timedelta(days=days)
        assert compute_freshness_score(ts, domain) < 0.4

    @pytest.mark.unit
    @pytest.mark.parametrize("domain,days", [
        ("medical",   10),
        ("finance",   10),
        ("ai_policy", 10),
    ])
    def test_fresh_documents_above_threshold(self, domain, days):
        ts = datetime.now(timezone.utc) - timedelta(days=days)
        assert compute_freshness_score(ts, domain) >= 0.7
