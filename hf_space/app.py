"""
KnowShift — Hugging Face Gradio Space
Submission for AMD Developer Hackathon 2025.

Deploy:
  1. Create a new Space on huggingface.co/spaces
  2. SDK: Gradio | Python 3.11
  3. Set Secret KNOWSHIFT_API_URL → your Render backend URL
  4. Push this file as app.py
"""

import os

import gradio as gr
import requests

API_URL = os.getenv("KNOWSHIFT_API_URL", "http://localhost:8000")

DEMO_Q = {
    "medical":   "What is the first-line treatment for Type 2 Diabetes?",
    "finance":   "What is the tax rate for income between Rs 10-12 lakhs?",
    "ai_policy": "What obligations do high-risk AI system providers have?",
}


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _ask(question: str, domain: str, include_stale: bool):
    q = question.strip() or DEMO_Q.get(domain, "")
    try:
        r = requests.post(
            f"{API_URL}/query/ask",
            json={"question": q, "domain": domain,
                  "include_stale": include_stale, "return_sources": True},
            timeout=40,
        )
        if r.status_code != 200:
            return f"❌ API Error {r.status_code}", "N/A", "N/A", ""
        d = r.json()
    except Exception as exc:
        return f"❌ {exc}", "N/A", "N/A", ""

    score = d.get("freshness_confidence", 0)
    if score >= 0.7:
        freshness = f"✅ Fresh ({round(score*100)}%)"
    elif score >= 0.4:
        freshness = f"⏳ Aging ({round(score*100)}%)"
    else:
        freshness = f"⚠️ Stale ({round(score*100)}%)"

    staleness = (
        "⚠️ Warning: some sources may be outdated. Upload newer documents."
        if d.get("staleness_warning")
        else "✅ All sources are current"
    )

    sources_lines = []
    for s in d.get("sources", []):
        sources_lines.append(
            f"📄 {s.get('source_name','?')}\n"
            f"   Freshness: {round(s.get('freshness_score',0)*100)}%\n"
            f"   Verified:  {s.get('last_verified','?')}"
        )
    sources_text = "\n\n".join(sources_lines) or "No sources returned."

    return d.get("answer", "No answer generated"), freshness, staleness, sources_text


def _compare(question: str, domain: str):
    q = question.strip() or DEMO_Q.get(domain, "")
    try:
        r = requests.get(
            f"{API_URL}/query/compare",
            params={"question": q, "domain": domain},
            timeout=60,
        )
        if r.status_code != 200:
            return "Error", "Error", f"HTTP {r.status_code}"
        d = r.json()
    except Exception as exc:
        return f"Error: {exc}", f"Error: {exc}", "Comparison failed"

    stale = d.get("stale_answer", {}).get("answer", "N/A")
    fresh = d.get("fresh_answer", {}).get("answer", "N/A")
    diff  = (
        "⚡ Knowledge difference detected! Self-healing prevented outdated info."
        if d.get("difference_detected")
        else "✅ Both indexes are consistent."
    )
    return stale, fresh, diff


def _dashboard(domain: str) -> str:
    try:
        r = requests.get(f"{API_URL}/freshness/dashboard/{domain}", timeout=10)
        if r.status_code != 200:
            return "Dashboard unavailable"
        d = r.json()
    except Exception as exc:
        return f"Error: {exc}"

    total = d.get("total", 0)
    if not total:
        return "No data — upload documents first."

    health = round((d.get("fresh", 0) / total) * 100)
    return (
        f"📊 Knowledge Health: {health}%\n\n"
        f"✅ Fresh:      {d.get('fresh', 0)}\n"
        f"⏳ Aging:      {d.get('aging', 0)}\n"
        f"⚠️  Stale:     {d.get('stale', 0)}\n"
        f"🗑️  Deprecated: {d.get('deprecated', 0)}\n"
        f"📦 Total:      {total}"
    )


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

THEME = gr.themes.Soft(primary_hue="blue", secondary_hue="slate")

with gr.Blocks(title="KnowShift — Temporal Self-Healing RAG", theme=THEME) as demo:

    gr.Markdown("""
# 🧠 KnowShift
### Temporal Self-Healing RAG System
> **AMD Developer Hackathon 2025** · Powered by AMD Instinct MI300X

KnowShift treats temporal validity as a first-class retrieval signal.
It detects stale knowledge, repairs its own index, and delivers answers
with explicit freshness transparency.
""")

    domain_dd = gr.Dropdown(
        choices=["medical", "finance", "ai_policy"],
        value="medical",
        label="Domain",
        info="Medical (180d) | Finance (90d) | AI Policy (365d)",
    )

    with gr.Tabs():

        # ── Query ──────────────────────────────────────────────────────────
        with gr.TabItem("🔍 Query"):
            q_input  = gr.Textbox(label="Question", lines=3,
                                  placeholder="Or leave blank to use demo question…")
            stale_cb = gr.Checkbox(label="Include stale documents", value=False)
            ask_btn  = gr.Button("Ask KnowShift", variant="primary")

            answer_out   = gr.Textbox(label="Answer", lines=8, interactive=False)
            freshness_out= gr.Textbox(label="Freshness", interactive=False)
            staleness_out= gr.Textbox(label="Staleness Warning", interactive=False)
            sources_out  = gr.Textbox(label="Sources", lines=6, interactive=False)

            ask_btn.click(
                _ask,
                [q_input, domain_dd, stale_cb],
                [answer_out, freshness_out, staleness_out, sources_out],
            )

        # ── Change Map ─────────────────────────────────────────────────────
        with gr.TabItem("🗺️ Change Map"):
            gr.Markdown("""
### Signature Feature — Side-by-Side Comparison
See what the AI would have said with stale knowledge
versus what it says now with the fresh, healed index.
""")
            cmp_q   = gr.Textbox(label="Question (blank = demo question)", lines=2)
            cmp_btn = gr.Button("Run Comparison", variant="primary")

            with gr.Row():
                stale_out = gr.Textbox(label="⚠️ Old Answer (Stale)", lines=8, interactive=False)
                fresh_out = gr.Textbox(label="✅ New Answer (Fresh)", lines=8, interactive=False)

            diff_out = gr.Textbox(label="Difference Analysis", interactive=False)

            cmp_btn.click(_compare, [cmp_q, domain_dd], [stale_out, fresh_out, diff_out])

        # ── Dashboard ──────────────────────────────────────────────────────
        with gr.TabItem("📊 Dashboard"):
            gr.Markdown("### Knowledge Health Monitor")
            refresh_btn   = gr.Button("Refresh", variant="secondary")
            dashboard_out = gr.Textbox(label="Health Status", lines=10, interactive=False)
            refresh_btn.click(_dashboard, [domain_dd], [dashboard_out])

    gr.Markdown("""
---
**KnowShift** · AMD Developer Hackathon 2025 ·
[GitHub](https://github.com/yourusername/knowshift) ·
[lablab.ai](https://lablab.ai)

Three core innovations:
1. **Freshness as a retrieval signal** — not just semantic similarity
2. **Exponential chunk-level decay** — per-domain validity horizons
3. **Selective re-indexing** — surgical self-healing, no full rebuild
""")

if __name__ == "__main__":
    demo.launch()
