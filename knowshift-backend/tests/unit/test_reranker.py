"""
Unit tests for the temporal reranking engine (reranker.py).
Tests combined scoring, domain weights, and conflict detection.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

# root conftest.py already stubbed app.database and app.config
from app.services.reranker import (
    rerank_chunks,
    detect_ranking_conflicts,
    explain_ranking,
    _DOMAIN_WEIGHTS,     # private but tested to ensure contract
)

# Convenient alias used throughout tests
DOMAIN_WEIGHTS = _DOMAIN_WEIGHTS


def _chunk(
    chunk_id="c-001",
    similarity=0.80,
    freshness=0.90,
    source="Test Source",
):
    return {
        "chunk_id":        chunk_id,
        "chunk_text":      f"Some text for {chunk_id}",
        "similarity":      similarity,
        "freshness_score": freshness,
        "source_name":     source,
        "last_verified":   datetime.now(timezone.utc).isoformat(),
        "document_id":     "doc-001",
    }


class TestRerankChunks:
    """Tests for rerank_chunks()."""

    @pytest.mark.unit
    def test_returns_sorted_by_combined_score_desc(self, sample_retrieved_chunks):
        ranked = rerank_chunks(sample_retrieved_chunks, "medical")
        scores = [c["combined_score"] for c in ranked]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.unit
    def test_combined_score_added_to_every_chunk(self, sample_retrieved_chunks):
        ranked = rerank_chunks(sample_retrieved_chunks, "medical")
        for c in ranked:
            assert "combined_score" in c
            assert 0.0 <= c["combined_score"] <= 1.0

    @pytest.mark.unit
    def test_staleness_warning_field_present(self, sample_retrieved_chunks):
        ranked = rerank_chunks(sample_retrieved_chunks, "medical")
        for c in ranked:
            assert "staleness_warning" in c

    @pytest.mark.unit
    def test_stale_chunk_has_warning_true(self, sample_retrieved_chunks):
        # reranker uses < 0.5 threshold
        ranked = rerank_chunks(sample_retrieved_chunks, "medical")
        for c in ranked:
            if c["freshness_score"] < 0.5:
                assert c["staleness_warning"] is True

    @pytest.mark.unit
    def test_fresh_chunk_warning_is_false(self):
        ranked = rerank_chunks([_chunk("fresh", freshness=0.9)], "medical")
        assert ranked[0]["staleness_warning"] is False

    @pytest.mark.unit
    def test_fresh_chunk_ranks_higher_when_semantics_equal(self):
        fresh = _chunk("fresh", similarity=0.87, freshness=0.95)
        stale = _chunk("stale", similarity=0.87, freshness=0.08)
        ranked = rerank_chunks([fresh, stale], "medical")
        assert ranked[0]["chunk_id"] == "fresh"

    @pytest.mark.unit
    def test_empty_input_returns_empty_list(self):
        assert rerank_chunks([], "medical") == []

    @pytest.mark.unit
    def test_single_chunk_returned_with_combined_score(self):
        result = rerank_chunks([_chunk()], "medical")
        assert len(result) == 1
        assert "combined_score" in result[0]

    @pytest.mark.unit
    def test_authority_score_field_added(self):
        result = rerank_chunks([_chunk()], "medical")
        assert "authority_score" in result[0]

    @pytest.mark.unit
    def test_explanation_field_added(self):
        result = rerank_chunks([_chunk()], "medical")
        assert "explanation" in result[0]
        assert len(result[0]["explanation"]) > 0

    @pytest.mark.unit
    @pytest.mark.parametrize("domain", ["medical", "finance", "ai_policy"])
    def test_all_domains_produce_valid_scores(self, domain):
        chunks = [_chunk("c1", 0.8, 0.9), _chunk("c2", 0.7, 0.5)]
        ranked = rerank_chunks(chunks, domain)
        for c in ranked:
            assert 0.0 <= c["combined_score"] <= 1.0


class TestDomainWeights:
    """Validate domain weight constants."""

    @pytest.mark.unit
    def test_all_domains_present(self):
        for d in ("medical", "finance", "ai_policy"):
            assert d in DOMAIN_WEIGHTS

    @pytest.mark.unit
    def test_weights_are_tuples_of_3(self):
        for domain, w in DOMAIN_WEIGHTS.items():
            assert len(w) == 3, f"{domain} weights tuple must have 3 elements"

    @pytest.mark.unit
    def test_weights_sum_to_one(self):
        for domain, (a, b, g) in DOMAIN_WEIGHTS.items():
            total = a + b + g
            assert abs(total - 1.0) < 0.01, f"{domain} weights sum to {total}"

    @pytest.mark.unit
    def test_finance_highest_freshness_weight(self):
        # β is index [1]
        finance_beta   = DOMAIN_WEIGHTS["finance"][1]
        medical_beta   = DOMAIN_WEIGHTS["medical"][1]
        ai_policy_beta = DOMAIN_WEIGHTS["ai_policy"][1]
        assert finance_beta >= medical_beta
        assert finance_beta >= ai_policy_beta

    @pytest.mark.unit
    def test_all_weights_positive(self):
        for domain, weights in DOMAIN_WEIGHTS.items():
            for w in weights:
                assert w > 0, f"{domain} has zero/negative weight: {w}"


class TestDetectRankingConflicts:
    """Tests for detect_ranking_conflicts()."""

    @pytest.mark.unit
    def test_flags_high_similarity_low_freshness(self):
        # conflict: sim > 0.85 AND freshness < 0.5
        chunks = [{
            "chunk_id":        "conflict-001",
            "similarity":       0.92,
            "freshness_score":  0.08,
            "staleness_warning": True,
            "combined_score":   0.55,
            "source_name":      "Old Source",
            "last_verified":    "2021-01-01",
        }]
        conflicts = detect_ranking_conflicts(chunks)
        assert len(conflicts) > 0
        assert conflicts[0]["chunk_id"] == "conflict-001"

    @pytest.mark.unit
    def test_no_conflict_for_fresh_relevant_chunk(self):
        chunks = [{
            "chunk_id":        "no-conflict",
            "similarity":       0.92,
            "freshness_score":  0.95,
            "staleness_warning": False,
            "combined_score":   0.93,
            "source_name":      "Fresh Source",
        }]
        assert detect_ranking_conflicts(chunks) == []

    @pytest.mark.unit
    def test_no_conflict_for_stale_irrelevant_chunk(self):
        chunks = [{
            "chunk_id":        "irrelevant-stale",
            "similarity":       0.30,   # below 0.85 threshold
            "freshness_score":  0.05,
            "staleness_warning": True,
            "combined_score":   0.20,
            "source_name":      "Old Irrelevant",
        }]
        assert detect_ranking_conflicts(chunks) == []

    @pytest.mark.unit
    def test_conflict_has_required_fields(self):
        chunks = [{
            "chunk_id":       "c1",
            "similarity":      0.92,
            "freshness_score": 0.10,
            "source_name":     "Old",
            "last_verified":   "2021-01-01",
        }]
        conflicts = detect_ranking_conflicts(chunks)
        assert len(conflicts) == 1
        for field in ("chunk_id", "semantic_similarity", "freshness_score", "reason", "suggested_action"):
            assert field in conflicts[0], f"Missing conflict field: {field}"


class TestExplainRanking:
    """Tests for explain_ranking()."""

    @pytest.mark.unit
    def test_returns_non_empty_string(self):
        chunk = {
            "similarity":      0.85,
            "freshness_score": 0.92,
            "combined_score":  0.88,
            "authority_score": 0.80,
        }
        result = explain_ranking(chunk, alpha=0.5, beta=0.4, gamma=0.1)
        assert isinstance(result, str) and len(result) > 0

    @pytest.mark.unit
    def test_contains_rank_score(self):
        chunk = {"similarity": 0.8, "freshness_score": 0.9, "combined_score": 0.85}
        result = explain_ranking(chunk, 0.5, 0.4, 0.1)
        assert "Rank Score" in result

    @pytest.mark.unit
    def test_contains_percentage_values(self):
        chunk = {"similarity": 0.8, "freshness_score": 0.9, "combined_score": 0.85}
        result = explain_ranking(chunk, 0.5, 0.4, 0.1)
        assert "%" in result
