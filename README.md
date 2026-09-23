# noul

**The local abstention gate. Tell your RAG when the docs *don't* have the answer.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![Eval: 42/42](https://img.shields.io/badge/eval-42%2F42%20✓-success.svg)](https://github.com/takimdigital/noul/blob/main/packs/answerability.json)

```bash
pip install laya noul && noul doctor && noul check --doc "The budget is $12k." --ask "What is the budget?"
```

```
ANSWERABLE       noul=0.92   90ms

$ noul check --doc "The budget is $12k." --ask "What color is the CEO laptop?"
NOT ANSWERABLE   noul=0.19   → ABSTAIN
```

Zero network calls. Zero labels required to start. Your documents never leave the box.

---

## Why

Retrieval makes models lie:

- **Claude 3.5 Sonnet** abstains **84%** closed-book, only **52%** with RAG
- **43%** of RAG answers contain a hallucinated span
- The model *knows* the docs don't have the answer — but it answers anyway

`noul` runs a **26–135 ms** local check before your LLM generates, and says *"your docs don't have this — don't guess."*

It's the missing half of your local stack: **Ollama generates, noul decides when to shut up.**

---

## Features

- **Typed decisions** — choice / score / noul (abstention), one forward pass
- **Calibrated probabilities** from Kev-0.8B (ECE 0.089, acts 64% at 99%)
- **MCP server** — one tool (`answerable`) plugs into LM Studio, VS Code, Claude Desktop, Open WebUI
- **CLI** — `check`, `pack`, `eval`, `mcp`, `tally`, `doctor`
- **Sealed eval card** — refuses automation until ≥100 labels pass the gate
- **Stdlib only** — zero transitive dependencies

---

## Install

```bash
pip install laya noul
```

Requires a running engine. Quickest path (Kev-0.8B):

```bash
uv sync --extra serve
uv run --extra serve python -m kev.serve --run jaredpalmer/kev-0.8b --port 8009
```

Then:

```bash
noul doctor        # check engine status
```

---

## Quick start

```bash
# Single check
noul check --doc "The client capped the budget at $12k and asked for weekly reports." --ask "How often are reports?"
# ANSWERABLE       noul=0.92   90ms

# File input
noul check --file document.md --ask "What is the deadline?"

# FEAS D5 polarity control (gap >= 0.50 required)
noul pack control answerability

# Eval card (refused below 100 labels)
noul eval --pack answerability

# MCP config block for your host
noul mcp --print-config lmstudio    # lmstudio|vscode|claude|openwebui
```

Paste the printed JSON into `~/.lmstudio/mcp.json`, then ask your agent: *"should I trust this answer?"*

---

## How it works

```
Your app → retrieve(docs, question)
              ↓
         noul check --doc {docs} --ask {question}
              ↓
         POST http://127.0.0.1:8009/v1/systemone
              ↓
         Kev-0.8B: typed decision + calibrated probability
              ↓
         ANSWERABLE (0.92)     |     NOT ANSWERABLE (0.19)
              ↓                         ↓
         send to LLM               ABSTAIN, don't guess
```

`noul` sends `{state, model, questions}` to `/v1/systemone` and gets back a typed decision in a single forward pass — no generation, no parsing, no hallucination.

---

## Eval card

Measured 2026-09-23 on Kev-0.8B (CUDA, RTX 3070). Balanced 21/21.

| Metric | Value |
|---|---|
| **n** | 42 |
| **Accuracy** | **1.000** (42/42) |
| **95% Wilson CI** | [0.916, 1.0] |
| Precision | 1.0 (0 FP) |
| Recall | 1.0 (0 FN) |
| F1 | 1.0 |
| Latency (avg) | 114.7 ms |
| D5 polarity gap | **0.74** (min 0.50) |

> Rule-of-three (FEAS L4): 0 errors in 42 items → claim ≥92.9% with 95% confidence.

See [`packs/answerability.json`](packs/answerability.json) for the full measurement record.

---

## MCP

`noul` ships as a stdio MCP server. One tool, zero config:

```bash
noul mcp --print-config lmstudio
```

Exposes:

| Tool | Description |
|---|---|
| `answerable(state, question, engine?)` | Does this context contain the answer? Returns ANSWERABLE / NOT ANSWERABLE + probability |
| `can_automate()` | Returns whether automation is allowed (refused until a measured eval card exists) |

Works with **LM Studio**, **VS Code**, **Claude Desktop**, **Open WebUI** — any MCP host.

---

## CLI reference

| Command | Description |
|---|---|
| `noul check --doc TEXT --ask QUESTION` | Run one answerability check |
| `noul check --file FILE --ask QUESTION` | Read context from file |
| `noul doctor` | Engine status (latency, enforce readiness) |
| `noul pack list` | List installed packs |
| `noul pack show NAME` | Show pack contents |
| `noul pack control NAME` | Run FEAS D5 polarity controls |
| `noul tally` | Usage counter (ANSWERABLE / NOT ANSWERABLE) |
| `noul label --index N --correct LABEL` | Label a check for eval |
| `noul eval --pack NAME` | Print sealed eval card |
| `noul mcp --print-config HOST` | Copy-paste MCP config block |

---

## Engine

| Engine | Params | Context | Latency (GPU) | ECE | Gate? |
|---|---|---|---|---|---|
| **Kev-0.8B** (default) | 0.8B | 512–8k | 90–135 ms | **0.089** | ✅ Yes |
| Laya (EN) | 421M | 1024 | 26 ms | unmeasured | ⚠️ Display only |
| Laya (multi) | 322M | 1024–8k | 35 ms | 0.234 | ❌ No |

Kev is the only MEASURED gate on this box (ECE 0.089, acts 64% at 99%). Laya's confidence is not a gate.

---

## Limitations

- One document per call (≤512 tokens EN, ≤1024 multilingual)
- EN-only enforcement in v0.1
- Not a defence against adversarial input (FEAS H5: 8% accuracy under attack)
- κ is INFERRED (single annotator; two-human overlap pending)

---

## Roadmap

- [ ] Two-human κ measurement (FEAS L3)
- [ ] ≥100-label eval card on public corpus (FEAS L1)
- [ ] EN-Laya ECE measurement (FEAS H4)
- [ ] Second pack: MCP tool shortlist (U-DEV #1)
- [ ] Open WebUI pipeline hook: `retrieve → gate → generate`
- [ ] Batch CSV runner (`decidekit`)
- [ ] Docker sidecar + Compose

---

## FAQ

**Is this a classifier?**
Yes. A non-autoregressive typed-decision model that outputs labels + calibrated probabilities. No text generation.

**Why not just use an LLM as a judge?**
Two reasons: (1) an LLM judge is ~100× slower and costs per call; (2) an LLM judge is itself a source of hallucination. `noul` is the consistency check, not another source of error.

**What does "noul" mean?**
"None of the usual labels" — the abstention primitive. When none of your labels fit, `noul` is the answer.

**Can I use this with Ollama?**
Yes. Run Ollama for generation, run `noul` (with Kev) for decisions. They coexist on 8 GB VRAM (1.7 GB for Kev + ~5 GB for a 7B).

**What if the docs are longer than 512 tokens?**
Split into chunks, run `noul` per chunk, aggregate. v0.1 is per-page; hierarchical aggregation is a rung on the roadmap.

---

## License

Apache-2.0 © 2026 [Takim Digital](https://github.com/takimdigital)
