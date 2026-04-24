# KnowShift — Phase 4 Setup Complete ✅

## Everything that was built

### Phase 1 — Foundation
- Supabase schema (documents / chunks / change_log + pgvector functions)
- FastAPI scaffold with config, database client, settings
- Gemini `text-embedding-004` integration
- PDF → chunk → embed → store ingestion pipeline
- Exponential freshness decay engine

### Phase 2 — Core RAG Pipeline
- pgvector semantic retrieval (`match_chunks` RPC)
- Temporal reranking engine (`α×semantic + β×freshness + γ×authority`)
- `/query/ask` and `/query/compare` endpoints
- Selective re-indexing (`find_overlapping_chunks` RPC → auto-deprecation)
- Full `change_log` audit trail
- Celery + Redis background jobs (daily scan, 6-hour freshness updates)

### Phase 3 — React Frontend
- Vite + React 18 + Tailwind CSS project
- DomainSelector, QueryPanel, ChangeMap (3-panel), FreshnessDashboard, UploadPanel
- Recharts donut chart, Framer Motion animations
- Custom hooks: `useQuery`, `useDashboard`, `useChangeLog`
- Shared components: `FreshnessTag`, `ConfidenceBar`, `ErrorBanner`

### Phase 4 — Integration & Deployment
- `app/main.py` — startup verification, CORS, timing middleware, error handler
- `scripts/generate_test_pdfs.py` — 6 realistic domain PDFs via reportlab
- `scripts/seed_demo_data.py` — automated upload of all demo PDFs
- `scripts/backdate_documents.py` — simulate document aging (400–600 days)
- `scripts/verify_setup.py` — 14-test pre-demo verification suite
- `render.yaml` — Render deployment for API + worker + beat + Redis
- `hf_space/` — Gradio HF Space with Query, Change Map, Dashboard tabs
- `tests/` — conftest, endpoint tests, freshness unit tests, E2E tests
- `docs/ARCHITECTURE.md` — full system diagrams and data flow
- `docs/API_REFERENCE.md` — complete endpoint reference
- `README.md` — project overview with quick start
- `DEMO_SCRIPT.md` — 5-minute timed demo walkthrough
- `SOCIAL_MEDIA_KIT.md` — 4 ready-to-post Build in Public updates

---

## Final Deployment Checklist

### Backend → Render
```bash
# 1. Push to GitHub
git add -A && git commit -m "feat: KnowShift Phase 4 complete"
git push origin main

# 2. Render dashboard → New Blueprint → connect repo
#    render.yaml provisions: API + worker + beat + Redis

# 3. Set environment variables in Render:
#    SUPABASE_URL=...
#    SUPABASE_KEY=...
#    GEMINI_API_KEY=...

# 4. Wait for deploy (~3 min), verify:
curl https://knowshift-api.onrender.com/health
```

### Seed Production Data
```bash
API_URL=https://knowshift-api.onrender.com python scripts/generate_test_pdfs.py
API_URL=https://knowshift-api.onrender.com python scripts/seed_demo_data.py
API_URL=https://knowshift-api.onrender.com python scripts/backdate_documents.py
API_URL=https://knowshift-api.onrender.com python scripts/verify_setup.py
```

### Frontend → Vercel
```bash
cd knowshift-frontend
# Edit .env.production → VITE_API_URL=https://knowshift-api.onrender.com
npm i -g vercel
vercel              # first deploy
# Set VITE_API_URL in Vercel dashboard
vercel --prod       # production deploy
```

### HF Space
```bash
# Create new Gradio Space on huggingface.co/spaces
# Upload hf_space/ contents as app.py + requirements.txt + README.md
# Add Secret: KNOWSHIFT_API_URL=https://knowshift-api.onrender.com
```

### Run Tests
```bash
cd knowshift-backend
API_URL=https://knowshift-api.onrender.com pytest tests/ -v
# Should pass all tests
```

---

## Demo Day Sequence

```
1. python scripts/verify_setup.py      # all 14 tests green
2. Open browser → Vercel URL
3. Follow DEMO_SCRIPT.md exactly (5 min)
4. Q&A: use docs/ARCHITECTURE.md for deep dives
5. Publish final ship tweet from SOCIAL_MEDIA_KIT.md
```

---

## Post-Hackathon Roadmap

| Feature                            | Priority |
|------------------------------------|----------|
| WebSocket live freshness updates   | High     |
| Authority scoring via citation API | Medium   |
| Admin panel + re-index queue UI    | Medium   |
| Multi-domain comparison view       | Low      |
| Playwright E2E browser tests       | Low      |
| Redis response caching             | Low      |
