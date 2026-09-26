"""noul — the local abstention gate. stdlib-only."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error

__version__ = "0.1.0"

# Engines. kev is the only MEASURED gate on this box (ECE 0.089, acts 64% at 99%).
# DeepOpen is the production Laya engine (1,020⭐, 4 days, CLINC150/Banking77 benchmarks).
ENGINES = {
    "kev": {
        "url": "http://127.0.0.1:8009/v1/systemone",
        "model": "kev-latest",
        "default": True,
        "enforce": True,
        "notes": "ECE 0.089, acts 64% at 99%. The only enforce-ready engine.",
    },
    "laya": {
        "url": None,  # not running on this box; document-only in v0.1
        "model": "laya-en",
        "default": False,
        "enforce": False,
        "notes": "EN-Laya ECE unmeasured. Multilingual ECE 0.234 with flat sweep. Display/suggest only in v0.1.",
    },
    "deepopen": {
        "url": "http://127.0.0.1:8009/v1/systemone",
        "model": "deepopen",
        "default": False,
        "enforce": False,
        "notes": "Production Laya engine (1,020⭐, CLINC150/Banking77 benchmarks). 33ms single, 7.2ms batched on T4. 3 question types: choice, score, noul. Built-in Router selects best checkpoint per request. RLCD training (strictly proper scoring rules). 6-7x faster than TypeSafe Jev.",
    },
}


def decide(
    state: str,
    questions: dict,
    engine: str = "kev",
    timeout: float = 10.0,
) -> dict:
    """Call the engine's /v1/systemone endpoint. Returns the parsed JSON response."""
    cfg = ENGINES.get(engine)
    if not cfg or not cfg["url"]:
        raise RuntimeError(
            f"Engine '{engine}' has no reachable endpoint in v0.1. "
            f"Use --engine kev (the only MEASURED gate on this box)."
        )
    body = json.dumps({"state": state, "model": cfg["model"], "questions": questions}).encode()
    req = urllib.request.Request(
        cfg["url"], data=body, headers={"content-type": "application/json"}, method="POST"
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            latency_ms = (time.perf_counter() - t0) * 1000
            out = json.loads(raw)
            out["_noul_engine"] = engine
            out["_noul_latency_ms"] = round(latency_ms, 1)
            return out
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Engine '{engine}' at {cfg['url']} unreachable: {e}. "
            f"Is the server running? (e.g. `python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009`)"
        ) from e


def doctor() -> dict:
    """Return engine status for the active engine."""
    results = {}
    for name, cfg in ENGINES.items():
        if not cfg["url"]:
            results[name] = {"reachable": False, "reason": "no endpoint configured"}
            continue
        t0 = time.perf_counter()
        try:
            out = decide(
                "ping",
                {"q": {"type": "noul", "instructions": "is this a test?"}},
                engine=name,
            )
            results[name] = {
                "reachable": True,
                "latency_ms": out["_noul_latency_ms"],
                "model": out.get("model"),
                "enforce": cfg["enforce"],
                "notes": cfg["notes"],
            }
        except Exception as e:
            results[name] = {"reachable": False, "reason": str(e)}
    return results
