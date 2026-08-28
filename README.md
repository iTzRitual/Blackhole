# Life Inbox

Life Inbox is a zero-organization personal inbox for fragmented everyday information. A person can capture a short note, receipt, document, task, subscription, contract, or financial observation without first deciding where it belongs.

The system is intended to do the organizing later: extract facts, classify inputs, link them to existing entities, maintain state over time, identify obligations and deadlines, detect duplicates and changes, aggregate deterministic financial data, and surface only information that needs attention.

## Status

This repository is currently a documentation-only scaffold for the micro1 Agentic Workflows Hackathon. Product implementation, benchmark data, and evaluation code are intentionally not present yet.

## Design principles

- Capture should require minimal cognitive effort and no upfront taxonomy.
- Raw source material is immutable and remains available as evidence.
- Derived state is versioned and rebuildable from immutable sources.
- Known, inferred, and unknown information remain distinguishable.
- Missing data is not silently treated as zero, false, or complete.
- Deterministic calculations belong in code or SQL, not in an LLM response.
- No consequential action happens without explicit user approval.
- Benchmark holdout ground truth is evaluator-owned and protected from implementation agents.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/` | Product, architecture, decision, evaluation, and reproduction documents |
| `prompts/` | Versioned runtime and coding prompt placeholders |
| `benchmark/` | Development and evaluator-controlled benchmark boundaries |
| `baseline/` | Reserved location for baseline definitions and artifacts |
| `app/` | Reserved for a future product implementation |
| `data/` | Reserved locations for synthetic and raw source data |
| `eval/` | Reserved location for evaluation outputs |
| `trajectories/` | Coding and runtime agent trace artifacts |
| `scripts/` | Reserved location for reproducibility and evaluation tooling |

## Scope of this phase

This phase establishes shared language, safety invariants, evaluation boundaries, and reproducibility expectations. It does not define an application schema or commit to a particular framework, database, model provider, or user interface.

Read [AGENTS.md](AGENTS.md) before changing the repository. The design context is in [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/EVALUATION.md](docs/EVALUATION.md).
