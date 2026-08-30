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

## Authorized provider-fix follow-up — 2026-08-30

The preceding **PARTIAL** result is preserved as historical evidence. This
follow-up used the exact source HEAD
`b9478c6a15752b22c0bee8843381c1bf56bebd45` and the isolated
`product/v2-provider-fix` branch. The sanitized control matrix and invocation
record are in
`trajectories/coding/036-product-v2-live-provider-fix/provider-diagnostics.json`.

### Actual provider root cause

The fatal condition was not the PowerShell shell-snapshot warning. The Product
V2 adapter's output schema was incompatible with the installed Codex
structured-output contract: its root object allowed additional properties,
its arrays did not declare `items`, and its nested objects were not strict.
Codex emitted a terminal `turn.failed` event containing
`invalid_request_error` / `invalid_json_schema` with status 400 and exited with
code 1 before generating a model message. The earlier bounded diagnostic chose
stderr warning lines first, which obscured that terminal error.

Controls A and B completed with `OK` while emitting the shell-snapshot warning.
Control D added `--disable shell_snapshot`; the warning disappeared, but the
same schema failure and exit code 1 remained. The final adapter therefore does
not disable shell snapshots merely to silence the warning.

The adapter now generates a strict schema with typed array items, closed object
properties, required fields, and nullable representations for optional semantic
values. It also preserves the terminal JSON failure event, a bounded sanitized
stdout/stderr tail, return code, and timeout state. Non-zero exits remain
retryable failures.

### Final invocation boundary

The final Product V2 call shape is:

```text
codex exec --ephemeral --json --model gpt-5.6-luna
  -c model_reasoning_effort=high
  -s read-only --ignore-rules --skip-git-repo-check
  -C <temporary-isolated-workspace>
  --add-dir <BLACKHOLE_HOME>
  --output-schema <temporary-strict-schema>
  [-i <stored-image>]
  -o <temporary-last-message-file> -
```

The subprocess inherits the environment without modification, sends UTF-8
prompt bytes through a pipe, and uses the normal externally authenticated
Codex configuration. It does not use `--ignore-user-config`,
`--disable shell_snapshot`, or any workspace-write/dangerous sandbox flag.
There is no explicit approval flag; the sandbox is read-only. The default
timeout is 900 seconds. The exact resolved executable path, version, argv
placeholders, and all boundary fields are recorded in the sanitized diagnostic
artifact.

The installed CLI exposes local image support through `--image`; the adapter
forwards image attachments through that flag and leaves document/PDF
attachments as explicit metadata-only records. No OCR or unverified document
interpretation was added, so this limitation remains visible rather than being
presented as a successful read.

### Follow-up live smoke

`python -m app.host init` succeeded in a fresh temporary Home and reported the
normal ChatGPT login. The normal `python -m app.web_app` launch accepted both
authorized captures immediately: approximately 33.0 ms and 9.2 ms, each with
`processing: pending`. The managed worker then processed both on their first
attempt, with 2 processed, 0 pending, 0 processing, 0 failed, and zero retries.

Memory contained the known fact `Klucze do piwnicy / location / u mamy` with
source reference `provider-smoke-basement`. Attention contained the open
appointment `Odebrać dzieci`, due ten minutes after capture, with source
reference `provider-smoke-kids`.

The second prescribed Ask returned the useful children Attention item with
evidence. The first prescribed Ask, `Gdzie są klucze do piwnicy?`, was instead
routed to the unrelated Attention item by an existing deterministic Polish
router rule that treated the standalone preposition `do` as a task/time
marker. This is recorded as an unrelated product-routing issue; no semantic
router change is retained in this provider-only branch, and no additional live
Ask was made because the authorized two-Ask limit had been reached.

### Follow-up decision

The real provider adapter repair is **KEEP as a provider-boundary change**: the
authenticated normal worker now produces useful semantic Memory and Attention
state without retries. The overall prescribed live provider gate remains
**PARTIAL / REVISE** because the first live Ask was not useful; fixing that
unrelated router issue requires separate product-scope authorization and a
fresh bounded validation. No benchmark, baseline,
holdout, V1 oracle, G01/G02/G03 run, global Codex configuration, or protected
worktree was changed or accessed.
