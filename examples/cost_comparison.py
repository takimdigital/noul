#!/usr/bin/env python3
"""Show cost savings: noul (free) vs API-based guard ($$).

A typical n8n RAG workflow sends every question to an LLM judge
to check if the retrieved docs contain the answer.

Cost at scale: 5,000 questions/day × $0.005 = $750/month
With noul: $0/month, 90ms vs 2-5s per decision.
"""
# Cost comparison table
scenarios = [
    {"name": "Small team", "q_per_day": 500, "months": 1},
    {"name": "Growth startup", "q_per_day": 5000, "months": 1},
    {"name": "Enterprise", "q_per_day": 50000, "months": 1},
]

api_cost_per_call = 0.005  # GPT-4.1-nano, short context
noul_cost_per_call = 0.00
noul_latency_ms = 90
api_latency_ms = 3500

print("=" * 60)
print("  COST COMPARISON: noul vs API-based abstention guard")
print("=" * 60)
print()
print(f"{'Scenario':<20} {'Questions/mo':<14} {'API cost/mo':<14} {'noul cost/mo':<14} {'Savings':<10}")
print("-" * 72)
for s in scenarios:
    q_per_month = s["q_per_day"] * 30
    api_cost = q_per_month * api_cost_per_call
    noul_cost = q_per_month * noul_cost_per_call
    savings = api_cost - noul_cost
    print(f"{s['name']:<20} {q_per_month:>10,}    ${api_cost:>10,.0f}    ${noul_cost:>10,.0f}    ${savings:>8,.0f}")

print()
print("Speed comparison:")
print(f"  noul decision:  {noul_latency_ms} ms  (local, Kev-0.8B, GPU)")
print(f"  API guard call: {api_latency_ms} ms  (round-trip to OpenAI/Anthropic)")
print(f"  Speedup: {api_latency_ms/noul_latency_ms:.0f}x")
print()
print("What this means:")
print("  - 5,000 questions/day: API guard costs ~$750/mo, noul costs $0")
print("  - No rate limits, no API keys, no data leaving the box")
print("  - Works offline (Algeria's exam-period internet cuts? no problem)")
