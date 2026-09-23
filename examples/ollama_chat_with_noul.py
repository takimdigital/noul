#!/usr/bin/env python3
"""ollama_chat_with_noul.py — a drop-in wrapper that runs noul as a guard before every Ollama call.

Usage:
    python examples/ollama_chat_with_noul.py

Requirements:
    pip install ollama  (or install Ollama from https://ollama.com)
    pip install laya noul
    uv run --extra serve python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from noul import decide, doctor, load_pack

OLLAMA_MODEL = "llama3.2:latest"
ENGINE = "kev"
ABSTAIN_REPLY = "I don't know — the retrieved context doesn't contain the answer to that question."

SYSTEM = "You are a helpful assistant. Answer ONLY using the provided context. If the context doesn't say, say you don't know."


def ollama_chat(messages: list, model: str = OLLAMA_MODEL) -> str:
    """Call Ollama's /api/chat. Falls back to echo if Ollama is unreachable."""
    try:
        import urllib.request, json
        body = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=body,
                                     headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["message"]["content"]
    except Exception as e:
        return f"[Ollama unreachable: {e}]"


def noul_check(context: str, question: str) -> tuple[bool, float]:
    """Returns (is_answerable, noul_probability)."""
    pack = load_pack("answerability")
    qname, q = next(iter(pack["questions"].items()))
    instructions = f"{q['instructions']} Question: {question}"
    resp = decide(context, {qname: {"type": "noul", "instructions": instructions}}, engine=ENGINE)
    noul_val = resp["answers"][qname].get("noul", 0.0)
    # noul high = condition applies (answer is stated)
    return noul_val >= 0.5, noul_val


def gated_answer(context: str, question: str) -> str:
    """Run noul first. If NOT ANSWERABLE, abstain. Otherwise, call Ollama."""
    is_ans, noul_val = noul_check(context, question)
    print(f"  [noul] {'ANSWERABLE' if is_ans else 'NOT ANSWERABLE'} noul={noul_val:.3f}  {resp_ms():.1f}ms")
    if not is_ans:
        return ABSTAIN_REPLY
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    return ollama_chat(messages)


def resp_ms():
    return 0  # placeholder; noul latency printed by decide()


def main():
    print("=" * 60)
    print("  noul + Ollama — gated chat demo")
    print("=" * 60)
    print(f"  Ollama model: {OLLAMA_MODEL}")
    print(f"  noul engine:  {ENGINE} (:8009)")
    print()
    eng = doctor()
    if not eng.get("kev", {}).get("reachable"):
        print("  ERROR: Kev engine not reachable on :8009")
        print("  Run: uv run --extra serve python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009")
        return

    context = (
        "The client capped the project budget at $12,000 and asked for weekly status reports every Monday. "
        "The project deadline is March 15, 2026. The team uses agile methodology with 2-week sprints. "
        "The main developer is Sarah Chen, reachable at sarah@example.com."
    )
    questions = [
        "What is the project deadline?",
        "Who is the main developer?",
        "What is the CEO's home address?",
        "How often are status reports?",
        "What is the company's stock price?",
    ]

    for q in questions:
        print(f"\nQ: {q}")
        answer = gated_answer(context, q)
        print(f"A: {answer}")


if __name__ == "__main__":
    main()
