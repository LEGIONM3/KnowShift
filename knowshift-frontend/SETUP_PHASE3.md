# KnowShift Phase 3 — Frontend Setup Guide

React + Vite + Tailwind CSS frontend for the KnowShift Temporal Self-Healing RAG system.

---

## Quick Start

```bash
# 1. Enter the frontend directory
cd knowshift-frontend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.local.example .env.local   # already provided as .env.local

# 4. Start the dev server (make sure backend is running on :8000)
npm run dev

# App opens at: http://localhost:3000
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Node.js | >= 18 |
| npm | >= 9 |
| KnowShift backend | Running on http://localhost:8000 |

---

## Project Structure

```
knowshift-frontend/
├── src/
│   ├── api/              # Axios API layer
│   ├── components/
│   │   ├── changemap/    # 3-panel Change Map (signature feature)
│   │   ├── dashboard/    # Freshness Dashboard + Recharts pie chart
│   │   ├── domain/       # Domain selector tabs
│   │   ├── layout/       # Header, LoadingSpinner
│   │   ├── query/        # QueryPanel + SourceCard
│   │   ├── shared/       # FreshnessTag, ConfidenceBar, ErrorBanner, EmptyState
│   │   └── upload/       # UploadPanel with drag-and-drop
│   ├── hooks/            # useQuery, useDashboard, useChangeLog
│   ├── pages/            # HomePage
│   ├── utils/            # freshness.js, formatting.js
│   ├── App.jsx
│   └── main.jsx
├── .env.local            # Local API URL
├── .env.production       # Production API URL
├── vercel.json           # Vercel SPA rewrite rules
└── tailwind.config.js
```

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `VITE_API_URL` | FastAPI backend base URL | `http://localhost:8000` |
| `VITE_APP_NAME` | App display name | `KnowShift` |
| `VITE_APP_VERSION` | Semver string | `1.0.0` |

---

## Component Checklist

Run the app and verify each item:

| Component | ID / Selector | What to check |
|---|---|---|
| DomainSelector | `#domain-tab-medical` | Click tabs, animated ring moves |
| QueryPanel | `#query-submit` | Submit question, answer renders with FreshnessTag |
| ConfidenceBar | Progress bar | Width animates to correct % |
| ChangeMap | `#changemap-compare` | 3 panels render, difference banner shows |
| FreshnessDashboard | `#run-stale-scan` | Donut chart renders, health score updates |
| UploadPanel | `#upload-submit` | Drag PDF, fill source name, upload succeeds |
| Header | API status dot | Green dot with pulse when backend is online |

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `CORS error` on API calls | Backend not running | Start FastAPI: `uvicorn app.main:app --reload --port 8000` |
| Blank page on first load | Tailwind JIT not compiled | Run `npm run dev` (not open index.html directly) |
| Vite proxy 502 | Wrong port in vite.config.js | Confirm backend runs on :8000 |
| `Cannot find module 'framer-motion'` | deps not installed | `npm install` |
| Chart doesn't render | No data for domain | Upload a PDF first to populate chunks |
| `freshness_confidence` is 0 | No chunks found | Check domain filter matches uploaded docs |

---

## Vercel Deployment

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Deploy
vercel

# 3. Set environment variables in Vercel dashboard:
#    VITE_API_URL = https://your-knowshift-api.onrender.com

# 4. Redeploy after setting env vars
vercel --prod
```

> **Note**: Update `.env.production` with your Render API URL before building.

---

## API Proxy (Development)

The Vite proxy in `vite.config.js` forwards `/api/*` → `http://localhost:8000`.
All `api.*()` calls in `knowshiftApi.js` use the `VITE_API_URL` base directly
(not the `/api` prefix), so the proxy is only used if you change the import to use `/api`.

---

## Build for Production

```bash
npm run build
# Output in dist/ — deploy to Vercel, Netlify, or any static host
```

---

## Phase 4 Preview

- [ ] Admin panel: re-index queue management
- [ ] Live WebSocket freshness updates
- [ ] Multi-domain comparison view
- [ ] Document timeline visualisation
- [ ] Integration tests with Playwright
