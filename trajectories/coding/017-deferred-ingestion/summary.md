# Trajectory 017 — deferred end-to-end ingestion

## Status

In progress. This is a backend/product-runtime milestone authorized after the
final E005 benchmark-optimization experiment; it is not Experiment 006.

## Goal

Extract a reusable, generic deferred-ingestion service from the kept Blackhole
architecture. Captures must be saved synchronously as immutable raw events with
derived pending processing state; semantic work must run later through the
existing extraction, completeness, relation-recovery, duplicate-consolidation,
and rebuildable SQLite projection boundaries.

## Agent/tool used

Codex in the shared local backend worktree using PowerShell, `rg`,
`apply_patch`, Python stdlib tooling, the existing SQLite state store, provider
boundary, runner, and tests. No UI worktree, holdout material, or provider
credentials are in scope.

## Product rationale

Blackhole's capture path is intentionally `CAPTURE → SAVED → END INTERACTION`.
Users should not wait for semantic classification or model reasoning. The
backend must make captured information useful later when an Ask-like caller
requires fresh structured state.

## Architecture before

- `StateStore` owns immutable `raw_events`, semantic observations,
  relationships, projection runs, current facts, and the E005 duplicate
  component projection.
- `app/advanced_runner.py` coordinates chronological benchmark/replay
  extraction and the kept completeness, relation-recovery, and duplicate
  projection options.
- `app/provider.py` exposes the subscription-first local Codex CLI boundary.
- `app/demo.py` has a raw-only capture helper, but no reusable production-facing
  pending queue or deferred ingestion service.
- There is no separate authoritative derived processing-status table.

## Initial hypothesis

The smallest safe runtime boundary is a generic `IngestionEngine` that owns
capture append, derived processing state, bounded chronological processing,
retry, and ask-time freshness while delegating semantic work to the existing
provider and projection components. Stable event-scoped transformation
identities should make repeated processing idempotent without mutating raw
events or requiring benchmark expected output.

## Scope and invariants

Preserve the frozen 200-event benchmark, response-contract-v2, evaluator,
baseline-v1, calibration evidence, and all prior experiment artifacts. Do not
modify `app/web/**`, UI assets, benchmark cases, expected output, query bundle,
or add Claude/background scheduling. Use neutral synthetic integration data
outside `benchmark/dev`; never execute consequential actions.

## Planned validation

Add a fake-provider integration test covering immediate raw-only capture,
chronological correction, unknown preservation, duplicate handling,
idempotency, failure/retry, and approval-boundary behavior. Run the existing
stdlib suites, benchmark generator check, contract smoke, compileall, the
frozen E005 deterministic replay, protected hash audit, and clean diff check.

No authentic coding-session transcript is available; none is being fabricated.

## Architecture after

- `app/semantic.py` is the shared public-contract normalization boundary used
  by both `advanced_runner` and the product runtime; semantic ingestion was not
  copied into a second implementation.
- `app/state_store.py` now persists a separate derived `processing_state` row
  for each raw event and exposes raw-event retrieval, status inspection,
  chronological queue selection, claim, success, and failure transitions.
- `app/ingestion_engine.py` provides `IngestionEngine.capture()`,
  `process_event()`, `process_pending()`, `retry_failed()`,
  `processing_status()`, `ensure_state_fresh()`, and `snapshot()`. Its default
  processing path composes the existing extraction normalization, deterministic
  completeness, retrieval relation recovery, E005 duplicate evidence, and
  rebuildable projection.
- `CodexCLIProvider` wraps the existing subscription-first `app.provider`
  boundary in a temporary workspace. A fake provider can be injected without
  changing production code.
- `app/process_pending.py` provides the explicit, UI-independent processing
  command. No background scheduler, Claude adapter, or frontend integration was
  added.

## Important implementation decisions

- Capture preserves the supplied payload and returns `Saved.` after only raw
  insertion plus derived pending-state insertion. It does not call a provider,
  add semantic observations, add relationships, or rebuild semantic state.
- `process_pending()` selects only pending rows, orders them by source sequence,
  and sends bounded batches to the provider. A failed batch marks its claimed
  rows failed and stops later batches; `retry_failed()` explicitly retries and
  will not bypass earlier unprocessed captures.
- Stable StateStore fingerprints, event-scoped transformation versions, and
  processed-state skipping provide idempotency. Reprocessing an already
  processed queue does not invoke the provider or add semantic effects.
- Provider errors are stored as bounded status descriptions, while the command
  prints only concise counts. Authentication remains owned by the local Codex
  CLI; no credential file or token is read or persisted.
- The engine requires only a public contract/configuration and raw SQLite state;
  it does not import expected output, evaluator code, score artifacts, or
  benchmark diagnostics.

## Tools/actions and failures

The implementation used PowerShell, `rg`, `apply_patch`, Python stdlib tests,
the existing SQLite store, the shared runner components, and the unchanged
deterministic evaluator. The first focused test run found an incorrect
`Protocol` import in the new module; it was fixed by importing `Protocol` from
`typing`. The next run found only a neutral fake-fixture prefix mismatch for
the PineVault example; the fixture was corrected and rerun. No benchmark or UI
file was changed during these fixes.

## Fake-provider integration result

The neutral fixture passed all seven deferred-ingestion tests. It demonstrated:

- raw-only capture without any provider;
- later extraction of a renewal date;
- chronological correction from 20 EUR to 25 EUR with both history values;
- `unknown/not_stated` preservation for an unverified month;
- a proposed payment with zero execution;
- two preserved raw duplicate captures projected as one occurrence;
- bounded chronological batches;
- failure state, preserved prior projection, retry, and later-queue ordering;
- a second `process_pending()` with zero provider calls and zero semantic
  effects; and
- an empty processing command that requires no provider.

The representative deterministic trace is recorded at
`trajectories/runtime/017-deferred-ingestion-fake/summary.md`.

## Frozen E005 regression

The required replay used new regression-only paths and the unchanged public
scenario, recorded semantic extraction, retrieval recovery, deterministic
completeness, duplicate-evidence projection, contract, and evaluator. It made
zero provider calls or tokens. The result matches the kept E005 reference
exactly: LQA-0M `0.8695006212469447`, DSCR `40`, and checkpoints
`0.8888888888888888 / 0.8713728401228401 / 0.8321654040404041 /
0.8855753519356461`. Existing E005 result artifacts were not overwritten.

## Optional real-provider smoke

Not run. The optional one-to-three-capture Codex smoke was not needed to
validate the service boundary; the mandatory deterministic fake-provider suite
passed, and the frozen regression replay used recorded public extraction.

## Validation and result

The full stdlib discovery suite passed: 59 tests. The seven deferred-ingestion
tests, benchmark generator `--check`, contract smoke, compilation, and
`git diff --check` all passed. The final frozen E005 regression replay passed
with LQA-0M `0.8695006212469447`, DSCR `40`, all four checkpoint scores
unchanged, zero provider calls/tokens, `hard_failure=false`, schema-valid
output, safety pass, and source-integrity valid. No baseline rerun, holdout
access, or prompt tuning occurred.

## Limitations and final decision

The MVP has no background scheduler, multi-user isolation, OCR/document
transport, provider capability negotiation beyond the existing CLI boundary, or
selective Ask-time processing. A stuck `processing` row requires operational
recovery that is not automated. Consequential actions remain proposals only.

**KEEP** the deferred ingestion architecture as a product/runtime milestone.
It is not Experiment 006 and does not change the frozen benchmark or official
baseline. No `IMPROVEMENT_CHANGELOG.md` benchmark entry was added because this
task did not introduce a benchmark optimization experiment.

## Related commit

Prior kept reference: E005 `46b60856e30b44f7898b6d4c723964bf2efed38f`.
The final deferred-ingestion commit is this trajectory's coherent commit; its
SHA is reported in the task handoff.
