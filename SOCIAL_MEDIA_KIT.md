# KnowShift — Social Media Kit

Minimum requirement for the **Build in Public** bonus:
≥ 2 technical posts tagging **@lablab** and **@AIatAMD** (X/Twitter)
or **lablab.ai** and **AMD Developer** (LinkedIn).

---

## POST 1 — Project Announcement (Day 1)

### Twitter/X

```
🧠 Building KnowShift for the @AIatAMD Developer Hackathon

Problem: RAG systems have no idea when their knowledge goes stale.
They confidently give 2021 answers to 2025 questions.

Fix: Treat TIME as a first-class retrieval signal.

combined_score = α×semantic + β×freshness + γ×authority

Stack: FastAPI · Supabase pgvector · Gemini embeddings
→ Exponential freshness decay per domain
→ Selective self-healing re-indexing

Day 1: Supabase schema ✅ FastAPI scaffold ✅ Let's go 🚀

@lablab #AMDHackathon #BuildInPublic #RAG #AI
```

### LinkedIn

```
Excited to be building KnowShift for the AMD Developer Hackathon 2025!

The problem I'm solving: Standard RAG systems treat all retrieved chunks
as equally valid, regardless of when they were written.

A medical guideline from 2021 and one from 2024 get the same
"semantic match" score — but they might recommend completely different
treatments.

KnowShift's approach: temporal validity as a FIRST-CLASS retrieval signal.

Every chunk gets a freshness score:
  freshness = exp(-λ × days_elapsed)

Domain-specific decay rates:
  Medical   λ=0.015 → 180-day validity
  Finance   λ=0.025 → 90-day validity
  AI Policy λ=0.005 → 365-day validity

Day 1: Supabase schema with pgvector complete.
Embedding pipeline coming next.

#AMDHackathon #BuildInPublic #RAG #FastAPI #AI
Tags: lablab.ai | AMD Developer
```

---

## POST 2 — Technical Deep Dive (Day 2–3)

### Twitter/X

```
🔧 KnowShift update — the temporal reranking formula:

combined = α×semantic + β×freshness + γ×authority

Finance domain:  α=0.50, β=0.45 — staleness = legal risk
Medical domain:  α=0.50, β=0.40 — 2021 guidelines ≠ 2024 guidelines  
AI Policy:       α=0.60, β=0.30 — slower decay, but still matters

When a new PDF is uploaded, KnowShift:
1. Embeds all new chunks
2. Finds overlapping old chunks (cosine >0.85)
3. Auto-deprecates them
4. Logs to change_log (full audit trail)

Self-healing — no human intervention needed.

[screenshot of reranker.py]

@lablab @AIatAMD #AMDHackathon #BuildInPublic
```

---

## POST 3 — Demo Video (Day 4–5)

### Twitter/X

```
🎥 KnowShift live demo — the Change Map feature:

Ask: "First-line treatment for Type 2 Diabetes?"

⚠️ Stale index → "Metformin" (2021 ADA guideline)
✅ Fresh index → "GLP-1 agonists added" (2024 update)

KnowShift shows BOTH answers side-by-side, explains what changed,
and healed itself when the 2024 PDF was uploaded.

Self-healing RAG in action 👇

[video]

Try it: [Vercel URL]
Code:   [GitHub URL]
HF:     [Space URL]

@lablab @AIatAMD #AMDHackathon #BuildInPublic
```

---

## POST 4 — Ship Tweet (Final Day)

### Twitter/X

```
🚢 SHIPPED: KnowShift

The RAG that knows when the world changed.

✅ Temporal reranking (semantic + freshness + authority)
✅ Exponential per-domain freshness decay
✅ Three-panel Change Map UI (signature feature)
✅ Live document injection + self-healing
✅ Full change_log audit trail
✅ Celery background freshness scans

Built with: FastAPI · Supabase pgvector · Gemini · React · Celery

Demo:  [Vercel URL]
Code:  [GitHub URL]
Space: [HF URL]

@lablab @AIatAMD
#AMDHackathon #BuildInPublic #ShipIt #RAG
```

---

## AMD Developer Feedback (Required)

Document this in your submission:

### ROCm / AMD Instinct MI300X Experience

**What worked well:**
- [ ] List performance wins here

**Friction points / workarounds:**
- [ ] List any issues here

**Suggestions to the AMD team:**
- [ ] List improvements here

### AMD Developer Cloud

- Credit used: $_____ of $100
- GPU used: AMD Instinct MI300X
- Benchmark observations: _____
- Documentation gaps: _____
