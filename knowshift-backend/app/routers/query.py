"""
KnowShift — Query Router  (Phase 2 — full RAG endpoints)

Endpoints:
    POST /query/ask      — Full RAG pipeline: embed → retrieve → rerank → generate
    GET  /query/compare  — Side-by-side stale-vs-fresh answer comparison
"""

import logging
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.config import settings
from app.services.embedder import embed_query
from app.services.retriever import retrieve_chunks
from app.services.reranker import rerank_chunks, detect_ranking_conflicts

logger = logging.getLogger(__name__)

# Configure Gemini client once at module load
genai.configure(api_key=settings.gemini_api_key)

router = APIRouter()

_DOMAIN_EXPERT: Dict[str, str] = {
    "medical":   "medical expert and clinician",
    "finance":   "financial advisor and regulatory analyst",
    "ai_policy": "AI policy analyst and governance expert",
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question:      str  = Field(..., min_length=5, max_length=500)
    domain:        str  = Field(..., pattern="^(medical|finance|ai_policy)$")
    include_stale: bool = Field(default=False,  description="Include stale document chunks")
    top_k:         int  = Field(default=10, ge=1, le=20, description="Chunks to retrieve")
    return_sources:bool = Field(default=True,   description="Attach source metadata")


class SourceInfo(BaseModel):
    source_name:    str
    last_verified:  str
    freshness_score: float
    chunk_preview:  str   # First 100 chars of the chunk


class QueryResponse(BaseModel):
    answer:               str
    freshness_confidence: float
    staleness_warning:    bool
    sources:              List[SourceInfo]      = []
    ranking_conflicts:    List[Dict[str, Any]]  = []
    processing_time_ms:   int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_context(top_chunks: List[Dict[str, Any]]) -> str:
    """Format top-k chunks into a prompt-ready context block."""
    parts = []
    for i, chunk in enumerate(top_chunks, start=1):
        source    = chunk.get("source_name",    "Unknown source")
        verified  = chunk.get("last_verified",  "unknown date")
        freshness = chunk.get("freshness_score", 0.0)
        text      = chunk.get("chunk_text", "")
        parts.append(
            f"[{i}] Source: {source} | Last verified: {verified} | "
            f"Freshness: {freshness:.2f}\n{text}"
        )
    return "\n\n---\n\n".join(parts)


def _build_prompt(question: str, domain: str, context: str) -> str:
    expert = _DOMAIN_EXPERT.get(domain, "domain expert")
    return (
        f"You are a {expert}.\n\n"
        "Answer the question using ONLY the provided context below. "
        "For each piece of information, cite the source name and its verification date. "
        "If the context is insufficient, say so explicitly. "
        "If you notice conflicting or potentially outdated information, highlight it.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer (with inline citations):"
    )


def _generate_answer(prompt: str) -> str:
    """Call Gemini Flash to generate an answer from the prompt."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        logger.error("Gemini generation failed: %s", exc)
        return (
            "Answer generation encountered an error. "
            "Please check the sources below for information relevant to your query."
        )


# ---------------------------------------------------------------------------
# POST /ask — primary RAG endpoint
# ---------------------------------------------------------------------------

@router.post("/ask", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def ask(req: QueryRequest) -> QueryResponse:
    """Full RAG pipeline with temporal reranking.

    Pipeline:
        1. Embed user question
        2. Retrieve top_k chunks via pgvector ANN
        3. Temporal rerank (semantic + freshness + authority)
        4. Detect ranking conflicts (high-relevance stale chunks)
        5. Build context from top-5 chunks
        6. Generate answer with Gemini 1.5 Flash
        7. Return structured response with sources and metadata
    """
    start_time = time.time()
    logger.info(
        "Query received | domain=%s | preview='%s...'",
        req.domain, req.question[:60],
    )

    # ------------------------------------------------------------------
    # 1. Embed query
    # ------------------------------------------------------------------
    try:
        q_embedding = embed_query(req.question)
    except Exception as exc:
        logger.error("Query embedding failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding failed: {exc}",
        )

    # ------------------------------------------------------------------
    # 2. Retrieve chunks from pgvector
    # ------------------------------------------------------------------
    raw_chunks = retrieve_chunks(
        query_embedding=q_embedding,
        domain=req.domain,
        top_k=req.top_k,
        include_stale=req.include_stale,
    )

    if not raw_chunks:
        processing_time = int((time.time() - start_time) * 1000)
        logger.warning(
            "No chunks found | domain=%s | include_stale=%s",
            req.domain, req.include_stale,
        )
        return QueryResponse(
            answer="No relevant information found in the knowledge base for this domain.",
            freshness_confidence=0.0,
            staleness_warning=True,
            sources=[],
            ranking_conflicts=[],
            processing_time_ms=processing_time,
        )

    # ------------------------------------------------------------------
    # 3. Temporal rerank
    # ------------------------------------------------------------------
    ranked_chunks = rerank_chunks(raw_chunks, req.domain)

    # ------------------------------------------------------------------
    # 4. Detect knowledge conflicts
    # ------------------------------------------------------------------
    ranking_conflicts = detect_ranking_conflicts(ranked_chunks)

    # ------------------------------------------------------------------
    # 5. Build context from top-5 chunks
    # ------------------------------------------------------------------
    top5 = ranked_chunks[:5]
    context = _build_context(top5)

    # ------------------------------------------------------------------
    # 6. Freshness confidence metrics
    # ------------------------------------------------------------------
    freshness_scores = [c.get("freshness_score", 1.0) for c in top5]
    # Conservative: use the minimum freshness among top results
    freshness_confidence = round(min(freshness_scores), 3)
    has_stale = any(c.get("staleness_warning", False) for c in top5)

    # ------------------------------------------------------------------
    # 7. Generate answer
    # ------------------------------------------------------------------
    prompt = _build_prompt(req.question, req.domain, context)
    answer_text = _generate_answer(prompt)

    # ------------------------------------------------------------------
    # 8. Build sources list
    # ------------------------------------------------------------------
    sources: List[SourceInfo] = []
    if req.return_sources:
        for chunk in top5:
            raw_preview = chunk.get("chunk_text", "")
            sources.append(
                SourceInfo(
                    source_name=    chunk.get("source_name", "Unknown"),
                    last_verified=  str(chunk.get("last_verified", "")),
                    freshness_score=round(chunk.get("freshness_score", 0.0), 3),
                    chunk_preview=  raw_preview[:100] + ("…" if len(raw_preview) > 100 else ""),
                )
            )

    processing_time = int((time.time() - start_time) * 1000)
    logger.info(
        "Query complete | domain=%s | freshness_confidence=%.3f | time_ms=%d",
        req.domain, freshness_confidence, processing_time,
    )

    return QueryResponse(
        answer=answer_text,
        freshness_confidence=freshness_confidence,
        staleness_warning=has_stale,
        sources=sources,
        ranking_conflicts=ranking_conflicts,
        processing_time_ms=processing_time,
    )


# ---------------------------------------------------------------------------
# GET /compare — stale-vs-fresh side-by-side comparison
# ---------------------------------------------------------------------------

@router.get("/compare", status_code=status.HTTP_200_OK)
async def compare_stale_vs_fresh(
    question: str = Query(..., min_length=5, max_length=500),
    domain:   str = Query(..., pattern="^(medical|finance|ai_policy)$"),
    top_k:    int = Query(default=10, ge=1, le=20),
) -> Dict[str, Any]:
    """Run the same question with and without stale chunks, return both answers.

    Useful for the Change Map UI to demonstrate how index freshness impacts
    the quality and accuracy of generated answers.

    Returns:
        {
            "stale_answer":         QueryResponse,
            "fresh_answer":         QueryResponse,
            "difference_detected":  bool,
            "freshness_delta":      float   # fresh_confidence - stale_confidence
        }
    """
    logger.info("Compare request | domain=%s | question='%s...'", domain, question[:60])

    # Run both pipelines — sequential to avoid doubling Gemini rate usage
    stale_req = QueryRequest(
        question=question,
        domain=domain,
        include_stale=True,
        top_k=top_k,
        return_sources=True,
    )
    fresh_req = QueryRequest(
        question=question,
        domain=domain,
        include_stale=False,
        top_k=top_k,
        return_sources=True,
    )

    stale_result = await ask(stale_req)
    fresh_result = await ask(fresh_req)

    difference_detected = stale_result.answer != fresh_result.answer
    freshness_delta = round(
        fresh_result.freshness_confidence - stale_result.freshness_confidence, 3
    )

    return {
        "question":           question,
        "domain":             domain,
        "stale_answer":       stale_result,
        "fresh_answer":       fresh_result,
        "difference_detected": difference_detected,
        "freshness_delta":    freshness_delta,
    }
