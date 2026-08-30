# Blackhole

Blackhole is a zero-organization personal inbox: capture a fragment now and
let structured state, history, and attention emerge later.

It is a micro1 Agentic Workflows Hackathon submission focused on one difficult
product question: can an agent maintain useful personal state as everyday
information changes over time without making capture another organizational
task?

## Run the current local product

The current product is a mobile-first PWA served by the local Blackhole Host.
From the repository root, initialize the Host, run its safe readiness check,
and start the same-origin web transport:

```text
python -m app.host init
python -m app.host doctor
python -m app.web_app --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080`. The PWA has four views:

- **Capture** — one universal text box, with an optional small text-file import;
  the normal response is `Saved.`
- **Attention** — an open deadline and an approval-gated proposed action;
- **Memory** — current subscriptions, historical price, task reassignment and
  cancellation, observed costs, missing periods, duplicates, and unknown data;
- **Ask Blackhole** — a handful of deterministic structured lookups over the
  same state.

`app.host init` creates `config.json` and `blackhole.db` inside Blackhole Home
(`~/.blackhole/` by default). `doctor` reports safe Host, database, and Codex
readiness metadata without semantic inference. Capture appends immutable raw
evidence and returns `Saved.` even when Codex processing is unavailable. When
pending captures exist, Ask needs an authenticated local Codex CLI to make the
state fresh; a provider failure is reported without presenting stale state as
fresh.

Codex authentication is external to Blackhole. The current Host path does not
require `OPENAI_API_KEY`; it discovers and invokes an already-installed local
Codex CLI, while Blackhole never requests, reads, copies, exports, or persists
provider tokens.

### Optional trusted-LAN phone demonstration

To open the PWA from a phone on a trusted private network, opt in explicitly:

```text
python -m app.web_app \
  --host 0.0.0.0 \
  --port 8080 \
  --trusted-lan-demo
```

Warning: this is for a trusted private network only. It has no device
authentication, pairing, or TLS, and is not safe for the Internet. It is not
production remote access.

## Historical deterministic demo utility

The earlier seeded demo remains in the repository as reproducibility evidence
for the deterministic presentation and its historical trajectories. It is not
the current Host/PWA quickstart:

```text
python scripts/seed_demo.py --reset
```

By default this replaces the synthetic database at `data/demo/state.sqlite`.
The utility and `app/demo.py` are provider-free and retain the earlier 14-event
demo seed, but the current `app.web_app` does not auto-seed that database and
does not expose `POST /api/reset`. The integrated Host uses Blackhole Home and
its Host-owned `blackhole.db` instead.

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

## Capture now, understand later

The backend product loop is intentionally split:

```text
capture → immutable raw event → pending derived processing state → Saved.

later: process pending → structured Blackhole state → query / attention / memory
```

`IngestionEngine.capture()` validates and appends the source, records a pending
row outside the raw JSON, and returns without invoking a provider or rebuilding
semantic state. `process_pending()` later handles bounded chronological batches
through the existing semantic extraction, deterministic completeness, relation
recovery, duplicate-aware consolidation, and rebuildable SQLite projection.
`ensure_state_fresh()` is the backend boundary an Ask caller can use when it
needs current state. Failures are recorded per capture and can be retried; no
background scheduler is included in this legacy V1-compatible ingestion
engine. The separate Product V2 runtime adds a bounded daemon worker after
capture without changing that frozen V1 path.

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

The current integrated application slice is intentionally scoped:

- `app/host.py` — `HostRuntime` ownership boundary plus the backend commands
  `init`, `status`, `doctor`, `process`, and `retry`;
- `app/runtime_config.py` — validated non-sensitive runtime configuration,
  `BLACKHOLE_HOME`, and the default `~/.blackhole/` home;
- `app/codex_discovery.py` — safe PATH, version, and external-login readiness
  discovery for the local Codex CLI;
- `app/state_store.py` — append-only SQLite raw events, payload hashes,
  structured observations and relationships, rebuildable projections, and an
  opt-in duplicate-evidence component layer;
- `app/semantic.py` — shared public-contract normalization used by both the
  kept runner and deferred runtime;
- `app/ingestion_engine.py` — generic synchronous capture, derived processing
  status, bounded deferred ingestion, retry, and ask-time freshness boundary;
- `app/process_pending.py` — UI-independent processing command using the
  externally authenticated Codex CLI when pending work exists;
- `app/query_service.py` — bounded, database-free question projections over a
  Host snapshot;
- `app/completeness.py` — generic raw-source evidence scanning and conservative
  selective completion helpers;
- `app/response_projector.py` — generic, query-scoped deterministic projections;
- `app/provider.py` and `app/advanced_runner.py` — the subscription-first
  local Codex CLI boundary for separately authorized semantic runs;
- `app/product_v2.py` and `app/product_v2_store.py` — the isolated Product V2
  open-world runtime, durable queue, attachment blobs, Attention, Ask, and
  rebuildable projections;
- `app/product_process.py` — the UI-independent Product V2 init/status/process/
  retry command boundary;
- `app/web_app.py` — the same-origin Host HTTP transport and static PWA server;
- `app/web/` — the mobile-first PWA interface, manifest, and service worker; and
- `app/demo.py` and `scripts/seed_demo.py` — the historical deterministic demo
  utility, separate from the integrated Host database.

This is not production infrastructure. There is no hosted service, account
system, OCR pipeline, external-action executor, Claude adapter, or holdout
package in this repository. There is no pairing, device-authentication, TLS,
remote-access, or public-Internet deployment boundary. The Host reports only
safe provider readiness metadata and never reads or persists authentication
material.

## Post-evaluation Product V2 runtime foundation

The explicitly authorized Product V2 work is isolated on the
`product/v2-runtime` branch/worktree. It is a backend/API foundation, not a
claim that the PWA has been redesigned. V2 uses a separate `blackhole-v2.db`
and `blobs/` store inside Blackhole Home, so the frozen V1 `blackhole.db`,
benchmark, evaluator, baseline, and recorded results remain unchanged.

V2 adds immediate text/attachment capture, durable chronological processing
with lease recovery and retry, generic open-world memory, deterministic
Attention and arithmetic/date paths, bounded natural Ask retrieval, and
append-only semantic retraction. The explicit routes are:

```text
POST /api/v2/capture
GET  /api/v2/state
GET  /api/v2/processing
POST /api/v2/process
POST /api/v2/retry
POST /api/v2/ask
POST /api/v2/retract
POST /api/v2/attention/status
GET  /api/v2/attachments/<sha256>
```

The read-only V2 GET routes do not start provider work; semantic Ask is
POST-only. The UI-independent command boundary is:

```text
python -m app.product_process --home <blackhole-home> init
python -m app.product_process --home <blackhole-home> status
python -m app.product_process --home <blackhole-home> process
python -m app.product_process --home <blackhole-home> retry
```

The product default is the configured `gpt-5.6-luna` model at `high`
reasoning, distinct from the frozen benchmark's `max` configuration.

V2 deterministic tests use fake providers and temporary Homes. No live
provider call, benchmark expected output, holdout material, OCR guarantee,
production hosting, Claude adapter, or consequential action execution is part
of this foundation.

## Benchmark status

Gate A is frozen at one public 200-event development scenario with checkpoints
at 50, 100, 150, and 200. Gate B's `response-contract-v2` repair is valid. The
official fair comparator remains `baseline-v1` at `LQA-0M=0.3014914553` with
`DSCR=277`. The latest kept advanced replay is Experiment 005 at
`LQA-0M=0.8695006212` with `DSCR=40`; it preserves the same frozen benchmark
and has no safety or source-integrity failure. Experiment 004 remains preserved
as the preceding kept replay at `LQA-0M=0.8630770101` with `DSCR=41`, and
Experiment 003 remains preserved at `LQA-0M=0.8157180034` with `DSCR=45`.

Those are development measurements, not a claim of production readiness or
holdout superiority. The public benchmark, calibration evidence, baseline
artifacts, and evaluator behavior are preserved. Experiment 005 tested
duplicate-aware evidence consolidation over the existing raw/derived boundary;
its kept replay made zero provider calls. The treatment remains experimental
and does not expose holdout material or perform provider-assisted resolution.

`implementation-freeze-v1` remains the evaluated frozen version. The final
Generalization V1R1 result is now public in
[docs/GENERALIZATION_V1R1_REPORT.md](docs/GENERALIZATION_V1R1_REPORT.md); the
blind baseline and Blackhole candidates were sealed before oracle scoring. It
is a post-freeze shadow/generalization set of three fresh synthetic worlds, not
an organizer-provided official holdout and not evidence of statistical
significance. The large DEV improvement did not transfer strongly to unseen
worlds. Subsequent Product v2 work is post-evaluation product development,
not retroactive tuning of the reported V1R1 score.

See [docs/EVALUATION.md](docs/EVALUATION.md) for the contract and metrics,
[docs/REPRODUCTION.md](docs/REPRODUCTION.md) for judge-facing commands,
[`eval/results/experiment-005-duplicate-evidence-full.json`](eval/results/experiment-005-duplicate-evidence-full.json)
for the current advanced replay, and
[`eval/results/final-comparison-v1.json`](eval/results/final-comparison-v1.json)
for the historical/superseded product-phase baseline comparison snapshot, not
the current final comparison.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/` | Product, architecture, decisions, evaluation, reproduction, and video notes |
| `prompts/` | Versioned runtime and coding prompt artifacts |
| `benchmark/` | Calibration and public development benchmark boundaries |
| `baseline/` | Fair stateless provider-baseline harness |
| `app/` | Host-owned runtime, deferred ingestion service, same-origin transport, PWA, and historical demo utility |
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
