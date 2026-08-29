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

This repository is at a reopened Gate A design/review checkpoint for the micro1
Agentic Workflows Hackathon. The earlier 200-event package and Gate B contract
repair are preserved as historical draft/execution evidence, but are not current
approval of the revised Gate A proposal. The active review target is a single
60–100-event long-chat benchmark with zero-maintenance queries and a defined
maintenance-burden metric. No new benchmark, evaluator, baseline, or
application implementation should begin before human approval.

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
| `app/` | Reserved for a future product implementation |
| `data/` | Reserved locations for synthetic and raw source data |
| `eval/` | Deterministic development scorer and reproducible result artifacts |
| `trajectories/` | Coding and runtime agent trace artifacts |
| `scripts/` | Reserved location for future reproducibility tooling |

## Scope of this phase

The prior phase froze a public development benchmark and measured a fair
baseline, but the current human review reopens Gate A before any new freeze.
The active task is design-only. It does not implement the Blackhole
application, add production infrastructure, expose evaluator-owned holdout
ground truth, or add a Claude adapter. The prior baseline remains a benchmark
treatment, not product memory or application code.

Read [AGENTS.md](AGENTS.md) before changing the repository. The design context is
in [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md),
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and
[docs/EVALUATION.md](docs/EVALUATION.md).
