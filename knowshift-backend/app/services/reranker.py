"""
KnowShift — Temporal Reranking Engine  (Phase 2 — full implementation)

Reranks pgvector results using three signals:
  α · semantic_similarity  +  β · freshness_score  +  γ · authority_score

Domain-specific weight presets bias the formula toward what matters most
per vertical (e.g., finance cares most about freshness; ai_policy less so).
"""

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain weight presets  (α, β, γ)
# ---------------------------------------------------------------------------
_DOMAIN_WEIGHTS: Dict[str, Tuple[float, float, float]] = {
    "medical":   (0.5, 0.40, 0.10),   # Boost freshness — drug guidelines change fast
    "finance":   (0.5, 0.45, 0.05),   # Maximum freshness weight — regs are time-critical
    "ai_policy": (0.6, 0.30, 0.10),   # Standard — policy evolves more slowly
}
_DEFAULT_WEIGHTS: Tuple[float, float, float] = (0.6, 0.30, 0.10)

# ---------------------------------------------------------------------------
# Authority patterns — extend this list for richer scoring in Phase 3
# ---------------------------------------------------------------------------
_AUTHORITY_RULES: Dict[str, float] = {
    # Medical
    "who": 1.0, "cdc": 1.0, "fda": 1.0, "nih": 1.0, "lancet": 0.95, "nejm": 0.95,
    # Finance
    "irs": 1.0, "rbi": 1.0, "sec": 1.0, "fed": 1.0, "ecb": 1.0, "imf": 1.0,
    # AI / Policy
    "eu": 1.0, "nist": 1.0, "iso": 1.0, "ieee": 0.95, "acm": 0.90,
    # Generic high-quality
    "government": 0.95, "gov": 0.95, "official": 0.90,
}
_DEFAULT_AUTHORITY = 0.80


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _authority_score(source_name: str) -> float:
    """Derive an authority score from the source name.

    Simple keyword-match heuristic — will be replaced by a proper reputation
    lookup in Phase 3.

    Args:
        source_name: Human-readable name of the source document.

    Returns:
        Float between 0.0 and 1.0.
    """
    name_lower = source_name.lower()
    for keyword, score in _AUTHORITY_RULES.items():
        if keyword in name_lower:
            return score
    return _DEFAULT_AUTHORITY


def _get_weights(domain: str, alpha: float, beta: float, gamma: float) -> Tuple[float, float, float]:
    """Return effective weights — use caller-supplied values unless they are
    the default (0.6, 0.3, 0.1), in which case apply domain presets."""
    if (alpha, beta, gamma) == (0.6, 0.3, 0.1):
        return _DOMAIN_WEIGHTS.get(domain, _DEFAULT_WEIGHTS)
    return (alpha, beta, gamma)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def explain_ranking(chunk: Dict[str, Any], alpha: float, beta: float, gamma: float) -> str:
    """Generate a human-readable explanation of a chunk's combined score.

    Example output:
        "Rank Score: 0.8720 | Semantic: 0.920 (50%) + Freshness: 0.780 (40%) + Authority: 0.800 (10%)"

    Args:
        chunk: A reranked chunk dict (must have combined_score already set).
        alpha, beta, gamma: The weights used for this chunk.

    Returns:
        Formatted explanation string.
    """
    sim  = chunk.get("similarity", 0.0)
    fres = chunk.get("freshness_score", 0.0)
    auth = chunk.get("authority_score", _DEFAULT_AUTHORITY)
    comb = chunk.get("combined_score", 0.0)

    a_pct = int(round(alpha * 100))
    b_pct = int(round(beta  * 100))
    g_pct = int(round(gamma * 100))

    return (
        f"Rank Score: {comb:.4f} | "
        f"Semantic: {sim:.3f} ({a_pct}%) + "
        f"Freshness: {fres:.3f} ({b_pct}%) + "
        f"Authority: {auth:.3f} ({g_pct}%)"
    )


def detect_ranking_conflicts(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify chunks that are semantically relevant but temporally stale.

    A "conflict" is a chunk where:
        similarity > 0.85  AND  freshness_score < 0.5

    These are the most dangerous cases — the model would use highly
    relevant but outdated information in its answer.

    Args:
        chunks: Reranked chunk list (combined_score already present).

    Returns:
        List of conflict descriptors, each with:
            chunk_id, semantic_similarity, freshness_score,
            reason, suggested_action
    """
    conflicts: List[Dict[str, Any]] = []

    for chunk in chunks:
        sim  = chunk.get("similarity", 0.0)
        fres = chunk.get("freshness_score", 1.0)

        if sim > 0.85 and fres < 0.5:
            last_verified = chunk.get("last_verified", "unknown")
            conflicts.append({
                "chunk_id":           chunk.get("chunk_id"),
                "semantic_similarity": round(sim, 4),
                "freshness_score":    round(fres, 4),
                "source_name":        chunk.get("source_name", "unknown"),
                "last_verified":      str(last_verified),
                "reason": (
                    f"High semantic relevance ({sim:.2f}) but very stale "
                    f"(freshness={fres:.2f}, last_verified={last_verified})."
                ),
                "suggested_action": "Flag for verification or re-indexing",
            })

    logger.info("detect_ranking_conflicts | conflicts found: %d", len(conflicts))
    return conflicts


def rerank_chunks(
    chunks: List[Dict[str, Any]],
    domain: str,
    alpha: float = 0.6,
    beta:  float = 0.3,
    gamma: float = 0.1,
) -> List[Dict[str, Any]]:
    """Re-score and sort chunks using temporal + semantic + authority signals.

    Formula:
        combined_score = α·similarity + β·freshness_score + γ·authority_score

    Domain-specific weight presets are applied automatically unless the caller
    explicitly overrides all three weights.

    Mutates each chunk dict in-place, adding:
        - ``authority_score``  (float)
        - ``combined_score``   (float)
        - ``staleness_warning`` (bool) — True when freshness_score < 0.5
        - ``explanation``       (str)  — human-readable score breakdown

    Args:
        chunks: Raw retrieval results from ``retrieve_chunks()``.
        domain: Knowledge domain for weight selection.
        alpha: Weight for semantic similarity (default 0.6 → overridden by presets).
        beta:  Weight for freshness score     (default 0.3 → overridden by presets).
        gamma: Weight for authority score     (default 0.1 → overridden by presets).

    Returns:
        Sorted list (descending combined_score).
    """
    eff_alpha, eff_beta, eff_gamma = _get_weights(domain, alpha, beta, gamma)
    logger.debug(
        "rerank_chunks | domain=%s | weights=(α=%.2f β=%.2f γ=%.2f) | n=%d",
        domain, eff_alpha, eff_beta, eff_gamma, len(chunks),
    )

    for chunk in chunks:
        sim   = float(chunk.get("similarity", 0.0))
        fres  = float(chunk.get("freshness_score", 1.0))
        auth  = _authority_score(chunk.get("source_name", ""))

        combined = (eff_alpha * sim) + (eff_beta * fres) + (eff_gamma * auth)

        chunk["authority_score"]   = round(auth, 4)
        chunk["combined_score"]    = round(combined, 4)
        chunk["staleness_warning"] = fres < 0.5
        chunk["explanation"]       = explain_ranking(
            chunk, eff_alpha, eff_beta, eff_gamma
        )

    sorted_chunks = sorted(chunks, key=lambda c: c["combined_score"], reverse=True)

    if sorted_chunks:
        logger.info(
            "Reranking complete | domain=%s | top_score=%.4f | n=%d",
            domain, sorted_chunks[0]["combined_score"], len(sorted_chunks),
        )

    return sorted_chunks
