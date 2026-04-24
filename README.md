# 🧠 KnowShift

### Temporal Self-Healing RAG System

> **AMD Developer Hackathon 2025** — Track 1: AI Agents & Agentic Workflows

[![API](https://img.shields.io/badge/API-Render-green)](https://knowshift-api.onrender.com)
[![Demo](https://img.shields.io/badge/Live_Demo-Vercel-black)](https://knowshift.vercel.app)
[![HF Space](https://img.shields.io/badge/HuggingFace-Space-yellow)](https://huggingface.co/spaces/yourusername/knowshift)
[![AMD](https://img.shields.io/badge/Powered_by-AMD_MI300X-red)](https://developer.amd.com)

---

## What is KnowShift?

KnowShift is a domain-selectable, self-healing RAG system that:

- **Detects** when its knowledge becomes stale
- **Repairs** its own index (selective re-indexing)
- **Shows** users explicit freshness transparency for every answer

Unlike standard RAG in which all retrieved chunks are treated equally,
KnowShift treats **temporal validity** as a first-class retrieval signal
alongside semantic similarity.

---

## Three Core Innovations

### 1. Freshness as a Retrieval Signal

```
combined_score = α × semantic + β × freshness + γ × authority
```

| Domain     | α (semantic) | β (freshness) | γ (authority) |
|------------|-------------|--------------|--------------|
| Medical    | 0.50        | **0.40**     | 0.10         |
| Finance    | 0.50        | **0.45**     | 0.05         |
| AI Policy  | 0.60        | 0.30         | 0.10         |

### 2. Exponential Chunk-Level Decay

Every chunk carries a freshness score:

```python
freshness_score = exp(-λ × days_elapsed)
```

| Domain     | λ (decay rate) | ~Validity horizon |
|------------|---------------|-------------------|
| Medical    | 0.015         | 180 days          |
| Finance    | 0.025         | 90 days           |
| AI Policy  | 0.005         | 365 days          |

### 3. Selective Re-Indexing (Self-Healing)

When new documents arrive:

1. New chunk embeddings compared vs existing corpus (cosine > 0.85)
2. Overlapping stale chunks **automatically deprecated**
3. Every event logged to `change_log` (full audit trail)
4. Next query retrieves fresh information — **no human intervention required**

---

## Architecture

```
┌──────────────────────────────────────────────┐
│           React + Vite (Vercel)               │
│  DomainSelector  QueryPanel  ChangeMap        │
│  FreshnessDashboard  UploadPanel              │
└─────────────────┬────────────────────────────┘
                  │ HTTP/REST
┌─────────────────▼────────────────────────────┐
│           FastAPI (Render)                    │
│  /ingest  /query/ask  /query/compare          │
│  /freshness/scan  /freshness/dashboard/{d}    │
└────────┬──────────────────────┬──────────────┘
         │                      │
┌────────▼──────┐   ┌───────────▼──────────────┐
│  Gemini API   │   │  Supabase PostgreSQL       │
│  embedding-04 │   │  + pgvector                │
│  gemini-flash │   │  documents / chunks /      │
└───────────────┘   │  change_log                │
                    └──────────────────────────┘
┌────────────────────────────────────────────┐
│  Celery + Redis                            │
│  Periodic stale scans  Freshness updates   │
└────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

| Tool      | Version |
|-----------|---------|
| Python    | 3.11+   |
| Node.js   | 18+     |
| Supabase  | Free account |
| Gemini    | Free API key |

### 1. Backend

```bash
cd knowshift-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# → edit SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY

uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

### 2. Seed Demo Data

```bash
# Generate PDFs
python scripts/generate_test_pdfs.py

# Upload to API
python scripts/seed_demo_data.py

# Backdate old documents (creates stale contrast)
python scripts/backdate_documents.py

# Verify everything
python scripts/verify_setup.py
```

### 3. Frontend

```bash
cd knowshift-frontend
npm install
# edit .env.local → VITE_API_URL=http://localhost:8000
npm run dev
# → http://localhost:3000
```

---

## API Reference

```
POST /query/ask          RAG query with freshness scoring
GET  /query/compare      Stale vs fresh side-by-side
POST /ingest/upload      PDF document ingestion
POST /freshness/scan     Trigger stale detection sweep
GET  /freshness/dashboard/{domain}
GET  /freshness/change-log/{domain}
GET  /health             Component health check
GET  /stats              System-wide counts
```

---

## Demo Questions

| Domain     | Stale answer (2021)            | Fresh answer (2024)                  |
|------------|-------------------------------|--------------------------------------|
| Medical    | Metformin first-line           | GLP-1 agonists elevated to first-line|
| Finance    | 20% tax on Rs 10–12L           | 15% tax on Rs 10–12L (budget 2024)  |
| AI Policy  | Draft obligations (no deadline)| Legally binding + August 2025/2026  |

---

## Deployment

### Backend → Render

```bash
# Uses render.yaml — just connect GitHub repo
# Set env vars in Render dashboard:
#   SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY
```

### Frontend → Vercel

```bash
vercel
# Set VITE_API_URL=https://knowshift-api.onrender.com
vercel --prod
```

### HF Space

```bash
# Push hf_space/ contents to a new Gradio Space
# Set Secret: KNOWSHIFT_API_URL
```

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | React 18 + Vite + Tailwind CSS      |
| Charts      | Recharts + Framer Motion            |
| Backend     | FastAPI + Python 3.11               |
| Database    | Supabase (PostgreSQL + pgvector)    |
| Embeddings  | Gemini `text-embedding-004` 768-dim |
| LLM         | Gemini 1.5 Flash                    |
| Background  | Celery + Redis                      |
| Deploy API  | Render (free tier)                  |
| Deploy UI   | Vercel (free tier)                  |
| HF Space    | Gradio 4.x                         |

---

## License

MIT — see [LICENSE](LICENSE)
