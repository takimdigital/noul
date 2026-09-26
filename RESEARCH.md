# RESEARCH.md — fast-decision models & how to beat them

Sources this session:
- YouTube: "Faster Jev is HERE" (CoderOne, 2026-09)
- HuggingFace: `fastino/GLiNER2.5-Decide` (340M, DeBERTa-v3-large, Apache 2.0)
- HuggingFace Space: `davanstrien/topic-feed-lab` (CPU, not fetched)

## What's real

### 1. Jev / Leia / Lia — System-1 typed-decision models
- Non-autoregressive. No text generation. Labels + calibrated probs, single forward pass.
- Leia (coder name for the Snake demo model): 10–18 ms per decision, ~1 GB VRAM, 60 decisions/sec on M3 Max.
- Emperor (CoderOne): sub-30 ms.
- These are **decision engines**, not chatbots. The YouTube examples are all *action-triggering* use cases:
  - Driving simulator: continuous steering/throttle/brake control
  - Trolley problem: 100 trials, 99% lever-pull every time
  - Drawing app: "draw blue square here" → places square immediately
  - Slop detector: watches X posts as you scroll, labels "slop or not-slop"
  - **SEO internal linking**: 586 pages → 584 links placed + 139 rejected, 45 sec, $21

### 2. GLiNER2.5-Decide — 340M schema-driven classifier
Key API patterns noul should steal:

| Pattern | What it does | noul application |
|---|---|---|
| **Multi-label in one call** | Several heads scored simultaneously: `intent + urgency + route` | noul can check answerability + urgency + handoff in one call |
| **Ordinal scales** | Pass `"0"…"10"` as candidate labels — model returns a rank | noul could return confidence tiers: `definite / maybe / not` |
| **Labels with descriptions** | Each label carries a human-written description | noul packs can specify what "answerable" means contextually |
| **340M, CPU-friendly** | DeBERTa-v3-large encoder, runs on CPU through `gliner2` | noul could offer GLiNER2.5-Decide as a no-GPU engine option |

### 3. Benchmark: GLiNER2.5-Decide 60.2% vs alternatives

| Model | Size | Score |
|---|---|---|
| **GLiNER2.5-Decide** | 340M | **60.2%** |
| GLiNER2 XL | 1B | 59.6% |
| JevK5 | ? | 57.6% |
| SemIf (Qwen3.5-4B) | 4B | 56.4% |
| GLiFormer large-v1 | ? | 49.0% |
| ~~Laya Router~~ | ? | ~~46.6%~~ |

Note: "Laya Router" appears in the GLiNER benchmark table. This may or may not be related to the user's Laya model family. Either way, a 340M model beating 1B and 4B models confirms that **specialist encoders > big LLMs** for typed decisions.

## What this means for noul

### Opportunity 1: Multi-label abstention packs
noul's current pack is binary: `ANSWERABLE / NOT_ANSWERABLE`. GLiNER shows we can score multiple heads:
- `answerable` + `confidence_tier` + `needs_human`

A pack like `{answerable: yes, confidence_tier: high, needs_human: no}` is strictly more useful for routing than a single binary.

### Opportunity 2: GLiNER2.5-Decide as a no-GPU engine
- 340M params, Apache 2.0, CPU-capable
- `noul doctor --engine gliner` for environments without CUDA
- Kev stays the calibrated gate (ECE 0.089); GLiNER is a fallback

### Opportunity 3: Batch mode (the 586-page problem)
The SEO use case is the strongest signal: **thousands of tiny yes/no decisions** is exactly what noul's abstention gate is for.

```
noul batch --input questions.csv --doc document.md
# reads (question, doc_id) pairs, outputs decision + probability per row
```

### Opportunity 4: Ordinal confidence tiers
Instead of a raw probability, return:
- `definite_yes` (noul ≥ 0.9)
- `maybe` (0.5 ≤ noul < 0.9)
- `definite_no` (noul < 0.5)

This is what the drawing-app / slop-detector examples need: "this post is definitely slop" vs "I'm unsure."

## Honest limitations still hold
- Multi-label: noul's current API returns one label. Adding heads is an API change.
- GLiNER engine: requires `pip install gliner2` — adds a dependency. Can be optional.
- Batch mode: straightforward, minimal risk.
- Ordinal tiers: also straightforward, minimal risk.

## DeepOpen / System 1 Agents findings (2026-09-25)

Verified sources:
- DeepOpen: https://github.com/deepopen-com/deepopen (1,020⭐, 110 forks, created 09-21, Apache 2.0)
- System1 Agents: https://github.com/ThinkFlowLab/system1-agents
- DeepOpen README (raw): non-autoregressive System 1 engine built on Laya; 3 checkpoints + Router; RLCD training; 33ms single / 7.2ms batched on T4; 100+ languages; 3 question types (choice, score, noul); benchmarks CLINC150 / Banking77 / HWU64
- System1 Agents README (raw): openJiuwen agent core; model slot = `jev`/`laya`/`cua`; 6× faster / 25× cheaper than chat; browser/computer/desktop tasks

### What DeepOpen is (and isn't)
- DeepOpen IS the production Laya engine. NOT a competitor.
- DeepOpen already has a `noul` question type (one of 3: choice/score/noul).
- DeepOpen's `noul` is uncalibrated (no ECE reported). noul (Kev) provides the calibrated gate.
- DeepOpen's architecture is a reference: Router + encoder + multi-label heads.

### Hypotheses / possibilities
H1 (COMPLEMENTARY): DeepOpen routes (33ms) → noul gates (90ms, calibrated) → generate only if ANSWERABLE. Total < 130ms.
H2 (BATCH): DeepOpen's batch speed (7.2ms/q) ↔ noul batch mode (new, unmeasured). Use DeepOpen benchmarks as noul packs.
H3 (MULTI-LABEL): DeepOpen's multi-dim classification → noul multi-head packs (answerable + urgency + route).
H4 (AGENT): System1 Agents framework needs both a decision model (DeepOpen) AND a gate (noul). This is the reference architecture.
H5 (STACK): DeepOpen + noul + Ollama = complete local stack with documented reference scripts.

### Action taken in session
- engine.py: added `deepopen` to ENGINES (url, model, notes)
- batch.py + cli.py: batch mode + ordinal tiers (`definite_yes`/`maybe`/`definite_no`)
- RESEARCH.md: this section
- README.md: usage examples with Ollama / Open WebUI / n8n (patched into README)

## Recommendation
Implement batch mode + ordinal tiers (DONE this session).
Position noul explicitly as the complementary gate to DeepOpen/DeepOpen-class engines.
Add DeepOpen benchmarks (CLINC150, Banking77) as noul pack templates for credibility.

