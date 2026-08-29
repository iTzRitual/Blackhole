# Retrospective task summary

> This document is a retrospective summary of the human-authorized scaffold
> task. It is not a verbatim historical prompt and does not claim to reproduce
> an original agent transcript.

The human authorized the next post-freeze product-runtime milestone after the
deferred-ingestion work was completed and kept at commit
`0c60da9d78448be9aa4ce277ae788a67525a8f01`. The frozen development benchmark
and its evidence must remain unchanged: the public scenario stays at 200
events with checkpoints at 50, 100, 150, and 200; `response-contract-v2`, the
official `baseline-v1` result, the evaluator, and the calibration evidence are
protected. The latest kept reference is Experiment 005 with LQA-0M
`0.8695006212469447` and DSCR `40`. No E006 benchmark-optimization work is
authorized.

Build the non-visual Blackhole Host foundation in the current primary backend
worktree. A separate `ui/mobile-pwa` worktree is actively changing the PWA;
do not switch worktrees or modify `app/web/**`, `app/web_app.py`, frontend/PWA
assets, UI trajectories, `docs/VIDEO_SCRIPT.md`, or
`docs/VIDEO_SHOT_LIST.md`.

The intended boundary is:

```text
Client -> future Host API -> HostRuntime
                         -> IngestionEngine -> StateStore
                                          -> semantic provider -> Codex CLI
```

Codex CLI is only a semantic provider. Blackhole owns durable state, SQLite,
deferred ingestion, processing lifecycle, and runtime configuration. Do not
use a persistent Codex thread as Blackhole memory, and do not build the final
HTTP/PWA integration in this task.

Introduce a small reusable `HostRuntime` facade that wraps and reuses the
existing `IngestionEngine` rather than duplicating extraction, completeness,
relation recovery, duplicate-evidence, or projection logic. It should own or
coordinate runtime configuration, database location, `StateStore`, optional
`CodexCLIProvider`, provider readiness, and processing status. Its Python-level
boundary should include `status()`, `capture(...)`, `processing_status(...)`,
`process_pending(...)`, `retry_failed(...)`, and `ensure_state_fresh()`, plus
clean state/query/view access where that can be exposed without duplicated
logic.

Add safe, machine-readable host/provider status. It may report host version,
database location, provider type, installation/version/authentication/readiness
state, and pending/failed processing counts, but must never expose tokens,
credential paths, cookies, API keys, provider secrets, or auth-file contents.
Discover the actually installed Codex CLI capability using safe local
commands (PATH, version, help, and login status as appropriate), without
reading credential material, logging in, or making an expensive semantic
probe. Distinguish missing, installed-but-unauthenticated, ready, and error
states; binary existence alone is not readiness. Normal product configuration
must remain separate from frozen benchmark constants. Use a small validated,
versioned non-sensitive configuration boundary for provider, model, reasoning,
timeout, batch size, and related runtime settings.

Create an explicit `BLACKHOLE_HOME` application-data boundary with a simple
cross-platform default such as `~/.blackhole/`. The host may own `config.json`,
`blackhole.db`, and safe runtime metadata there, but never provider
credentials, Codex auth material, or benchmark ground truth. Tests must use
temporary directories. Add first-run CLI/backend-only initialization via
`python -m app.host init`; it must initialize the data directory and database
even when Codex is missing. Capture must work without an AI provider, retain
the immutable raw event, and mark processing pending.

Provide one stdlib backend CLI with `init`, `status`, `process`, `retry`, and
`doctor` (or an equivalent small set). Ordinary status/doctor checks must not
run semantic inference. Processing must delegate to `IngestionEngine`; provider
failures must produce concise host-level retryable status without exposing raw
provider stderr. Do not add a generic shell/exec API. Consequential actions
remain proposals requiring explicit approval.

Do not implement networking in this milestone: no LAN HTTP server, pairing,
device tokens, mDNS, public exposure, HTTPS, remote access, tunnel, or cloud
relay. Document the future transport mapping only (status, capture, process or
ensure-fresh, processing status, state/memory, attention, and query).

Add neutral tests for initialization, `BLACKHOLE_HOME`, provider discovery and
absence, safe serialization/no secrets, capture without a provider, fake
provider processing, idempotency, retry, config persistence, and database
persistence across restart. Real Codex is not required for the main suite.
Cheap local Codex version/help/login-status checks are allowed, but do not run
semantic Luna inference, a benchmark run, or an expensive experiment.

After implementation, run the normal test suite, host tests, compile checks,
benchmark generator/contract smoke checks as applicable, the latest E005
deterministic replay in new output paths, and protected hash/content checks.
The E005 reference must remain exactly LQA-0M `0.8695006212469447` and DSCR
`40`; this is regression validation, not a new benchmark experiment. Update
the architecture, decision, and reproduction documentation, create this
trajectory, make one coherent commit, and stop without UI, networking,
pairing, benchmark generalization, or E006 work.
