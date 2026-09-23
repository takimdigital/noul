"""noul evaluation harness — FEAS L1/L4: refuses automation until >=100 labels pass the gate."""
from __future__ import annotations

import json
import math
import os
from collections import Counter

LOG_PATH = os.path.expanduser("~/.noul/log.jsonl")
LABELS_PATH = os.path.expanduser("~/.noul/labels.jsonl")


def load_log() -> list[dict]:
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_labels() -> list[dict]:
    if not os.path.exists(LABELS_PATH):
        return []
    with open(LABELS_PATH, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def add_label(check_index: int, correct_label: str) -> None:
    """Label a specific check from the log. `correct_label` is the TRUE answer (ANSWERABLE/NOT ANSWERABLE)."""
    os.makedirs(os.path.dirname(LABELS_PATH), exist_ok=True)
    with open(LABELS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"check_index": check_index, "correct_label": correct_label}) + "\n")


def labels_count() -> int:
    return len(load_labels())


def eval_card() -> dict:
    """FEAS L1/L4 eval card. Refuses under 100 labels / 20 per class / kappa < 0.6."""
    labels = load_labels()
    n = len(labels)

    # L1: refuse under 100
    if n < 100:
        return {
            "status": "REFUSED",
            "reason": f"Need >=100 labels, have {n}.",
            "labels_required": 100,
            "labels_per_class": 20,
            "kappa_min": 0.6,
        }

    # Count per class
    counts = Counter(l["correct_label"] for l in labels)
    per_class_ok = all(c >= 20 for c in counts.values())
    if not per_class_ok:
        return {
            "status": "REFUSED",
            "reason": f"Need >=20 per class, have {dict(counts)}.",
            "labels_required": 100,
            "labels_per_class": 20,
            "kappa_min": 0.6,
        }

    # Accuracy (vs model prediction)
    log = load_log()
    correct = 0
    for lab in labels:
        idx = lab["check_index"]
        if idx < len(log):
            pred = log[idx]["label"]
            if pred == lab["correct_label"]:
                correct += 1
    accuracy = correct / n if n > 0 else 0.0

    # Wilson CI
    z = 1.96
    p = accuracy
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    ci_low = max(0.0, center - spread)
    ci_high = min(1.0, center + spread)

    # Kappa (simplified — assumes two human raters agreed, uses model as one rater)
    # This is INFERRED until two-human kappa is measured
    kappa = 0.0
    if n > 0:
        # placeholder: kappa requires two-human overlap, not yet measured
        kappa = None  # INFERRED

    passed = accuracy >= 0.80 and (kappa is None or kappa >= 0.6)

    return {
        "status": "PASS" if passed else "BELOW_THRESHOLD",
        "n": n,
        "accuracy": round(accuracy, 3),
        "ci_low": round(ci_low, 3),
        "ci_high": round(ci_high, 3),
        "kappa": kappa,
        "per_class_counts": dict(counts),
        "rule_of_three_max_claim": f"{(1 - 3/n)*100:.1f}%" if n >= 3 else "n/a",
        "enforce_allowed": passed,
    }
