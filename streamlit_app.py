#!/usr/bin/env python3
"""noul GUI — Streamlit interface for non-technical users.

Usage:
  pip install streamlit
  streamlit run streamlit_app.py

Requires a running engine (Kev-0.8B running at http://127.0.0.1:8009)."""
import os
import sys

# Ensure noul is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from noul import ENGINES, load_pack, batch_decide, ordinal_tier

st.set_page_config(page_title="noul — local abstention gate", page_icon="🧭", layout="centered")

# Header
st.title("🧭 noul — the local abstention gate")
st.markdown(
    "Tell your RAG when the docs *don't* have the answer. "
    "Zero network calls. Zero labels required to start."
)

# Sidebar info
st.sidebar.title("About")
st.sidebar.markdown(
    "**Engine status**: only the running engine can answer. "
    "Run `python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009` to start Kev."
)
st.sidebar.markdown("**Built for local RAG** — before your LLM generates, ask noul: should I trust this answer?")

# Single check form
st.subheader("Single check")

doc_text = st.text_area("Context (the docs):", height=200,
                        placeholder="Paste the text your RAG retrieved...")
question_text = st.text_input("Question:", placeholder="What is the budget?")

engine_choice = st.selectbox("Engine:", list(ENGINES.keys()), index=0,
                             help="kev = calibrated gate (ECE 0.089). deepopen = production Laya engine.")
ordinal_check = st.checkbox("Show ordinal tier (definite_yes / maybe / definite_no)")

def run_single_check(doc: str, question: str, engine: str, ordinal: bool):
    import urllib.request
    import json
    import time
    from noul.engine import decide
    pack = load_pack("answerability")
    qname, q = next(iter(pack["questions"].items()))
    instructions = f"{q['instructions']} Question: {question}"
    try:
        resp = decide(doc, {qname: {"type": "noul", "instructions": instructions}}, engine=engine)
        ans = resp["answers"][qname]
        noul = ans.get("noul", 0.0)
        label = q["label_true"] if noul >= 0.5 else q["label_false"]
        tier = ordinal_tier(noul) if ordinal else None
        return {
            "verdict": label,
            "noul": round(noul, 3),
            "tier": tier,
            "engine": engine,
            "latency_ms": resp["_noul_latency_ms"],
            "error": None,
        }
    except Exception as e:
        return {"verdict": "ERROR", "noul": 0.0, "tier": None, "engine": engine,
                "latency_ms": 0.0, "error": str(e)}

if st.button("Check answerability", type="primary", disabled=not (doc_text and question_text)):
    with st.spinner(f"Asking engine '{engine_choice}'..."):
        result = run_single_check(doc_text, question_text, engine_choice, ordinal_check)
    if result.get("error"):
        st.error(f"Engine '{engine_choice}' unreachable: {result['error']}")
        st.info("Make sure the server is running: `python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009`")
    else:
        # Color-coded result
        if result["verdict"] == "ANSWERABLE":
            st.success(f"✅ ANSWERABLE — noul = {result['noul']:.3f}  ({result['latency_ms']:.1f} ms)")
        elif result["verdict"] == "NOT_ANSWERABLE":
            st.warning(f"❌ NOT ANSWERABLE — noul = {result['noul']:.3f}  ({result['latency_ms']:.1f} ms)")
        else:
            st.info(f"{result['verdict']} — noul = {result['noul']:.3f}  ({result['latency_ms']:.1f} ms)")
        if ordinal_check:
            tier = result.get("tier")
            if tier == "definite_yes":
                st.success(f"Tier: {tier}")
            elif tier == "definite_no":
                st.error(f"Tier: {tier}")
            elif tier == "maybe":
                st.warning(f"Tier: {tier}")

# Batch section
st.subheader("Batch check (multiple questions)")
st.markdown("Upload a CSV with columns: `question` (required), `context` (optional).")

batch_file = st.file_uploader("Batch file (.csv, .jsonl)", type=["csv", "jsonl"],
                              help="CSV needs a 'question' column. JSONL: each line {\"question\": \"...\"}")

batch_engine = st.selectbox("Batch engine:", list(ENGINES.keys()), index=0, key="batch_engine")
batch_ordinal = st.checkbox("Show ordinal tiers for batch", key="batch_ordinal")

if batch_file is not None:
    try:
        from noul.batch import load_batch_input, save_batch_results
        # Read file content
        content = batch_file.read()
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            f.write(content)
            tmp_path = f.name
        items = load_batch_input(tmp_path)
        batch_doc_text = st.text_area("Shared context for batch (optional):", height=100,
                                      placeholder="Leave empty if each row has 'context' column.")
        if st.button("Run batch check", disabled=not items):
            with st.spinner(f"Running {len(items)} checks on engine '{batch_engine}'..."):
                # Use shared doc if no per-row context
                if batch_doc_text:
                    for item in items:
                        item.setdefault("context", batch_doc_text)
                else:
                    # Ensure each item has context; if not, use shared doc (even if empty)
                    for item in items:
                        item.setdefault("context", "")
                results = batch_decide(
                    [{"question": item.get("question", ""),
                      "context": item.get("context", batch_doc_text or ""),
                      "id": item.get("id", i)}
                     for i, item in enumerate(items)],
                    doc=batch_doc_text or "",
                    pack="answerability",
                    engine=batch_engine,
                    ordinal=batch_ordinal,
                )
            # Show results
            st.subheader("Results")
            for r in results:
                if "error" in r:
                    st.error(f"Item {r.get('index', '?')}: {r['error']}")
                else:
                    verdict = r.get("verdict", "?")
                    if verdict == "ANSWERABLE":
                        st.success(f"✅ {verdict} — noul={r['noul']:.3f}  {r.get('question', '')[:60]}")
                    else:
                        st.warning(f"❌ {verdict} — noul={r['noul']:.3f}  {r.get('question', '')[:60]}")
                    if r.get("tier"):
                        st.caption(f"Tier: {r['tier']}")
    except Exception as e:
        st.error(f"Batch load error: {str(e)}")

# Footer
st.divider()
st.markdown(
    f"Built with `noul` v0.1 — engine: **{engine_choice}**, pack: `answerability`. "
    "See `README.md` for the full CLI reference."
)
