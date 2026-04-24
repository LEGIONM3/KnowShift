# KnowShift — Phase 5 Testing Guide

> **Status:** ✅ Complete — 60+ backend tests | 35+ frontend tests | CI/CD pipelines

---

## Test Architecture

```
Project/
├── run_tests.ps1                        ← Windows runner (all modes)
├── run_tests.sh                         ← Linux/macOS runner
├── .github/workflows/
│   ├── test.yml                         ← CI: unit + integration + frontend
│   └── e2e.yml                          ← E2E/perf on dispatch or daily cron
│
├── knowshift-backend/
│   ├── pytest.ini                       ← markers, coverage config
│   └── tests/
│       ├── conftest.py                  ← ALL shared fixtures
│       ├── fixtures/
│       │   ├── sample_documents.py      ← realistic domain text
│       │   └── mock_responses.py        ← pre-built API response dicts
│       │
│       ├── unit/                        ← Pure offline tests
│       │   ├── test_freshness_engine.py (24 tests)
│       │   ├── test_chunker.py          (11 tests)
│       │   ├── test_embedder.py          (7 tests)
│       │   ├── test_reranker.py         (18 tests)
│       │   └── test_retriever.py         (7 tests)
│       │
│       ├── integration/                 ← FastAPI TestClient (mocked deps)
│       │   ├── test_ingest_router.py    (6 tests)
│       │   ├── test_query_router.py    (13 tests)
│       │   └── test_freshness_router.py (12 tests)
│       │
│       ├── e2e/                         ← Live HTTP (requires running API)
│       │   ├── test_full_pipeline.py   (17 tests)
│       │   └── test_self_healing.py    (12 tests)
│       │
│       ├── performance/                 ← Latency/throughput
│       │   ├── test_query_latency.py    (6 benchmarks)
│       │   └── test_ingestion_throughput.py (3 benchmarks)
│       │
│       └── demo/
│           └── test_demo_scenarios.py  (12 tests — run before demo!)
│
└── knowshift-frontend/
    └── src/__tests__/
        ├── setup.js                     ← jest-dom matchers
        ├── api/knowshiftApi.test.js      (9 tests)
        ├── utils/freshness.test.js      (30 tests)
        └── components/
            ├── FreshnessTag.test.jsx    (20 tests)
            └── QueryPanel.test.jsx      (15 tests)
```

---

## Quick Start

```powershell
# Install backend deps
cd knowshift-backend
pip install -r requirements.txt

# Install frontend deps
cd ..\knowshift-frontend
npm install
```

---

## Running Tests (Windows PowerShell)

```powershell
# Default (unit + integration — no live API needed)
.\run_tests.ps1

# Individual suites
.\run_tests.ps1 unit          # Pure offline unit tests
.\run_tests.ps1 integration   # FastAPI TestClient (mocked Supabase/Gemini)
.\run_tests.ps1 frontend      # Vitest component + utility tests
.\run_tests.ps1 coverage      # Unit + integration + HTML coverage report

# Live-API suites (start backend first: uvicorn app.main:app --reload)
$env:TEST_API_URL = "http://localhost:8000"
.\run_tests.ps1 all           # unit + integration + e2e
.\run_tests.ps1 demo          # demo validation (mirrors DEMO_SCRIPT.md)
.\run_tests.ps1 perf          # latency benchmarks
```

---

## Pytest Markers

| Marker | Description | Requires live API |
|--------|-------------|:-----------------:|
| `unit` | Pure Python, no I/O | No |
| `integration` | FastAPI TestClient, mocked DB | No |
| `e2e` | Real HTTP to live API | Yes |
| `performance` | Latency benchmarks | Yes |
| `demo` | Pre-demo readiness gate | Yes |
| `slow` | Tests > 5 seconds | varies |

---

## Pre-Demo Checklist

Run this **every time** before the hackathon presentation:

```powershell
cd knowshift-backend

# 1. Seed demo data (once per environment)
python scripts/seed_demo_data.py

# 2. Create temporal contrast
python scripts/backdate_documents.py

# 3. Run demo master gate
$env:TEST_API_URL = "https://your-api.onrender.com"
python -m pytest tests/demo/test_demo_scenarios.py::TestMasterDemoGate -v -s
```

A passing gate prints:
```
DEMO READINESS CHECK:
   ok api_health
   ok medical_has_data
   ok finance_has_data
   ok ai_policy_has_data
   ok query_works
   ok compare_works
```

---

## CI/CD Pipelines

### `test.yml` — Runs on every push/PR to `main`

| Job | Runs |
|-----|------|
| `backend-tests` | `unit` + `integration` (mocked, no credentials) |
| `frontend-tests` | Vitest + Vite build check |
| `code-quality` | black + isort + flake8 |
| `test-gate` | Blocks merge if any required job fails |

### `e2e.yml` — Manual dispatch or daily cron (05:00 UTC)

- Accepts `api_url` and `environment` inputs
- Runs `e2e` + `demo` + `performance` suites against live API
- Waits up to 2 minutes for API health before starting

---

## Performance Targets

| Endpoint | P95 Target |
|----------|:----------:|
| `GET /health` | < 200 ms |
| `GET /freshness/dashboard/{domain}` | < 2 s |
| `POST /query/ask` | < 12 s |
| `POST /ingest/upload` | < 120 s |

---

## Coverage

Target: **≥ 60%** line coverage on `app/` (enforced in `pytest.ini --cov-fail-under=60`).

```powershell
.\run_tests.ps1 coverage
# Open: knowshift-backend\coverage_report\index.html
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: app` | Run pytest from `knowshift-backend/` |
| `SUPABASE_URL not set` | conftest.py auto-sets test env vars |
| E2E: API not ready | Start: `uvicorn app.main:app --reload` |
| Demo: `X has no data` | Run `python scripts/seed_demo_data.py` |
| Demo: fresh ≈ stale score | Run `python scripts/backdate_documents.py` |
| Vitest packages missing | Run `npm install` in `knowshift-frontend/` |
