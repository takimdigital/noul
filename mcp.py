#!/usr/bin/env python3
"""noul MCP shim — one tool (answerable) + can_automate. stdlib-only."""
import json
import sys
import os

# Add parent so `import noul` works when run from the repo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noul import decide, doctor, ENGINES, load_pack, run_control, __version__

MCP_NAME = "noul"
MCP_VERSION = __version__


def _answerable(state: str, question: str, engine: str = "kev") -> dict:
    pack = load_pack("answerability")
    qname, q = next(iter(pack["questions"].items()))
    instructions = f"{q['instructions']} Question: {question}"
    resp = decide(state, {qname: {"type": "noul", "instructions": instructions}}, engine=engine)
    ans = resp["answers"][qname]
    noul = ans.get("noul", 0.0)
    label = q["label_true"] if noul >= 0.5 else q["label_false"]
    return {
        "answerable": label == "ANSWERABLE",
        "noul": round(noul, 3),
        "confidence": round(noul, 3) if label == "ANSWERABLE" else round(1 - noul, 3),
        "engine": engine,
        "latency_ms": resp["_noul_latency_ms"],
    }


def _can_automate() -> dict:
    """FEAS L1/L4: refuse automation until a measured card exists."""
    return {
        "allowed": False,
        "reason": "No eval card exists yet. Run `noul eval --pack answerability` with >=100 labels first.",
        "labels_required": 100,
        "labels_per_class": 20,
        "kappa_min": 0.6,
    }


def _handle(req: dict) -> dict:
    method = req.get("method", "")
    params = req.get("params", {})
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "answerable",
                    "description": "Does this context contain the answer to this question? Returns ANSWERABLE/NOT ANSWERABLE with probability.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "state": {"type": "string", "description": "The retrieved context / document."},
                            "question": {"type": "string", "description": "The question to check."},
                            "engine": {"type": "string", "description": "Engine: kev (default, calibrated) or laya."},
                        },
                        "required": ["state", "question"],
                    },
                },
                {
                    "name": "can_automate",
                    "description": "Returns whether automation is allowed (refused until a measured eval card exists).",
                    "inputSchema": {"type": "object", "properties": {}},
                },
            ]
        }
    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})
        if name == "answerable":
            return {"content": [{"type": "text", "text": json.dumps(_answerable(**args), indent=2)}]}
        if name == "can_automate":
            return {"content": [{"type": "text", "text": json.dumps(_can_automate(), indent=2)}]}
        return {"error": f"unknown tool: {name}"}
    return {"error": f"unknown method: {method}"}


def print_config(host: str = "lmstudio") -> str:
    """Return a copy-paste JSON block for the given host."""
    block = {
        "mcpServers": {
            "noul": {
                "command": sys.executable,
                "args": [__file__, "--stdio"],
            }
        }
    }
    configs = {
        "lmstudio": ("~/.lmstudio/mcp.json", block),
        "vscode": (".vscode/mcp.json", block),
        "claude": ("claude_desktop_config.json", block),
        "openwebui": ("(Admin → Integrations → MCP → Streamable HTTP → http://127.0.0.1:8080/mcp)", block),
    }
    path, cfg = configs.get(host, configs["lmstudio"])
    return f"# paste into {path}:\n{json.dumps(cfg, indent=2)}"


def main():
    import argparse
    p = argparse.ArgumentParser(prog="noul-mcp")
    p.add_argument("--print-config", choices=["lmstudio", "vscode", "claude", "openwebui"])
    p.add_argument("--stdio", action="store_true", help="Run as stdio MCP server")
    args = p.parse_args()
    if args.print_config:
        print(print_config(args.print_config))
        return
    if args.stdio:
        # stdio JSON-RPC loop
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = _handle(req)
            except Exception as e:
                resp = {"error": str(e)}
            print(json.dumps(resp), flush=True)
        return
    p.print_help()


if __name__ == "__main__":
    main()
