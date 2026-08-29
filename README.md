# Blackhole

Blackhole is a zero-organization personal inbox: capture a fragment now and
let structured state, history, and attention emerge later.

It is a micro1 Agentic Workflows Hackathon submission focused on one difficult
product question: can an agent maintain useful personal state as everyday
information changes over time without making capture another organizational
task?

## Try the local demo

The repository contains a small, deterministic, mobile-first web demo. It is
deliberately local and dependency-light:

```text
python scripts/seed_demo.py --reset
python -m app.web_app --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080`. The demo has four views:

- **Capture** — one universal text box, with an optional small text-file import;
  the normal response is `Saved.`
- **Attention** — an open deadline and an approval-gated proposed action;
- **Memory** — current subscriptions, historical price, task reassignment and
  cancellation, observed costs, missing periods, duplicates, and unknown data;
- **Ask Blackhole** — a handful of deterministic structured lookups over the
  same state.

The seed is synthetic and separate from the frozen benchmark. It contains 14
raw events, 27 semantic observations, and four relationships. A capture added
through the UI is stored as an immutable raw event with `semantic_status:
pending`; this demo does not silently call a model or execute an action.

## Product idea

People routinely accumulate short notes, receipts, documents, tasks,
subscriptions, contracts, and financial observations without wanting to choose
a folder, project, tag, or schema first. Blackhole accepts those fragments with
minimal friction and later aims to:

- extract facts and classifications;
- link observations to existing entities;
- preserve current state and longitudinal history;
- distinguish known, inferred, and unknown information;
- create tasks, obligations, and deadlines;
- detect duplicates, corrections, and material changes;
- aggregate deterministic financial observations; and
- surface only items that require attention.

The design is intentionally quiet: `capture → saved` is the default interaction.
Attention is reserved for deadlines, unresolved information, important changes,
and decisions that need explicit approval.

## Non-negotiable boundaries

- Raw source records are immutable and remain available as evidence.
- Derived state is versioned and rebuildable from raw inputs and transformation
  rules.
- Missing information stays unknown; it never becomes zero, false, empty, or
  complete by default.
- Arithmetic, date logic, duplicate checks, comparisons, and financial totals
  belong to deterministic code or SQL, not an LLM response.
- Sending, paying, cancelling, signing, changing an account, deleting evidence,
  or another consequential action requires explicit user approval.
- Holdout expected outputs remain evaluator-owned and outside the implementation
  agent's trust boundary.

## What is implemented

The current advanced application slice is intentionally scoped:

- `app/state_store.py` — append-only SQLite raw events, payload hashes,
  structured observations and relationships, and rebuildable projections;
- `app/response_projector.py` — generic, query-scoped deterministic projections;
- `app/provider.py` and `app/advanced_runner.py` — the subscription-first
  local Codex CLI boundary for separately authorized semantic runs;
- `app/demo.py` and `app/web_app.py` — the local seeded demo and its small HTTP
  surface;
- `app/web/` — the mobile-first static interface; and
- `scripts/seed_demo.py` — reproducible demo reset/seed.

This is not production infrastructure. There is no hosted service, account
system, OCR pipeline, external-action executor, Claude adapter, or holdout
package in this repository. The web demo's provider pill reports only whether a
`codex` executable is discoverable; it never reads or persists authentication
material.

## Benchmark status

Gate A is frozen at one public 200-event development scenario with checkpoints
at 50, 100, 150, and 200. Gate B's `response-contract-v2` repair is valid. The
official fair comparator remains `baseline-v1` at `LQA-0M=0.3014914553` with
`DSCR=277`. The latest kept advanced replay is Experiment 003 at
`LQA-0M=0.8157180034` with `DSCR=45`; it preserves the same frozen benchmark
and has no safety or source-integrity failure. Experiment 002 remains preserved
as the preceding kept replay at `LQA-0M=0.7492295899` with `DSCR=72`.

Those are development measurements, not a claim of production readiness or
holdout superiority. The public benchmark, calibration evidence, baseline
artifacts, and evaluator behavior are preserved. Experiment 003 tested bounded
raw-capture relation reconciliation; its current kept result is
`LQA-0M=0.8157180034` with `DSCR=45`.
The treatment remains experimental and does not expose holdout material or
perform provider-assisted resolution.

See [docs/EVALUATION.md](docs/EVALUATION.md) for the contract and metrics,
[docs/REPRODUCTION.md](docs/REPRODUCTION.md) for judge-facing commands,
[`eval/results/experiment-003-retrieval-full-v3.json`](eval/results/experiment-003-retrieval-full-v3.json)
for the current advanced replay, and
[`eval/results/final-comparison-v1.json`](eval/results/final-comparison-v1.json)
for the preceding product-phase baseline comparison snapshot.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/` | Product, architecture, decisions, evaluation, reproduction, and video notes |
| `prompts/` | Versioned runtime and coding prompt artifacts |
| `benchmark/` | Calibration and public development benchmark boundaries |
| `baseline/` | Fair stateless provider-baseline harness |
| `app/` | Scoped Blackhole state slice and local demo |
| `data/synthetic/` | Committed synthetic demo inputs; no personal data |
| `data/raw/` | Reserved raw-source location |
| `eval/` | Deterministic scorer, tests, and result artifacts |
| `trajectories/` | Coding and representative runtime evidence |
| `scripts/` | Reproduction helpers |

## Development checks

From the repository root:

```text
python -m unittest discover -s . -p "test_*.py" -v
python benchmark/dev/generate_benchmark.py --check
python eval/contract_smoke.py
python -m compileall -q app eval scripts
```

Read [AGENTS.md](AGENTS.md) before making changes. The product contract is in
[docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md), the trust boundaries are in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and the short demo narrative is
in [docs/VIDEO_SCRIPT.md](docs/VIDEO_SCRIPT.md).
