"""Pack loading + FEAS-D5 polarity validation."""
from __future__ import annotations

import json
import os
import sys

DEFAULT_PACK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "noul", "packs")

REQUIRED_KEYS = {"name", "version", "description", "questions"}
QUESTION_TYPES = {"choice", "noul", "score"}


def load_pack(name: str, pack_dir: str = DEFAULT_PACK_DIR) -> dict:
    path = os.path.join(pack_dir, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Pack '{name}' not found at {path}. Available: {list_packs(pack_dir)}"
        )
    with open(path, encoding="utf-8") as f:
        pack = json.load(f)
    missing = REQUIRED_KEYS - set(pack.keys())
    if missing:
        raise ValueError(f"Pack '{name}' missing required keys: {missing}")
    for qname, q in pack["questions"].items():
        if q.get("type") not in QUESTION_TYPES:
            raise ValueError(f"Pack '{name}' question '{qname}' has invalid type: {q.get('type')}")
    return pack


def list_packs(pack_dir: str = DEFAULT_PACK_DIR) -> list[str]:
    if not os.path.isdir(pack_dir):
        return []
    return [f[:-5] for f in os.listdir(pack_dir) if f.endswith(".json")]


def show_pack(name: str, pack_dir: str = DEFAULT_PACK_DIR) -> str:
    pack = load_pack(name, pack_dir)
    lines = [f"Pack: {pack['name']} v{pack['version']}", f"Description: {pack['description']}", ""]
    for qname, q in pack["questions"].items():
        lines.append(f"[{q['type']}] {qname}: {q['instructions']}")
        if "criteria" in q:
            c = q["criteria"]
            if isinstance(c, dict):
                for opt, desc in c.items():
                    lines.append(f"      - {opt}: {desc}")
            elif isinstance(c, list):
                for i, label in enumerate(c):
                    lines.append(f"      {i}: {label}")
    if pack.get("controls"):
        lines.append("")
        lines.append(f"Controls ({len(pack['controls'])}):")
        for ctrl in pack["controls"]:
            lines.append(f"  - {ctrl['name']}: {ctrl['description']}")
    return "\n".join(lines)


def run_control(
    pack_name: str, engine: str, pack_dir: str = DEFAULT_PACK_DIR
) -> dict:
    """Run the D5 vague/contrast control pair and return gaps. FEAS D5 requires gap >= 0.50."""
    pack = load_pack(pack_name, pack_dir)
    controls = pack.get("controls", [])
    if not controls:
        return {"pack": pack_name, "controls_run": 0, "results": []}
    from .engine import decide

    results = []
    for ctrl in controls:
        doc = ctrl["questionable_doc"]
        # Map each control question into the pack's first noul question slot
        # (the abstention signal is what the control tests).
        target_qname = _first_noul_question(pack)
        if not target_qname:
            results.append({"control": ctrl["name"], "error": "pack has no noul question to test"})
            continue

        vague_payload = {
            target_qname: {"type": "noul", "instructions": f"Is this true? {ctrl['vague_question']}"}
        }
        contrast_payload = {
            target_qname: {
                "type": "noul",
                "instructions": f"Is this true? {ctrl['contrast_question']}",
            }
        }
        vague_resp = decide(doc, vague_payload, engine=engine)
        contrast_resp = decide(doc, contrast_payload, engine=engine)
        v_prob = vague_resp["answers"][target_qname].get("noul", 0.0)
        c_prob = contrast_resp["answers"][target_qname].get("noul", 0.0)
        gap = v_prob - c_prob
        results.append(
            {
                "control": ctrl["name"],
                "vague_question": ctrl["vague_question"],
                "contrast_question": ctrl["contrast_question"],
                "vague_noul": round(v_prob, 3),
                "contrast_noul": round(c_prob, 3),
                "gap": round(gap, 3),
                "gap_min": ctrl.get("gap_min", 0.50),
                "PASS": gap >= ctrl.get("gap_min", 0.50),
                "vague_ms": vague_resp["_noul_latency_ms"],
                "contrast_ms": contrast_resp["_noul_latency_ms"],
            }
        )
    all_pass = all(r.get("PASS", False) for r in results)
    return {"pack": pack_name, "controls_run": len(results), "all_pass": all_pass, "results": results}


def _first_noul_question(pack: dict) -> str | None:
    for qname, q in pack["questions"].items():
        if q["type"] == "noul":
            return qname
    return None
