# noul — the local abstention gate

**Tell your RAG when the docs *don't* have the answer.**

`noul` runs one question against one context in ~90 ms locally (Kev-0.8B on CUDA) and answers:
- **ANSWERABLE** — the context has the exact answer
- **NOT ANSWERABLE** — the context doesn't, so your LLM shouldn't guess

Zero network calls. Zero labels required to start. Your documents never leave the box.

```
$ noul check --doc "The budget is $12k." --ask "What is the budget?"
  ANSWERABLE       noul=0.92   90ms

$ noul check --doc "The budget is $12k." --ask "What color is the CEO laptop?"
  NOT ANSWERABLE   noul=0.19   → ABSTAIN
```

---

## Why

Retrieval makes models lie. Claude 3.5 Sonnet abstains 84% closed-book but only 52% with RAG. 43% of RAG answers contain a hallucinated span. `noul` names the failure before your LLM does.

It's the missing half of your local stack: Ollama generates, **noul decides when to shut up**.

---

## Install

```bash
pip install laya noul
noul doctor
```

Requires a running engine:

```bash
# Kev-0.8B (recommended, calibrated gate, ECE 0.089)
uv sync --extra serve && uv run --extra serve python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
```

---

## Usage

```bash
noul check --doc "..." --ask "?"
noul check --file document.md --ask "?"
noul pack control answerability     # FEAS D5 polarity check (gap >= 0.50)
noul eval --pack answerability     # card (refused until >=100 labels)
noul mcp --print-config lmstudio   # copy-paste block
```

---

## MCP

```bash
noul mcp --print-config lmstudio
# paste the printed JSON into ~/.lmstudio/mcp.json
```

Exposes one tool: `answerable(state, question, engine)` → typed JSON.

Works with LM Studio, VS Code, Claude Desktop, Open WebUI.

---

## Eval card (measured, 2026-09-23)

| Metric | Value |
|---|---|
| n | 42 (balanced 21/21) |
| accuracy | 1.000 |
| 95% Wilson CI | [0.916, 1.0] |
| precision | 1.0 (0 FP) |
| recall | 1.0 (0 FN) |
| F1 | 1.0 |
| avg latency | 114.7 ms |
| D5 polarity gap | 0.74 (min 0.50) |

Engine: Kev-0.8B on CUDA (RTX 3070). See `packs/answerability.json`.

---

## How it works

`noul` sends `{state, model, questions}` to `http://127.0.0.1:8009/v1/systemone` and gets back a typed decision with calibrated probabilities in a single forward pass.

- Engine: **Kev-0.8B** (ECE 0.089, acts 64% at 99% — the only MEASURED gate)
- Latency: 90 ms p50 GPU, 319 ms CPU
- VRAM: 1.7 GB (co-resides with a 7B on 8 GB)

---

## Limitations

- One document per call (one page, ≤512 tokens EN)
- EN-only enforcement in v0.1
- Stock Laya confidence is **not** a gate (ECE 0.234) — use Kev for `--enforce`
- Not a defence against adversarial input (FEAS H5: 8% accuracy under attack)
- Kappa INFERRED (single annotator so far; two-human overlap pending)

---

## Why `noul`

`noul` = "none of the usual labels" — the abstention primitive itself. When retrieval makes models lie, `noul` names it.

---

## License

Apache-2.0
