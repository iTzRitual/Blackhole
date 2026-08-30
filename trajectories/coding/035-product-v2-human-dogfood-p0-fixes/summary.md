# Product V2 human dogfood P0 fixes

## Goal

Implement the explicitly authorized Product V2 human-dogfood P0/P1 fixes on an
isolated branch based exactly on integration SHA
`4224d826a5c35811f5eae582a510144cdce77e73`, while preserving frozen V1 and
all protected worktrees/evidence.

## Agent/tool used

Codex coding agent with PowerShell, Python standard-library test/runtime tools,
Git worktree/branch operations, and read-only SQLite inspection.

## Initial hypothesis

The observed store mismatch is likely an observability/lifecycle defect: Host
status reports the legacy `blackhole.db` and only reports V2 counts after a
ProductRuntime has been lazily opened, while `product_process` opens the
authoritative `blackhole-v2.db`. The provider failure is likely an invocation
compatibility defect because the Product V2 adapter passes CLI flags that may
not exist in the installed Codex version. The worker and PWA cache behavior
require direct reproduction before choosing fixes.

## Important implementation decisions

- Centralized Product V2 database resolution in `product_database_path()` and
  made Host status inspect the same V2 store that Product processing uses.
  The legacy `blackhole.db` remains a compatibility/V1 store.
- Started the managed Product V2 worker during normal default HostServer
  construction and preserved explicit worker-disabled fixture/integration
  modes.
- Removed the installed-CLI-incompatible `--ask-for-approval never` flag.
  Added bounded provider diagnostics with executable/version, model,
  reasoning, safe placeholder flags, return code, timeout, duration, and
  sanitized diagnostic stdout/stderr.
- Bounded automatic retries to five attempts with durable 1/2/4/8-second
  delays; terminal failures require explicit retry.
- Added typed pending/failed Ask results and visible Attention/Memory
  processing notices. Versioned the PWA shell to `v7`, excluded API data from
  the service-worker cache, and added update checks plus controlled-client
  reload behavior.
- Added deterministic tests for normal delayed HTTP processing, provider
  diagnostics, retry termination, and PWA/UI contracts. No benchmark prompt,
  expected output, evaluator, or holdout material changed.

## Tools/actions used

- Read the pasted task file before continuing.
- Verified the source integration worktree was clean at the required SHA.
- Created the isolated target worktree and branch.
- Read the Product V2 integration, dogfood, UI, architecture, decision, and
  reproduction documents before changing the subject area.
- Inspected the protected human-dogfood home read-only and recorded hashes and
  sanitized SQLite status evidence.
- Verified the installed Codex CLI surface read-only.
- Added and ran focused deterministic tests, full application tests, evaluator
  tests, Product V2 harness tests, qualification, compile/syntax checks, and
  the existing integrated acceptance protocol in an isolated temporary output
  directory.
- Ran two authorized live normal-launch smoke attempts in fresh temporary
  Homes, using one neutral capture per attempt and no live Ask after provider
  failure. No manual `product_process` processing was used.
- Rehashed the protected human-dogfood Home after all work; every recorded
  file hash and size was unchanged.

## Failures encountered

The first attempt to create the active goal found a pre-existing attachment-
reading goal in this thread. That completed goal was closed after the required
file was read, then this implementation goal was created.
- The first deterministic regression run left a read-only SQLite verification
  connection open on Windows; the test harness was corrected to close it and
  the regression then passed.
- The first live attempt returned a durable provider failure after an
  immediate capture. The second live attempt confirmed a separate CLI exit
  code 1 with sanitized warning output. The live gate therefore remains
  PARTIAL, as required by the task; no semantic success was inferred.

## Retries or changed approaches

- A broad patch was split into smaller `apply_patch` changes after one context
  verification failure, then rechecked with compile/tests.
- The historical integrated acceptance runner was executed from an isolated
  temporary working directory so its generated report could be inspected
  without overwriting the frozen `eval/results/product-v2-integrated-acceptance.json`.

## Human feedback or checkpoints

The authorizing pasted instruction is the governing checkpoint. No additional
human feedback has been received yet.

## Evaluation performed

Baseline before implementation: the existing focused Product V2/Host/PWA/UI
suite passed 37 tests.

After implementation:

- `python -m unittest discover -s app/tests -v`: **110 passed**.
- `python -m unittest discover -s eval/tests -v`: **10 passed**.
- `python -m unittest product_acceptance.harness.test_harness -v`: **7 passed**.
- `python scripts/qualification_check.py --inventory`: **no hard failures,
  4 pre-existing warnings**.
- Existing integrated acceptance protocol: **50/50 PASS**, all quality gates
  PASS, latency probe PASS (`capture_return_ms=8.841`,
  `processing_completion_ms=134.743`); the historical result file's SHA-256
  was unchanged before and after the rerun.
- `python -m compileall -q app eval product_acceptance scripts`: **PASS**.
- `node --check app/web/app.js`: **PASS**.
- Normal delayed-provider regression: **PASS**; capture returned immediately,
  pending Ask was typed `processing`, automatic worker completion produced
  Memory and Attention, status paths agreed on the V2 database, and the V1
  queue remained empty.
- Live normal `python -m app.web_app` smoke: **PARTIAL** after the authorized
  two-capture limit. Both captures returned HTTP 200/pending immediately;
  both provider attempts failed before semantic state. The exact sanitized
  second failure is in the runtime trace and Product V2 dogfood document.

## Result

The deterministic Product V2 P0/P1 repair is complete and regression-tested.
The live gate is not complete: the installed CLI still exits with code 1 in
the normal app path after the known unsupported flag was removed. The raw
captures remained durable, no Ask was issued against an unprocessed live
capture, and no benchmark or holdout boundary was crossed.

## Regressions or unresolved issues

No historical V1, evaluator, Product V2 acceptance, or deterministic UI
regression remains. The unresolved issue is the live provider exit-code-1
condition whose sanitized warning output is recorded in
`trajectories/runtime/035-product-v2-human-dogfood-live-smoke/trace.json`.
Further live attempts require a new authorization because the two-attempt
limit for this task was reached.

## Final decision

**KEEP** the deterministic store/path, worker lifecycle, retry, diagnostic,
typed UX, and service-worker changes. **REVISE** the live Codex adapter in a
separately authorized follow-up before claiming the human-dogfood gate PASS.

## Related git commit

`41271c9` — `fix: repair Product V2 human dogfood runtime`
