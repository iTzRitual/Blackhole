# Product V2 human-dogfood P0/P1 repair

Status: **PARTIAL**. The deterministic normal-launch regression passes. The
normal `python -m app.web_app` live Codex smoke reached the app and returned
captures immediately, but both authorized live provider attempts failed before
semantic state was produced. No live Ask was issued after those failures, and
no semantic success is claimed.

## Scope and protected boundaries

This work was performed only on the `product/v2-dogfood-fixes` branch, based
on the Product V2 integration commit recorded in the coding trajectory. The
integration worktree, master, the frozen V1 runtime and benchmark, evaluator,
baseline evidence, calibration evidence, other Product V2 worktrees, and
holdout material were not modified or used. No G01–G03 tuning, provider token,
production infrastructure, Claude adapter, or consequential action was added.

The human-dogfood Home was inspected read-only. Its before/after hashes and
the sanitized database observations are recorded in
`trajectories/coding/035-product-v2-human-dogfood-p0-fixes/forensic-evidence.json`.

## Findings and changes

### P0-1 — one Product V2 store and queue

All Product V2 entry points now use the resolved
`<BLACKHOLE_HOME>/blackhole-v2.db` through `product_database_path()`. Host
status opens the Product V2 store before reporting counts, so its queue agrees
with `app.product_process status`. The legacy `<BLACKHOLE_HOME>/blackhole.db`
remains the V1 compatibility store and is not the Product V2 queue.

### P0-2 — actual PWA V2 route and shell update

The shipped client continues to use only `/api/v2/*` for normal Product V2
Capture, state, and Ask. The shell cache is versioned to `v7`; shell asset
URLs are versioned, navigation uses network-first with an offline fallback,
and an installed worker is asked to update with `updateViaCache: "none"`.
Existing controlled clients reload once after `controllerchange` so a stale
legacy shell cannot remain the visible route indefinitely. Dynamic API
responses remain excluded from the service-worker cache.

### P0-3 — normal worker lifecycle

The default `HostServer` starts the managed Product V2 worker during normal
server construction. The worker remains alive for the server lifetime and is
closed with the Host runtime. Test/fixture forms that explicitly disable the
worker remain deterministic and request-scoped.

### P0-4 — provider invocation diagnostics

The installed CLI was verified as `codex-cli 0.150.0-alpha.12.2`, authenticated
through ChatGPT. A safe parser probe showed that the previous
`--ask-for-approval never` flag was rejected by this installation. That flag
was removed. Each Product V2 call now records bounded operational diagnostics:
executable, CLI version, model, reasoning effort, safe invocation flags,
return code, timeout state, duration, and redacted diagnostic stdout/stderr.
Provider failures are retryable and never expose stack traces or credentials to
the product UI.

The live smoke then exposed a separate unresolved CLI exit-code-1 condition.
The exact sanitized persisted failure from the second fresh Home was:

```text
semantic provider failed (exit code 1): 2026-08-30T14:49:50.685864Z  WARN codex_skills::interface: ignoring interface.icon_small: icon path with '..' must resolve under plugin assets/
2026-08-30T14:49:50.685893Z  WARN codex_skills::interface: ignoring interface.icon_large: icon path with '..' must resolve under plugin assets/
2026-08-30T14:49:50.696158Z  WARN codex_core::shell_snapshot: Failed to create shell snapshot for powershell: Shell snapshot not supported yet for PowerShell
2026-08-30T14:49:51.132594Z  WARN codex_skills::interface: ignoring interface.icon_small: icon path with '..' must resolve under plugin assets/
2026-08-30T14:49:51.132630Z  WARN codex_skills::interface: ignoring interface.icon_large: icon path with '..' must resolve under plugin assets/; retry available
```

This is recorded as an operational failure, not a semantic result. Further
live attempts were deliberately stopped at the authorized limit of two
captures.

### P0-5 — bounded automatic retry

Automatic retries use durable delays of 1, 2, 4, and 8 seconds, with five
automatic attempts total. A terminal failed row is not hot-looped; an explicit
retry requeues it. Raw captures remain durable throughout.

### P0-6 — truthful degraded UX

Ask returns typed `processing` or `processing_failed` responses while work is
pending or failed, instead of claiming that no memory exists. Attention and
Memory show an explicit “still understanding” or saved-but-unavailable notice.
Provider details remain outside the user-facing copy.

### P1 — service-worker update behavior

The versioned `v7` shell, update check, waiting-worker message, controlled-page
reload, and network-first navigation path provide a deterministic update route
for installed PWA clients without caching dynamic state.

## Deterministic validation

The added regression uses a fresh Home, normal default `create_server()`
construction, a delayed fake provider, real HTTP V2 Capture/processing/state/
Ask calls, and no manual processing command. It verifies immediate durable
capture, visible processing, automatic completion, evidence-backed Attention
and Memory, typed pending Ask, Host/Product queue agreement, the authoritative
database path, and an empty legacy V1 queue.

The focused Product V2/UI/provider suite passed after the harness cleanup
correction. The full results and command inventory are in the coding summary
and `eval/results/product-v2-human-dogfood-lifecycle.json`. The existing
visible Product V2 integrated acceptance suite was also rerun with its
historical result kept unchanged; it remains a deterministic fixture result,
not live-provider evidence.

## Decision

**KEEP** the deterministic store, lifecycle, retry, provider-diagnostic, typed
UX, and service-worker fixes. **REVISE** the live Codex adapter before calling
the human-dogfood gate PASS: the remaining CLI exit-code-1 condition needs an
explicitly authorized follow-up diagnosis and a new bounded live run.
