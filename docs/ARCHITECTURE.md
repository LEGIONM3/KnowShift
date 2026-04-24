# KnowShift — Architecture Reference

## System Overview

KnowShift is a temporal self-healing RAG system.
Standard RAG ranks retrieved chunks by **semantic similarity** alone.
KnowShift adds **freshness** and **authority** as retrieval signals.

---

## Component Map

```
┌─────────────────────────────────────────────────────────┐
│                  Browser (User)                          │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼─────────────────────────────────┐
│             React + Vite Frontend (Vercel)               │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │DomainSelector│  │  QueryPanel  │  │  ChangeMap   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────────────┐  ┌─────────────────────────┐  │
│  │  FreshnessDashboard  │  │      UploadPanel        │  │
│  └──────────────────────┘  └─────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ REST/JSON
┌───────────────────────▼─────────────────────────────────┐
│              FastAPI Backend (Render)                    │
│                                                         │
│  /ingest/upload ──► chunker ──► embedder ──► Supabase   │
│                         │                               │
│                         └──► selective_reindex()         │
│                                                         │
│  /query/ask   ──► embedder ──► retriever ──► reranker   │
│                                       └──► Gemini LLM   │
│                                                         │
│  /freshness/scan ──► freshness_engine ──► change_log    │
└──────┬────────────────────────────────┬─────────────────┘
       │                                │
┌──────▼──────┐                ┌────────▼──────────────────┐
│ Gemini API  │                │ Supabase (PostgreSQL)      │
│             │                │                           │
│ embedding-  │                │  documents                │
│ 004 768-dim │                │  chunks  (pgvector)       │
│             │                │  change_log               │
│ gemini-1.5  │                └───────────────────────────┘
│ -flash LLM  │
└─────────────┘
┌─────────────────────────────────────────────────────────┐
│       Celery + Redis (background jobs)                  │
│                                                         │
│  scan_stale_documents    every 24 h                     │
│  update_freshness_scores every  6 h                     │
│  generate_freshness_report weekly                       │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow: Document Ingestion

```
PDF file
  │
  ▼
LangChain RecursiveCharacterTextSplitter
  │  chunk_size=800, overlap=100
  │
  ▼
Gemini text-embedding-004 (768-dim)   ← rate limited: 1 s between calls
  │
  ▼
Supabase chunks table INSERT
  │
  ▼
selective_reindex()
  │
  ├─ For each new embedding:
  │     find_overlapping_chunks() RPC  ← cosine similarity > 0.85
  │     UPDATE chunks SET is_deprecated=True
  │     INSERT change_log (change_type='re-indexed')
  │
  └─ Return: { chunks_ingested, deprecated_old_chunks, self_healing_triggered }
```

---

## Data Flow: Query

```
User question
  │
  ▼
Gemini text-embedding-004 → 768-dim vector
  │
  ▼
match_chunks() RPC (pgvector KNN, top_k=10)
  │  optional: include_stale=False → filters stale-flagged docs
  │
  ▼
rerank_chunks()
  │  score = α×semantic + β×freshness + γ×authority
  │  domain-specific α/β/γ from DOMAIN_WEIGHTS dict
  │
  ▼
Top-5 chunks → context string
  │
  ▼
Gemini 1.5 Flash prompt:
  "You are a {domain_expert}. Answer using only the context below.
   Cite source name and verification date. Flag conflicts."
  │
  ▼
QueryResponse {
  answer, freshness_confidence, staleness_warning,
  sources[], ranking_conflicts[], processing_time_ms
}
```

---

## Database Schema

### documents
| Column        | Type        | Notes                                |
|---------------|-------------|--------------------------------------|
| id            | uuid PK     |                                      |
| domain        | text        | medical / finance / ai_policy        |
| source_name   | text        |                                      |
| source_url    | text        |                                      |
| published_at  | timestamptz |                                      |
| last_verified | timestamptz | Updated on re-ingestion              |
| stale_flag    | bool        | Set by freshness scanner             |
| created_at    | timestamptz |                                      |

### chunks
| Column          | Type        | Notes                              |
|-----------------|-------------|------------------------------------|
| id              | uuid PK     |                                    |
| document_id     | uuid FK     | → documents.id                     |
| chunk_text      | text        |                                    |
| embedding       | vector(768) | Gemini text-embedding-004          |
| freshness_score | float4      | exp(-λ × days); updated by Celery  |
| is_deprecated   | bool        | Set by selective_reindex()         |
| created_at      | timestamptz |                                    |

### change_log
| Column      | Type        | Notes                                    |
|-------------|-------------|------------------------------------------|
| id          | uuid PK     |                                          |
| document_id | uuid FK     |                                          |
| chunk_id    | uuid FK     | nullable (doc-level events)              |
| change_type | text        | deprecated / updated / re-indexed / stale_flagged |
| reason      | text        |                                          |
| old_value   | text        |                                          |
| new_value   | text        |                                          |
| changed_at  | timestamptz |                                          |

---

## Freshness Scoring

```
freshness_score = exp(-λ × days_elapsed)

where days_elapsed = (now - last_verified).days
```

| Score range | Category   | UI colour  |
|-------------|-----------|------------|
| ≥ 0.70      | Fresh     | 🟢 Green   |
| 0.40–0.69   | Aging     | 🟡 Yellow  |
| < 0.40      | Stale     | 🔴 Red     |
| deprecated  | —         | ⚫ Slate   |

---

## Reranking Weights

```python
DOMAIN_WEIGHTS = {
    "medical":   {"alpha": 0.5, "beta": 0.4,  "gamma": 0.1},
    "finance":   {"alpha": 0.5, "beta": 0.45, "gamma": 0.05},
    "ai_policy": {"alpha": 0.6, "beta": 0.3,  "gamma": 0.1},
}
```

`beta` (freshness weight) is highest for Finance because tax regulations
change frequently and using stale rates can cause legal liability.
