"""
Root conftest.py — runs BEFORE any test is collected.
Injects sys.modules stubs for app.config and app.database so that
the Supabase client is never instantiated during unit tests.

IMPORTANT: This file must live in knowshift-backend/ (the pytest rootdir),
not inside tests/, so it executes before any test module is imported.
"""

import os
import sys
import types
from unittest.mock import MagicMock

# ── 1. Set test environment variables ─────────────────────────────────────────
os.environ.setdefault("ENVIRONMENT",    "testing")
os.environ.setdefault("SUPABASE_URL",   "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY",   "test-key-123")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key-123")
os.environ.setdefault("REDIS_URL",      "redis://localhost:6379/0")

# ── 2. Stub app.config so pydantic never tries to resolve missing vars ─────────
_fake_settings = MagicMock()
_fake_settings.supabase_url          = "https://test.supabase.co"
_fake_settings.supabase_key          = "test-key-123"
_fake_settings.gemini_api_key        = "test-gemini-key-123"
_fake_settings.redis_url             = "redis://localhost:6379/0"
_fake_settings.environment           = "testing"
_fake_settings.medical_validity_days  = 180
_fake_settings.finance_validity_days  = 90
_fake_settings.ai_policy_validity_days = 365
_fake_settings.get_validity_days = (
    lambda domain:
    {"medical": 180, "finance": 90, "ai_policy": 365}.get(domain, 365)
)

_cfg_mod = types.ModuleType("app.config")
_cfg_mod.settings      = _fake_settings
_cfg_mod.get_settings  = lambda: _fake_settings
_cfg_mod.Settings      = MagicMock()
sys.modules.setdefault("app.config", _cfg_mod)

# ── 3. Stub app.database so create_client() is never called ───────────────────
_fake_supabase = MagicMock()
_db_mod = types.ModuleType("app.database")
_db_mod.supabase = _fake_supabase
sys.modules.setdefault("app.database", _db_mod)

# ── 4. Stub supabase SDK (only if not installed) ──────────────────────────────
if "supabase" not in sys.modules:
    _supabase_stub = types.ModuleType("supabase")
    _supabase_stub.create_client = MagicMock(return_value=_fake_supabase)
    _supabase_stub.Client        = MagicMock()
    sys.modules["supabase"] = _supabase_stub

# ── 5. Stub google.generativeai SDK (only if not installed) ───────────────────
if "google" not in sys.modules:
    _google_mod = types.ModuleType("google")
    sys.modules["google"] = _google_mod

if "google.generativeai" not in sys.modules:
    _genai_mod = types.ModuleType("google.generativeai")
    _genai_mod.configure        = MagicMock()
    _genai_mod.embed_content    = MagicMock(return_value={"embedding": [0.1] * 768})
    _genai_mod.GenerativeModel  = MagicMock()
    sys.modules["google.generativeai"] = _genai_mod

# ── 6. Pytest fixtures available to all tests ──────────────────────────────────
import pytest
from datetime import datetime, timezone, timedelta


@pytest.fixture
def sample_embedding():
    return [0.1] * 768


@pytest.fixture
def sample_query_embedding():
    return [0.15] * 768


@pytest.fixture
def sample_document_medical():
    return {
        "id":              "doc-medical-001",
        "domain":          "medical",
        "source_name":     "ADA Standards of Care 2024",
        "source_url":      "https://diabetesjournals.org/care",
        "published_at":    "2024-01-01T00:00:00+00:00",
        "last_verified":   datetime.now(timezone.utc).isoformat(),
        "validity_horizon": 180,
        "stale_flag":      False,
        "created_at":      datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_document_stale():
    old = datetime.now(timezone.utc) - timedelta(days=400)
    return {
        "id":              "doc-stale-001",
        "domain":          "medical",
        "source_name":     "ADA Standards of Care 2021",
        "source_url":      "https://diabetesjournals.org/care",
        "published_at":    "2021-01-01T00:00:00+00:00",
        "last_verified":   old.isoformat(),
        "validity_horizon": 180,
        "stale_flag":      True,
        "created_at":      old.isoformat(),
    }


@pytest.fixture
def sample_chunk_fresh(sample_embedding):
    return {
        "id":               "chunk-fresh-001",
        "document_id":      "doc-medical-001",
        "chunk_text":       "GLP-1 receptor agonists are recommended as first-line therapy.",
        "embedding":        sample_embedding,
        "freshness_score":  0.95,
        "is_deprecated":    False,
        "created_at":       datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def sample_chunk_stale(sample_embedding):
    old = datetime.now(timezone.utc) - timedelta(days=400)
    return {
        "id":               "chunk-stale-001",
        "document_id":      "doc-stale-001",
        "chunk_text":       "Metformin remains the preferred initial pharmacological agent.",
        "embedding":        sample_embedding,
        "freshness_score":  0.08,
        "is_deprecated":    False,
        "created_at":       old.isoformat(),
    }


@pytest.fixture
def sample_retrieved_chunks():
    now = datetime.now(timezone.utc)
    return [
        {
            "chunk_id":        "chunk-001",
            "chunk_text":      "GLP-1 agonists recommended as first-line (2024)",
            "freshness_score": 0.92,
            "similarity":      0.89,
            "published_at":    "2024-01-01T00:00:00+00:00",
            "last_verified":   now.isoformat(),
            "source_name":     "ADA Standards 2024",
            "document_id":     "doc-001",
        },
        {
            "chunk_id":        "chunk-002",
            "chunk_text":      "Metformin as first-line treatment (2021)",
            "freshness_score": 0.08,
            "similarity":      0.87,
            "published_at":    "2021-01-01T00:00:00+00:00",
            "last_verified":   (now - timedelta(days=400)).isoformat(),
            "source_name":     "ADA Standards 2021",
            "document_id":     "doc-002",
        },
        {
            "chunk_id":        "chunk-003",
            "chunk_text":      "SGLT2 inhibitors for heart failure patients",
            "freshness_score": 0.75,
            "similarity":      0.78,
            "published_at":    "2023-06-01T00:00:00+00:00",
            "last_verified":   (now - timedelta(days=60)).isoformat(),
            "source_name":     "Cardiology Guidelines 2023",
            "document_id":     "doc-003",
        },
    ]


@pytest.fixture
def sample_pdf_bytes():
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
        b"startxref\n190\n%%EOF"
    )


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = [{"id": "test-uuid"}]
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    mock.rpc.return_value.execute.return_value.data = []
    return mock


@pytest.fixture
def mock_embed_text(monkeypatch):
    monkeypatch.setattr(
        "app.services.embedder.embed_text",
        lambda text: [0.1] * 768,
    )


@pytest.fixture
def mock_embed_query(monkeypatch):
    monkeypatch.setattr(
        "app.services.embedder.embed_query",
        lambda text: [0.15] * 768,
    )


@pytest.fixture
def mock_gemini_generate(monkeypatch):
    resp = MagicMock()
    resp.text = (
        "Based on the 2024 ADA Standards, GLP-1 receptor agonists are "
        "first-line therapy for Type 2 Diabetes. [Source: ADA Standards 2024]"
    )
    mock_model = MagicMock()
    mock_model.generate_content.return_value = resp
    # Patch wherever the query router references the model
    try:
        monkeypatch.setattr("app.routers.query.model", mock_model)
    except AttributeError:
        pass
    return mock_model


@pytest.fixture
def app_client(mock_supabase, monkeypatch):
    """FastAPI TestClient with all external dependencies mocked."""
    monkeypatch.setattr("app.database.supabase", mock_supabase)
    try:
        monkeypatch.setattr("app.services.freshness_engine.supabase", mock_supabase)
    except AttributeError:
        pass
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def live_client():
    """HTTP client for E2E/performance/demo tests against a live API."""
    import httpx
    api_url = os.getenv("TEST_API_URL", "http://localhost:8000")
    return httpx.Client(base_url=api_url, timeout=45.0)
