# KnowShift Phase 2 — Testing Guide

Complete step-by-step verification for all Phase 2 features.

---

## Prerequisites

```bash
# 1. Activate virtual environment
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Ensure .env is populated (copy from .env.example and fill values)
cp .env.example .env

# 3. Start the API
uvicorn app.main:app --reload --port 8000

# 4. (Optional) Start Redis + Celery workers separately
#    In separate terminals:
redis-server
celery -A app.workers.tasks worker --loglevel=info
celery -A app.workers.tasks beat   --loglevel=info
```

---

## Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status": "ok", "environment": "development"}
```

---

## Test 2: Upload a PDF (Phase 1 + Phase 2 ingestion with self-healing)

```bash
curl -X POST http://localhost:8000/ingest/upload \
  -F "file=@/path/to/test.pdf" \
  -F "domain=ai_policy" \
  -F "source_name=EU AI Act 2024" \
  -F "source_url=https://example.com/eu-ai-act.pdf" \
  -F "published_at=2024-03-15T00:00:00"
```

**Expected (first upload — no overlaps yet):**
```json
{
  "document_id": "uuid-here",
  "chunks_ingested": 42,
  "deprecated_old_chunks": 0,
  "self_healing_triggered": false
}
```

**Expected (second upload of similar doc — self-healing kicks in):**
```json
{
  "document_id": "uuid-here",
  "chunks_ingested": 38,
  "deprecated_old_chunks": 15,
  "self_healing_triggered": true
}
```

---

## Test 3: RAG Query — `/query/ask`

```bash
curl -X POST http://localhost:8000/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the requirements for high-risk AI systems?",
    "domain": "ai_policy",
    "include_stale": false,
    "top_k": 5,
    "return_sources": true
  }'
```

**Expected:**
```json
{
  "answer": "According to [Source: EU AI Act 2024, Last verified: 2024-03-15]...",
  "freshness_confidence": 0.987,
  "staleness_warning": false,
  "sources": [
    {
      "source_name": "EU AI Act 2024",
      "last_verified": "2024-03-15T00:00:00",
      "freshness_score": 0.987,
      "chunk_preview": "High-risk AI systems must undergo conformity assessment..."
    }
  ],
  "ranking_conflicts": [],
  "processing_time_ms": 2340
}
```

**Checks:**
- `freshness_confidence >= 0.7` (document was just ingested)
- `staleness_warning == false`
- `sources` list is non-empty
- `answer` contains inline citations

---

## Test 4: Medical Domain Query

```bash
curl -X POST http://localhost:8000/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the first-line treatment for Type 2 Diabetes?",
    "domain": "medical",
    "include_stale": false,
    "top_k": 10
  }'
```

**Expected:**  Answer with medical citations, freshness_confidence reflecting 180-day medical horizon.

---

## Test 5: Stale vs Fresh Comparison — `/query/compare`

```bash
curl "http://localhost:8000/query/compare?question=What%20are%20the%20capital%20gains%20tax%20rates%3F&domain=finance&top_k=5"
```

**Expected:**
```json
{
  "question": "What are the capital gains tax rates?",
  "domain": "finance",
  "stale_answer": { ... },
  "fresh_answer": { ... },
  "difference_detected": true,
  "freshness_delta": 0.23
}
```

**Validation:** `difference_detected` will be `true` once you have a mix of stale and fresh docs.

---

## Test 6: Freshness Scan

```bash
curl -X POST http://localhost:8000/freshness/scan
```

**Expected:**
```json
{"newly_flagged": 0}
```

*(Will be > 0 after documents age past their validity_horizon)*

---

## Test 7: Domain Dashboard

```bash
curl http://localhost:8000/freshness/dashboard/ai_policy
```

**Expected:**
```json
{
  "domain": "ai_policy",
  "total": 42,
  "fresh": 40,
  "aging": 2,
  "stale": 0,
  "deprecated": 0
}
```

---

## Test 8: Change Log

```bash
curl "http://localhost:8000/freshness/change-log/ai_policy?limit=20"
```

**Expected:**
```json
{
  "domain": "ai_policy",
  "total_changes": 15,
  "changes": [
    {
      "id": "uuid",
      "chunk_id": "uuid",
      "document_id": "uuid",
      "change_type": "re-indexed",
      "reason": "Superseded by newer document...",
      "changed_at": "2024-04-24T...",
      "documents": {"source_name": "EU AI Act 2024", "domain": "ai_policy"}
    }
  ]
}
```

**Filter by change type:**
```bash
curl "http://localhost:8000/freshness/change-log/ai_policy?change_type=stale_flagged"
```

---

## Test 9: Re-Index Candidates

```bash
curl "http://localhost:8000/freshness/reindex-candidates/medical?staleness_threshold=0.5"
```

**Expected:**
```json
{
  "domain": "medical",
  "staleness_threshold": 0.5,
  "candidates_count": 2,
  "candidates": [
    {
      "document_id": "uuid",
      "source_name": "WHO Guidelines 2021",
      "last_verified": "2021-06-01T00:00:00",
      "avg_freshness": 0.12,
      "active_chunks": 28,
      "recommended_action": "Re-index with updated source document"
    }
  ]
}
```

---

## Test 10: Manual Re-Index Trigger

```bash
curl -X POST http://localhost:8000/freshness/trigger-reindex/YOUR-DOCUMENT-UUID
```

**Expected:**
```json
{
  "status": "Re-index queued",
  "document_id": "uuid",
  "source_name": "WHO Guidelines 2021"
}
```

---

## Test 11: Celery Background Tasks

### Start the worker
```bash
celery -A app.workers.tasks worker --loglevel=info
```

**Expected worker log:**
```
[tasks.scan_stale_documents] registered
[tasks.update_freshness_scores] registered
[tasks.generate_freshness_report] registered
```

### Trigger tasks manually (Python shell)
```python
from app.workers.tasks import scan_stale_documents, update_freshness_scores, generate_freshness_report

# Synchronous (dev testing — no broker needed)
scan_stale_documents()
update_freshness_scores("medical")
generate_freshness_report()

# Async via Celery (requires running worker + Redis)
scan_stale_documents.delay()
update_freshness_scores.delay("finance")
generate_freshness_report.delay()
```

---

## Test 12: Docker Compose (Full Stack)

```bash
# Build and start everything
docker compose up --build

# With Flower monitoring UI
docker compose --profile monitoring up --build

# API:    http://localhost:8000/docs
# Flower: http://localhost:5555
```

---

## Ranking Conflict Detection Verification

Upload an old document (set `published_at` to 2+ years ago), then query:

```bash
curl -X POST http://localhost:8000/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"...", "domain":"medical", "include_stale": true, "top_k": 10}'
```

If old chunks rank in the top results, you should see:
```json
{
  "ranking_conflicts": [
    {
      "chunk_id": "uuid",
      "semantic_similarity": 0.91,
      "freshness_score": 0.18,
      "reason": "High semantic relevance (0.91) but very stale (freshness=0.18)...",
      "suggested_action": "Flag for verification or re-indexing"
    }
  ]
}
```

---

## Common Issues & Fixes

| Error | Cause | Fix |
|---|---|---|
| `Connection refused` on Redis | Redis not running | `redis-server` or `docker compose up redis` |
| `celery: command not found` | Celery not in PATH | `pip install celery redis` in venv |
| `404` on `/query/ask` | Router prefix mismatch | Endpoint is `/query/ask` not `/ask` |
| `No relevant information found` | No docs in selected domain | Upload a PDF for that domain first |
| Embedding 429 rate limit | Gemini free tier | Built-in retry; reduce upload rate |
| `stale_flag` never True | Docs ingested just now | Manually set `last_verified` to 2+ years ago in Supabase table editor |
| Empty `ranking_conflicts` | No stale+relevant docs | Use `include_stale:true` with old docs |

---

## Render Deployment Guide

### 1. Create Redis Instance
- Render Dashboard → **New** → **Redis** (free tier)
- Copy the **Internal Redis URL**

### 2. Create Web Service (API)
- **New** → **Web Service** → connect GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: *(from Procfile — `web` process)*
- Environment variables:
  ```
  SUPABASE_URL      = your-url
  SUPABASE_KEY      = your-key
  GEMINI_API_KEY    = your-key
  REDIS_URL         = (paste internal Redis URL from step 1)
  ENVIRONMENT       = production
  ```

### 3. Create Worker Service
- **New** → **Background Worker** → same repo
- Start command: `celery -A app.workers.tasks worker --loglevel=info --concurrency=2`
- Same environment variables as the web service

### 4. Create Beat Service (optional — for automatic scheduling)
- **New** → **Background Worker** → same repo
- Start command: `celery -A app.workers.tasks beat --loglevel=info`
- Same environment variables

---

## Next Steps — Phase 3 (React Frontend)

- [ ] React + Vite frontend with domain selector tabs
- [ ] Knowledge freshness HUD with real-time score badges
- [ ] Change Map UI showing which chunks were deprecated
- [ ] Side-by-side Stale vs. Fresh comparison view
- [ ] Upload wizard with drag-and-drop PDF support
- [ ] Admin panel for manual re-index triggering
- [ ] Vercel deployment with API proxy to Render
