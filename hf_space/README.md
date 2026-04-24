---
title: KnowShift
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.19.2
app_file: app.py
pinned: true
license: mit
short_description: Temporal Self-Healing RAG System | AMD Hackathon 2025
tags:
  - RAG
  - temporal
  - self-healing
  - AMD
  - hackathon
  - gemini
  - supabase
  - pgvector
---

# KnowShift 🧠

**The RAG that knows when the world changed.**

Built for the **AMD Developer Hackathon 2025**.

## What is KnowShift?

KnowShift is a domain-selectable, self-healing RAG system that treats
**temporal validity** as a first-class retrieval signal alongside semantic
similarity.

## Three Core Innovations

### 1. Freshness as a First-Class Signal

| Signal       | Weight (Medical) | Weight (Finance) | Weight (AI Policy) |
|--------------|-----------------|-----------------|-------------------|
| Semantic     | 50%             | 50%             | 60%               |
| Freshness    | 40%             | 45%             | 30%               |
| Authority    | 10%             |  5%             | 10%               |

### 2. Chunk-Level Exponential Decay

```
freshness_score = exp(-λ × days_elapsed)
```

| Domain     | λ (decay rate) | Validity horizon |
|------------|---------------|-----------------|
| Medical    | 0.015         | ~180 days       |
| Finance    | 0.025         | ~90 days        |
| AI Policy  | 0.005         | ~365 days       |

### 3. Selective Re-Indexing (Self-Healing)

When new documents arrive, KnowShift:
1. Compares new chunk embeddings vs existing corpus (cosine >0.85)
2. Auto-deprecates overlapping stale chunks
3. Logs every event to `change_log` (full audit trail)
4. Next query automatically retrieves fresh information

**No full corpus rebuild required.**

## Demo Domains

| Domain     | Demo question                                              |
|------------|------------------------------------------------------------|
| Medical    | What is the first-line treatment for Type 2 Diabetes?     |
| Finance    | What is the tax rate for income between Rs 10–12 lakhs?   |
| AI Policy  | What obligations do high-risk AI system providers have?   |

## Tech Stack

- **Backend**: FastAPI + Python 3.11
- **Database**: Supabase (PostgreSQL + pgvector)
- **Embeddings**: Google Gemini `text-embedding-004` (768-dim)
- **LLM**: Gemini 1.5 Flash
- **Background Jobs**: Celery + Redis
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Deployment**: Render (API) + Vercel (React UI)
