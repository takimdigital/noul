#!/usr/bin/env python3
"""router_before_llm.py — the "impossible" use case.

People try to do this with prompts ("only answer if the docs have it")
but LLMs ignore the instruction ~30% of the time. noul is a separate
calibrated gate that the LLM cannot override.

This script:
  1. Runs noul (90ms, $0) to check if docs contain the answer
  2. If YES → send to your expensive model (GPT-4/Claude)
  3. If NO → send to a cheap local model (Ollama/phi3) or abstain

Result: you only pay for expensive calls when the docs actually help.
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from noul import decide, doctor, load_pack

EXPENSIVE_MODEL = "claude-sonnet-4-20250514"  # only used when docs have the answer
CHEAP_MODEL = "phi3:mini"                      # used when docs don't have the answer
ENGINE = "kev"

def noul_check(context, question):
    pack = load_pack("answerability")
    qname, q = next(iter(pack["questions"].items()))
    instructions = f"{q['instructions']} Question: {question}"
    resp = decide(context, {qname: {"type": "noul", "instructions": instructions}}, engine=ENGINE)
    noul_val = resp["answers"][qname].get("noul", 0.0)
    return noul_val >= 0.5, noul_val, resp["_noul_latency_ms"]

def call_expensive(context, question):
    """This is where you'd call Claude/GPT-4. Skipped in demo."""
    return f"[EXPENSIVE MODEL {EXPENSIVE_MODEL} — would answer here using context]"

def call_cheap(context, question):
    """This is where you'd call Ollama/phi3."""
    return f"[CHEAP MODEL {CHEAP_MODEL} — context missing, giving generic response]"

def main():
    print("=" * 60)
    print("  ROUTER: noul decides → expensive vs cheap model")
    print("=" * 60)
    print(f"  Engine:  {ENGINE}")
    print(f"  Expensive model (docs have answer): {EXPENSIVE_MODEL}")
    print(f"  Cheap model (docs missing):         {CHEAP_MODEL}")
    print()

    if not doctor().get("kev", {}).get("reachable"):
        print("ERROR: Kev not reachable on :8009")
        return

    tests = [
        ("The budget is $12,000, deadline March 15, 2026.", "What is the deadline?"),
        ("The budget is $12,000, deadline March 15, 2026.", "What is the CEO's favorite color?"),
        ("The medication is 500mg twice daily for 7 days.", "What is the dosage?"),
        ("The medication is 500mg twice daily for 7 days.", "What is the patient's blood type?"),
    ]

    noul_time = 0
    routed_expensive = 0
    routed_cheap = 0

    for ctx, q in tests:
        is_ans, noul_val, ms = noul_check(ctx, q)
        noul_time += ms
        if is_ans:
            routed_expensive += 1
            action = f"→ EXPENSIVE ({EXPENSIVE_MODEL})"
        else:
            routed_cheap += 1
            action = f"→ CHEAP ({CHEAP_MODEL})"
        print(f"  noul={noul_val:.3f} {ms:.1f}ms  {action}  q={q}")

    print()
    print(f"  Routed to expensive: {routed_expensive} (only when docs help)")
    print(f"  Routed to cheap:     {routed_cheap} (docs missing)")
    print(f"  noul overhead:       {noul_time:.1f}ms total, {noul_time/len(tests):.1f}ms avg")
    print(f"  Cost savings:        ~{routed_cheap}/{len(tests)} calls avoided expensive model")

if __name__ == "__main__":
    main()
