import json
import os
import sys
import time
sys.path.insert(0, 'D:/laya')
from noul import decide

GT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'eval_ground_truth.jsonl')

with open(GT_PATH) as f:
    cases = [json.loads(l) for l in f if l.strip()]

correct = 0
total = len(cases)
tp = fp = tn = fn = 0
times = []

print(f"Running {total} checks against Kev...\n")
for c in cases:
    t0 = time.perf_counter()
    resp = decide(
        c['context'],
        {'q': {'type': 'noul',
               'instructions': 'Is the specific answer to this question directly stated in the context above? Answer YES if the exact answer is present, NO if it requires guessing or outside knowledge. Question: ' + c['question']}},
        engine='kev'
    )
    dt = (time.perf_counter() - t0) * 1000
    times.append(dt)
    ans = resp['answers']['q']
    noul = ans.get('noul', 0.0)
    pred = 'ANSWERABLE' if noul >= 0.5 else 'NOT ANSWERABLE'
    truth = c['ground_truth']
    ok = pred == truth
    if ok:
        correct += 1
        if truth == 'ANSWERABLE':
            tp += 1
        else:
            tn += 1
    else:
        if pred == 'ANSWERABLE':
            fp += 1
        else:
            fn += 1
    mark = 'OK' if ok else 'FAIL'
    print(f"  [{mark}] noul={noul:.3f}  pred={pred:<16} true={truth:<16} {dt:.1f}ms  q={c['question'][:55]}")

accuracy = correct / total
avg_ms = sum(times) / total
p_correct = tp / (tp + fp) if (tp + fp) > 0 else 0
r_correct = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * p_correct * r_correct / (p_correct + r_correct) if (p_correct + r_correct) > 0 else 0

# Wilson CI for accuracy
import math
z = 1.96
p = accuracy
n = total
denom = 1 + z**2 / n
center = (p + z**2 / (2 * n)) / denom
spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
ci_low = max(0.0, center - spread)
ci_high = min(1.0, center + spread)

print(f"\n{'='*60}")
print(f"  EVAL CARD — noul v0.1 / Kev-0.8B  ({total} items)")
print(f"{'='*60}")
print(f"  accuracy:      {accuracy:.3f} ({correct}/{total})")
print(f"  95% Wilson CI: [{ci_low:.3f}, {ci_high:.3f}]")
print(f"  precision:     {p_correct:.3f}  (TP={tp}, FP={fp})")
print(f"  recall:        {r_correct:.3f}  (TP={tp}, FN={fn})")
print(f"  F1:            {f1:.3f}")
print(f"  avg latency:   {avg_ms:.1f} ms")
print(f"  min latency:   {min(times):.1f} ms")
print(f"  max latency:   {max(times):.1f} ms")
print(f"  NOT ANSWERABLE detected: {tn}/{tn+fp}")
print(f"{'='*60}")
print(f"  rule-of-three (L4): error rate <= {3/n*100:.1f}% (min acc {(1-3/n)*100:.1f}%) with 95% confidence")
print(f"{'='*60}")
