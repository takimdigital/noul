"""openwebui_function.py — a filter function for Open WebUI.

Install in Open WebUI → Admin → Functions → + New Function
Name: noul
Paste this entire file.

It runs noul as a guard before each generation. If the retrieved docs
don't contain the answer, it injects an ABSTAIN prompt instead.

Requires:
    pip install laya noul
    uv run --extra serve python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
"""
from __future__ import annotations

def load_pack(name: str):
    import json, os
    path = os.path.join(os.path.dirname(__file__), "packs", f"{name}.json")
    with open(path) as f:
        return json.load(f)

def noul_check(state: str, question: str, engine: str = "kev") -> tuple:
    from noul import decide
    pack = load_pack("answerability")
    qname, q = next(iter(pack["questions"].items()))
    instructions = f"{q['instructions']} Question: {question}"
    resp = decide(state, {qname: {"type": "noul", "instructions": instructions}}, engine=engine)
    noul = resp["answers"][qname].get("noul", 0.0)
    return noul >= 0.5, noul

class Filter:
    """Open WebUI filter interface."""
    class Valves:
        ENGINE = "kev"
        ABSTAIN_MESSAGE = "I don't know — the retrieved context doesn't contain the answer to that question."

    async def inlet(self, body: dict, __user__=None, __event_emitter__=None) -> dict:
        messages = body.get("messages", [])
        if not messages:
            return body

        # Get the user's last message
        last_user = None
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break

        if not last_user:
            return body

        # Get the system/context message (Open WebUI injects retrieved docs here)
        context = ""
        for m in messages:
            if m.get("role") == "system":
                context += m.get("content", "") + "\n"

        if not context.strip():
            return body

        try:
            is_ans, noul_val = noul_check(context, last_user, self.Valves.ENGINE)
            if not is_ans:
                # Replace user message with an abstain instruction
                for m in messages:
                    if m.get("role") == "system":
                        m["content"] = (
                            f"{m.get('content', '')}\n\n"
                            f"[noul gate: NOT ANSWERABLE (noul={noul_val:.3f}) — "
                            f"do not answer this question from the docs. "
                            f"Say: '{self.Valves.ABSTAIN_MESSAGE}']"
                        )
        except Exception as e:
            pass  # Fail open — don't block the user if noul is down

        return body
