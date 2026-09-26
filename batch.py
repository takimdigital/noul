"""noul batch processing + ordinal confidence tiers. stdlib-only."""
from __future__ import annotations

import csv
import io
import json
import os
import sys
from typing import Optional

from .engine import decide
from .pack import load_pack, _first_noul_question


def ordinal_tier(noul: float) -> str:
    """Map a noul probability to an ordinal confidence tier.

    definite_yes  noul >= 0.90   — docs clearly support the answer
    maybe         0.50 <= noul < 0.90 — uncertain — ask a human
    definite_no   noul < 0.50    — docs do not support the answer
    """
    if noul >= 0.90:
        return "definite_yes"
    elif noul >= 0.50:
        return "maybe"
    else:
        return "definite_no"


def batch_decide(
    items: list[dict],
    doc: str = "",
    pack: str = "answerability",
    engine: str = "kev",
    ordinal: bool = False,
) -> list[dict]:
    """Run noul check on a list of (question, context) pairs.

    Each item may have keys: 'question' (required), 'context' (optional, overrides shared doc),
    'id' (optional, echoed back).

    Returns a list of results with keys: question, verdict, noul, tier (if ordinal),
    engine, latency_ms, id (if provided).
    """
    loaded_pack = load_pack(pack)
    qname = _first_noul_question(loaded_pack)
    if not qname:
        raise ValueError(f"Pack '{pack}' has no noul-type question")
    instructions = loaded_pack["questions"][qname]["instructions"]

    results = []
    for i, item in enumerate(items):
        question = item.get("question", "")
        if not question:
            results.append({"error": "missing question", "index": i})
            continue
        context = item.get("context", doc)
        full_instructions = f"{instructions} Question: {question}"
        try:
            resp = decide(context, {qname: {"type": "noul", "instructions": full_instructions}}, engine=engine)
            ans = resp["answers"][qname]
            noul = ans.get("noul", 0.0)
            label = loaded_pack["questions"][qname]["label_true"] if noul >= 0.5 else loaded_pack["questions"][qname]["label_false"]
            result = {
                "question": question,
                "verdict": label,
                "noul": round(noul, 3),
                "engine": engine,
                "latency_ms": resp["_noul_latency_ms"],
            }
            if ordinal:
                result["tier"] = ordinal_tier(noul)
            if "id" in item:
                result["id"] = item["id"]
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "question": question, "index": i})
    return results


def load_batch_input(path: str) -> list[dict]:
    """Load batch input from CSV, TSV, or JSONL.

    CSV/TSV must have a 'question' column. Optional: 'context', 'id'.
    JSONL: each line is a JSON object with 'question' (required), 'context' (optional), 'id' (optional).
    """
    ext = os.path.splitext(path)[1].lower()
    items = []
    if ext == ".jsonl":
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    elif ext in (".csv", ".tsv"):
        delim = "\t" if ext == ".tsv" else ","
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=delim)
            for row in reader:
                items.append(dict(row))
    else:
        raise ValueError(f"Unsupported input format: {ext}. Use .csv, .tsv, or .jsonl")
    return items


def save_batch_results(results: list[dict], path: str) -> None:
    """Save batch results as JSONL."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
