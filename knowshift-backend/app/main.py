"""
KnowShift — FastAPI Application Entry Point  (Phase 4 — Final)

Startup flow:
  1. Verify Supabase connection
  2. Configure Gemini API
  3. Log environment info
  4. Mount all routers

Middleware:
  - Request-timing header (X-Process-Time-Ms)
  - CORS (configured per environment)

Global exception handler returns structured JSON for both
dev (full detail) and production (safe message).
"""

import logging
import re
import time
from datetime import datetime, timezone

import google.generativeai as genai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import supabase
from app.routers import freshness, ingest, query

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("knowshift.main")

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="KnowShift API",
    description=(
        "Temporal Self-Healing RAG — freshness-aware retrieval, "
        "selective re-indexing, and change-log provenance."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Dev: localhost only
_ORIGINS_DEV = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Prod: exact canonical domain + regex for Vercel preview URLs.
# NOTE: Starlette does NOT expand "https://*.vercel.app" as a glob.
# allow_origin_regex handles preview deployments (branch / PR URLs).
_ORIGINS_PROD = ["https://knowshift.vercel.app"]
_ORIGIN_REGEX_PROD = r"https://knowshift(-[a-zA-Z0-9-]+)?\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS_DEV if settings.environment == "development" else _ORIGINS_PROD,
    allow_origin_regex=None if settings.environment == "development" else _ORIGIN_REGEX_PROD,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request-timing middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    return response


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s",
                 request.method, request.url.path, exc, exc_info=True)
    detail = str(exc) if settings.environment == "development" else "An unexpected error occurred"
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": detail},
    )


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("KnowShift API starting up | ENV=%s", settings.environment)

    # — Supabase —
    try:
        supabase.table("documents").select("id").limit(1).execute()
        logger.info("✅ Supabase connection verified")
    except Exception as exc:
        logger.error("❌ Supabase connection failed: %s", exc)

    # — Gemini —
    try:
        genai.configure(api_key=settings.gemini_api_key)
        logger.info("✅ Gemini API configured")
    except Exception as exc:
        logger.error("❌ Gemini API setup failed: %s", exc)

    logger.info("✅ KnowShift API ready | version=1.0.0")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(ingest.router,    prefix="/ingest",    tags=["Ingestion"])
app.include_router(query.router,     prefix="/query",     tags=["Query"])
app.include_router(freshness.router, prefix="/freshness", tags=["Freshness"])


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health():
    """Enhanced health check — verifies each component independently."""
    components: dict = {}

    # Supabase
    try:
        supabase.table("documents").select("id").limit(1).execute()
        components["supabase"] = "ok"
    except Exception as exc:
        components["supabase"] = f"error: {exc}"

    # Gemini (config-level check only — avoid wasting quota)
    try:
        genai.configure(api_key=settings.gemini_api_key)
        components["gemini"] = "ok"
    except Exception as exc:
        components["gemini"] = f"error: {exc}"

    overall = "ok" if all(v == "ok" for v in components.values()) else "degraded"

    return {
        "status":      overall,
        "components":  components,
        "version":     "1.0.0",
        "environment": settings.environment,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }


@app.get("/stats", tags=["System"])
async def get_stats():
    """System-wide document and chunk statistics for the demo HUD."""
    try:
        total_docs    = len(supabase.table("documents").select("id").execute().data or [])
        total_chunks  = len(supabase.table("chunks").select("id").execute().data or [])
        deprecated    = len(
            supabase.table("chunks").select("id").eq("is_deprecated", True).execute().data or []
        )
        total_changes = len(supabase.table("change_log").select("id").execute().data or [])

        return {
            "total_documents":    total_docs,
            "total_chunks":       total_chunks,
            "deprecated_chunks":  deprecated,
            "active_chunks":      total_chunks - deprecated,
            "total_change_events": total_changes,
            "self_healing_events": total_changes,
        }
    except Exception as exc:
        logger.error("Stats endpoint failed: %s", exc)
        return {"error": str(exc)}
