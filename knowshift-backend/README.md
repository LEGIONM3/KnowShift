# KnowShift Backend — Phase 1

> **Temporal Self-Healing RAG System** — domain-selectable knowledge retrieval with explicit freshness transparency.
> Built for the AMD Developer Hackathon.

---

## Architecture Overview

```
PDF Upload → Text Extraction → Chunking → Gemini Embeddings → Supabase pgvector
                                                                      ↓
User Query → Query Embedding → pgvector ANN Search → Temporal Reranking → Response
                                                                      ↓
Scheduled Sweep → Freshness Decay → Stale Detection → change_log Audit
```

---

## Project Structure

```
knowshift-backend/
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── config.py             # Pydantic settings (env vars)
│   ├── database.py           # Supabase client singleton
│   ├── routers/
│   │   ├── ingest.py         # POST /ingest/upload
│   │   ├── query.py          # POST /query/search
│   │   └── freshness.py      # POST /freshness/scan | GET /freshness/dashboard/{domain}
│   ├── services/
│   │   ├── chunker.py        # PDF parsing & RecursiveCharacterTextSplitter
│   │   ├── embedder.py       # Gemini text-embedding-004 (768-dim)
│   │   ├── retriever.py      # pgvector match_chunks() wrapper
│   │   ├── reranker.py       # Temporal reranking (similarity × 0.6 + freshness × 0.4)
│   │   └── freshness_engine.py  # Exponential decay, stale detection sweep
│   └── workers/
│       └── tasks.py          # Celery stubs (Phase 2)
├── supabase_schema.sql       # Complete DB schema + SQL functions
├── requirements.txt
├── Procfile                  # Render deployment
└── .env.example
```

---

## Setup Guide

### Step 1 — Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign in.
2. Click **New Project**, choose a name (e.g. `knowshift`), set a database password, pick a region close to you.
3. Wait for the project to provision (~2 minutes).

### Step 2 — Run the SQL Schema

1. In your Supabase dashboard, open **SQL Editor** → **New Query**.
2. Paste the entire contents of `supabase_schema.sql` and click **Run**.
3. You should see "Success. No rows returned." for each statement.
4. Optionally create the storage bucket via **Storage** → **New Bucket** → name it `documents` (private).

### Step 3 — Get Your API Keys

| Variable | Where to find it |
|---|---|
| `SUPABASE_URL` | Supabase Dashboard → Project Settings → **API** → Project URL |
| `SUPABASE_KEY` | Supabase Dashboard → Project Settings → **API** → `anon` public key (or `service_role` for backend) |
| `GEMINI_API_KEY` | [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

### Step 4 — Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your real values
```

### Step 5 — Install Dependencies

```bash
# Python 3.10+
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 6 — Run Locally

```bash
uvicorn app.main:app --reload --port 8000
```

---

## API Reference

### `GET /health`
Liveness probe.
```json
{"status": "ok", "environment": "development"}
```

### `POST /ingest/upload`
Upload and ingest a PDF document.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | PDF document |
| `domain` | string | ✅ | `medical` \| `finance` \| `ai_policy` |
| `source_name` | string | ✅ | Human-readable source label |
| `source_url` | string | ❌ | URL of original document |
| `published_at` | string | ❌ | ISO 8601 publication date |

```json
{"document_id": "uuid", "chunks_ingested": 42}
```

### `POST /query/search`
Semantic search with temporal reranking.
```json
{
  "query": "What are the latest FDA guidelines on mRNA vaccines?",
  "domain": "medical",
  "match_count": 10,
  "include_stale": false
}
```

### `POST /freshness/scan`
Trigger a full stale-detection sweep.
```json
{"newly_flagged": 3}
```

### `GET /freshness/dashboard/{domain}`
Per-domain freshness summary.
```json
{"domain": "medical", "total": 200, "fresh": 150, "aging": 30, "stale": 15, "deprecated": 5}
```

---

## Testing Checklist

### 1. Health endpoint
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","environment":"development"}
```

### 2. Interactive API docs
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### 3. Test PDF upload
```bash
curl -X POST http://localhost:8000/ingest/upload \
  -F "file=@/path/to/test.pdf" \
  -F "domain=ai_policy" \
  -F "source_name=Test Document"
# Expected: {"document_id":"...","chunks_ingested":N}
```

### 4. Verify data in Supabase
- **Table Editor** → `documents` — should show 1 row.
- **Table Editor** → `chunks` — should show N rows with non-null `embedding` vectors.

### 5. Test semantic search
```bash
curl -X POST http://localhost:8000/query/search \
  -H "Content-Type: application/json" \
  -d '{"query":"your question here","domain":"ai_policy","match_count":5}'
```

### 6. Run freshness scan
```bash
curl -X POST http://localhost:8000/freshness/scan
```

### 7. View dashboard
```bash
curl http://localhost:8000/freshness/dashboard/ai_policy
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `SUPABASE_URL` validation error | Missing `.env` file | Copy `.env.example` → `.env` and fill values |
| `429 Resource Exhausted` from Gemini | Free tier rate limit | Built-in retry; reduce upload frequency |
| `pgvector operator does not exist` | pgvector not enabled | Run `CREATE EXTENSION IF NOT EXISTS vector;` in SQL editor |
| `No text could be extracted` | Image-only PDF | Use a text-layer PDF or run OCR pre-processing |
| `Could not find the 'documents' bucket` | Storage bucket missing | Create it in Supabase Storage dashboard |

---

## Deployment (Render)

1. Push the `knowshift-backend/` directory to GitHub.
2. In Render: **New** → **Web Service** → connect repo.
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: *(auto-detected from Procfile)*
5. Add environment variables in Render's **Environment** tab.

---

## Phase 2 Roadmap

- [ ] Selective re-indexing via `find_overlapping_chunks()` SQL function
- [ ] Celery + Redis background task queue (replace stubs in `workers/tasks.py`)
- [ ] Gemini Flash generative answer synthesis with source citations
- [ ] React + Vite frontend with domain selector and freshness badges
- [ ] Automated periodic stale sweep via Celery Beat
- [ ] Webhook notifications for newly stale critical documents
