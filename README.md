# Blackhole

**A zero-organization life inbox.**

Blackhole is a low-friction place to capture fragmented everyday information:
short text, receipts, documents, tasks, subscriptions, contracts, and financial
observations. The repository path remains unchanged; the product framing is now
Blackhole.

## Problem framing

Traditional productivity systems often make capture itself into a second task. A
person wants to get something out of their head quickly, but a tool may first
require choosing a database, folder, project, category, due date, priority, tags,
or properties. That organizational overhead can be especially costly for people
with high executive-function friction, attention overload, forgetfulness, or low
tolerance for setup. ADHD is a strong example of this user need; Blackhole makes
no claims to diagnose, treat, or improve any medical condition and is not medical
assistance.

Blackhole's principle is:

> **CAPTURE NOW. ORGANIZE LATER.**

The user should be able to submit a fragment without classifying it. Later, the
system can extract facts, link entities, maintain state, identify obligations and
deadlines, detect changes and duplicates, calculate deterministic financial
summaries, and surface only items that need attention.

## UX principles

- **SILENT BY DEFAULT:** normal capture should ideally be `input → saved`.
  Capturing information should not require maintaining a conversation.
- **INTERRUPT ONLY WHEN USEFUL:** proactive interruption is reserved for
  deadlines, reminders, material unresolved conflicts, required decisions, and
  important changes.
- **OBSERVE, DO NOT JUDGE:** surface factual observations without moralizing about
  behavior. Advice or interpretation is provided when explicitly requested.

## Status

This repository has completed the benchmark-and-baseline phase for the micro1
Agentic Workflows Hackathon. Gate A's 200-event development package is frozen,
and Gate B's response-contract repair is valid. The official `baseline-v1`
result remains the accepted baseline at `LQA-0M=0.3014914553`; the prior
`baseline-v0` result is preserved as invalid-contract evidence, not an official
semantic baseline; the independent v2 contract smoke test passes and the
corrected official baseline is recorded separately. The current authorized phase
is advanced Blackhole application experimentation. Production infrastructure,
Claude integration, and holdout ground truth remain out of scope.

Experiment 001 has now completed its authorized 200-event milestone with a
rebuildable SQLite state slice and deterministic public projections. Its
non-official result is recorded in the experiment trajectory and changelog; it
does not replace the frozen baseline or benchmark.

## Design principles

- Capture requires minimal cognitive effort and no upfront taxonomy.
- Raw source material is immutable and remains available as evidence.
- Derived state is versioned and rebuildable from immutable sources.
- Known, inferred, and unknown information remain distinguishable.
- Missing data is not silently treated as zero, false, or complete.
- Deterministic calculations belong in code or SQL, not in an LLM response.
- No consequential action happens without explicit user approval.
- Attention is a derived projection, not a replacement for evidence.
- Benchmark holdout ground truth is evaluator-owned and protected from
  implementation agents.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/` | Product, architecture, decision, evaluation, and reproduction documents |
| `prompts/` | Versioned runtime and coding prompt artifacts |
| `benchmark/` | Calibration, development, and evaluator-controlled benchmark boundaries |
| `baseline/` | Fair provider-baseline harness; not the Blackhole application |
| `app/` | Scoped advanced application experiments; no production app yet |
| `data/` | Reserved locations for synthetic and raw source data |
| `eval/` | Deterministic development scorer and reproducible result artifacts |
| `trajectories/` | Coding and runtime agent trace artifacts |
| `scripts/` | Reserved location for future reproducibility tooling |

## Scope of the completed benchmark phase

The completed benchmark phase froze the public development benchmark and
deterministic scorer, repaired and measured the fair baseline contract, and
recorded one corrected baseline run. The current advanced phase contains the
scoped Experiment 001 state-projection slice, but still has no production
infrastructure, evaluator-owned holdout access, or Claude adapter. The baseline
remains a benchmark treatment, not product memory.

Read [AGENTS.md](AGENTS.md) before changing the repository. The design context is
in [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md),
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and
[docs/EVALUATION.md](docs/EVALUATION.md).
