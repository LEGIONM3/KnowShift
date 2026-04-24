# KnowShift — 5-Minute Demo Script

## Pre-Demo Checklist (run 10 min before)

```bash
# Verify API is healthy and data is seeded
API_URL=https://your-api.onrender.com python scripts/verify_setup.py
# All 14 tests must pass ✅

# Keep tabs open:
#   Tab 1 — KnowShift frontend (Vercel URL or localhost:3000)
#   Tab 2 — Supabase Table Editor (chunks, change_log)
#   Tab 3 — This script
```

---

## THE SCRIPT

### MINUTE 1 — Hook (0:00–1:00)

> *"Every RAG system has a hidden time bomb."*

**Do:** Open the KnowShift frontend.

> *"When you ask a question, it answers based on whatever documents
> you fed it — months or years ago. Medical guidelines change.
> Tax laws change. AI regulations go from draft to legally binding.
> Most RAG systems have no idea. They confidently give you outdated,
> potentially dangerous answers.*
>
> *KnowShift is different. It knows when the world changed."*

**Do:** Click the **Medical** domain tab. Observe the animated ring.

---

### MINUTE 2 — The Problem (1:00–2:00)

> *"Let me show you the problem first."*

**Do:**
1. Toggle the mode button to **Include Stale**
2. Type (or click the demo hint): `What is the first-line treatment for Type 2 Diabetes?`
3. Click **Ask** — wait ~5 s

**Point to the answer:**

> *"It says Metformin is first-line. That was true — in 2021.
> Look at the freshness score: [point]. KnowShift is already warning us
> this answer comes from stale knowledge."*

---

### MINUTE 3 — The Solution (2:00–3:00)

> *"Now watch what happens when I switch to the fresh index."*

**Do:**
1. Toggle to **Fresh Index** mode
2. Ask the same question
3. Wait for the answer

**Point to the answer and freshness badge:**

> *"GLP-1 receptor agonists — semaglutide, tirzepatide — are now
> first-line for cardiovascular patients. That's the 2024 ADA update.
> [Point to freshness score] 90%+ confidence. The system retrieved
> the right document and ranked it correctly because it scored
> both semantic similarity AND temporal freshness."*

---

### MINUTE 4 — The Change Map (3:00–4:00)

> *"Now for the signature feature."*

**Do:**
1. Scroll to the **Change Map** section
2. The demo question is pre-filled
3. Click **Compare**
4. Wait ~10 s for both answers to load

**Walk through the three panels:**

> *"Left panel — old answer from the stale index: Metformin.
> Middle panel — what changed in the knowledge base.
> Right panel — new, healed answer: GLP-1 agonists.*
>
> *KnowShift didn't just find the right answer. It automatically
> deprecated the 2021 chunk when the 2024 document was uploaded.
> That is self-healing — no human intervention."*

**Point to the banner:**
> *"⚡ Knowledge difference detected — the self-healing index
> prevented outdated information from reaching the user."*

---

### MINUTE 5 — Live Self-Healing (4:00–5:00)

> *"Let me prove this works live."*

**Do:**
1. Go to the **Upload Panel** on the right sidebar
2. Drop any PDF (use `demo_data/medical_2024_guidelines.pdf`)
3. Type source name: `ADA 2025 Update`
4. Click **Upload & Heal**
5. Watch the result card appear

**Point to the stats:**

> *"X chunks indexed. Y old chunks deprecated. Self-healing triggered: YES.*
>
> *Every overlapping chunk from an older document was surgically removed
> from the index. The next query will automatically get the fresh answer.*
>
> *[Pause] KnowShift is not just self-correcting. It is self-healing."*

**Do:** Watch the Freshness Dashboard pie chart update.

> *"And here's the knowledge health score, live, after ingestion.*
> *That's KnowShift."*

---

## Backup Plans

| Problem               | Response                                              |
|-----------------------|-------------------------------------------------------|
| API is slow           | "Gemini free tier can be slow — here's a pre-recorded response" → open `demo_data/cached_responses.json` |
| API is down           | "Let me walk through the architecture" → show `docs/ARCHITECTURE.md` |
| Compare is slow       | "Both queries run in sequence — ~10 s" → wait it out |
| No stale diff visible | "Let me run a stale scan first" → click Run Stale Scan |

---

## Key Talking Points (use in Q&A)

- **Why not just re-index everything?** — "Selective re-indexing is O(new_chunks × existing_chunks) not O(corpus²). Faster and cheaper."
- **How does authority scoring work?** — "Keyword match on source_name for now; easily extensible to citation networks."
- **What about hallucinations?** — "Every answer is grounded in cited chunks with explicit freshness scores. Readers know when to verify."
- **Production readiness?** — "Change log gives full audit trail. Celery handles automated scans on a schedule."
