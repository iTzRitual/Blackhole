# Blackhole Host foundation

## Status

Complete. This trajectory records the backend/product-runtime milestone
authorized after the deferred-ingestion milestone. No authentic session
transcript is available, so no transcript file is fabricated.

## Goal

Create the non-visual Blackhole Host foundation: a local application-data
boundary, validated runtime configuration, safe Codex CLI capability
discovery, a reusable `HostRuntime` facade over the existing deferred
`IngestionEngine`, and a small backend CLI. Preserve the frozen benchmark and
keep capture usable without a semantic provider.

## Initial hypothesis

Blackhole can provide a safe first-run and deferred-processing boundary by
keeping durable state in its own SQLite-backed home, treating Codex CLI as an
optional externally authenticated semantic provider, and exposing only
Blackhole domain operations to future clients.

## Agent/tool used

Codex in the shared local repository worktree. Work stayed on the primary
backend branch and did not switch to or modify the concurrent UI worktree.

## Important implementation decisions

- Added `RuntimeConfig` and an explicit `BLACKHOLE_HOME` boundary. The default
  home is `~/.blackhole/`; the persisted config is versioned, validated, and
  limited to provider/model/reasoning/timeout/batch/database preferences.
- Added safe Codex discovery using the observed local CLI commands
  `codex --version` and `codex login status`. The implementation reports
  `MISSING`, `INSTALLED_NOT_AUTHENTICATED`, `READY`, or `ERROR` and never reads
  credential files, cookies, tokens, or auth paths.
- Added `HostRuntime` as orchestration over the existing `IngestionEngine` and
  `StateStore`. It exposes status, capture, processing status, processing,
  retry, freshness, snapshot, and state operations without duplicating the
  semantic pipeline.
- Added a backend-only `python -m app.host` CLI with `init`, `status`,
  `process`, `retry`, and `doctor`. Initialization creates SQLite without a
  provider; capture remains raw-only and provider failures are retryable.
- Added a safe Host provider wrapper so provider exception text and raw stderr
  do not cross the Host boundary. No generic shell/exec operation or
  consequential action executor was added.
- Extended the existing provider adapter with an explicit model parameter
  while retaining the frozen benchmark defaults and behavior. Product runtime
  configuration defaults to high reasoning; official benchmark configuration
  remains separate and unchanged.
- Documented the ownership boundary, security invariants, and future transport
  mapping in `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` (D-033), and
  `docs/REPRODUCTION.md`.

## Tools/actions used

- Read the task attachment and current `AGENTS.md`/repository state.
- Inspected the existing deferred-ingestion engine, StateStore, provider
  boundary, public contract, and the installed Codex help/login surface.
- Created the coding trajectory before implementation.
- Edited files with `apply_patch`.
- Ran neutral host tests, the full unittest suite, compile checks, benchmark
  generator check, contract smoke, and a deterministic public E005 regression.
- Calculated SHA-256 hashes for protected benchmark, response-contract,
  baseline, and E005 artifacts.

## Failures, retries, and changed approaches

The first host-test run exposed that `IngestionEngine` aggregates processing
errors in an `errors` list rather than a top-level `error`. The Host facade was
adjusted to expose a concise first `error` for CLI/API callers while retaining
the aggregate list. A second host-test run passed. The discovery/configuration
boundary was then tightened to sanitize injected provider-status values,
refresh cheap provider readiness before processing, and reject more sensitive
configuration key shapes.

One temporary CLI-check home was created outside the repository. The runtime
check succeeded; the environment rejected cleanup commands for that temporary
path, which did not affect the repository tree or test results.

## Human feedback and checkpoints

- The task was authorized after the deferred-ingestion milestone was marked
  KEEP at `0c60da9d78448be9aa4ce277ae788a67525a8f01`.
- The human-required boundaries were preserved: Gate A remains frozen, no E006
  work was started, the UI worktree stayed out of scope, and no HTTP/networking,
  pairing, production infrastructure, benchmark case, holdout, or baseline
  implementation was added.

## Evaluation performed

- `python -m unittest discover -s . -p "test_*.py" -q`: 70 tests passed.
- `python -m unittest app.tests.test_host -q`: 11 host tests passed.
- `python -m compileall -q app eval scripts`: passed.
- `python benchmark/dev/generate_benchmark.py --check`: 200 events and 4
  checkpoints checked.
- `python eval/contract_smoke.py`: non-scored smoke passed with semantic score
  1.0 and malformed output rejected.
- Fresh deterministic E005 replay and scoring in
  `trajectories/runtime/018-host-foundation-e005-regression/` and
  `eval/results/host-foundation-e005-regression*.json`: LQA-0M
  `0.8695006212469447`, DSCR `40`, zero provider calls/tokens. The scored
  regression result is byte-identical to
  `eval/results/experiment-005-duplicate-evidence-full.json`.
- Cheap local CLI check: `codex-cli 0.150.0-alpha.12.2`, login status
  authenticated, no semantic inference invoked.
- Protected SHA-256 values remained unchanged for the public scenario, public
  expected output, `response-contract-v2`, official `baseline-v1`, and the
  kept E005 result.

## Result

The non-visual Blackhole Host foundation is implemented and documented. It
supports first-run initialization and raw capture without Codex, delegates
semantic processing to the existing ingestion pipeline when a provider is
ready, and keeps the provider/authentication and future transport boundaries
explicit.

## Regressions or unresolved issues

No benchmark, evaluator, baseline, calibration, UI, or existing experiment
regression was observed. The host does not yet implement HTTP transport,
pairing, networking, remote access, or a production deployment boundary by
design. Codex model availability is reported as configured rather than probed
expensively; authentication remains an external Codex CLI responsibility.

## Final decision

KEEP as the authorized backend/product-runtime foundation. This is not a new
benchmark experiment and does not add an improvement-changelog entry.

## Scope constraints

- Do not modify the PWA worktree or UI files.
- Do not modify benchmark cases, expected values, response-contract-v2,
  evaluator behavior, baseline-v1, calibration evidence, or prior experiment
  results.
- Do not implement HTTP transport, pairing, networking, production
  infrastructure, a generic shell API, or E006.

## Decisions and evidence

## Related git commits

- Starting deferred-ingestion milestone:
  `0c60da9d78448be9aa4ce277ae788a67525a8f01`
- Kept Experiment 005 reference:
  `46b60856e30b44f7898b6d4c723964bf2efed38f`
- This trajectory's single coherent Host Foundation commit is the commit
  created for this task and is reported in the handoff.
