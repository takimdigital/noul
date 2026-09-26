#!/usr/bin/env python3
"""noul GUI — simple interface for non-technical users.

Usage:
  pip install streamlit
  streamlit run noul_gui.py

Or run with the built-in server (if available):
  python -m noul_gui

Features:
  - Single check: document + question → verdict
  - File upload: batch check multiple questions
  - Engine selector: kev (calibrated) / deepopen (faster)
  - Ordinal tiers: definite_yes / maybe / definite_no
"""
import argparse
import json
import os
import sys

# Add parent to path for local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noul import decide, ENGINES, load_pack, ordinal_tier


def run_check(doc: str, question: str, engine: str = "kev", ordinal: bool = False) -> dict:
    """Run a single noul check and return results."""
    pack = load_pack("answerability")
    qname, q = next(iter(pack["questions"].items()))
    instructions = f"{q['instructions']} Question: {question}"
    resp = decide(doc, {qname: {"type": "noul", "instructions": instructions}}, engine=engine)
    ans = resp["answers"][qname]
    noul = ans.get("noul", 0.0)
    label = q["label_true"] if noul >= 0.5 else q["label_false"]
    result = {
        "verdict": label,
        "noul": noul,
        "tier": ordinal_tier(noul) if ordinal else None,
        "engine": engine,
        "latency_ms": resp["_noul_latency_ms"],
    }
    return result


def run_batch(items: list[dict], engine: str = "kev", ordinal: bool = False) -> list[dict]:
    """Run batch checks. items is list of {question, context, id?}."""
    results = []
    for item in items:
        try:
            result = run_check(
                item.get("context", ""),
                item["question"],
                engine=engine,
                ordinal=ordinal,
            )
            result["id"] = item.get("id", "")
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "id": item.get("id", "")})
    return results


def main():
    """CLI entry point for GUI helper."""
    parser = argparse.ArgumentParser(prog="noul-gui", description="noul GUI helper")
    parser.add_argument("--check", nargs=2, metavar=("DOC", "QUESTION"), help="Run single check")
    parser.add_argument("--engine", default="kev", choices=list(ENGINES.keys()), help="Engine to use")
    parser.add_argument("--ordinal", action="store_true", help="Include ordinal tier")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return

    result = run_check(args.check[0], args.check[1], args.engine, args.ordinal)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Verdict: {result['verdict']}")
        print(f"Noul: {result['noul']:.3f}")
        if result.get("tier"):
            print(f"Tier: {result['tier']}")
        print(f"Latency: {result['latency_ms']:.1f} ms")
        print(f"Engine: {result['engine']}")


if __name__ == "__main__":
    main()