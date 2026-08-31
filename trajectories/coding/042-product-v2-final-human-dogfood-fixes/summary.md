# Product V2 final human dogfood P0/P1 repair

## Goal

Deliver the smallest coherent final Product V2 repair that materially improves
the path from capture to useful semantic Memory and Attention and makes
Attention, Memory, Ask, and operational logs visibly usable, while preserving
the settled semantic, persistence, provenance, retry, Undo, API, CLI, and
benchmark boundaries.

## Agent/tool used

This was completed in the routine Sol Advisor implementation lane in the
isolated `product/v2-final-dogfood-fixes` worktree. The worker context did not
expose exact runtime model, reasoning-effort, or native thread/session
metadata; no such values are inferred here. The actual bounded provider
experiment used the installed authenticated Codex CLI with model
`gpt-5.6-luna`. The browser review used the local in-app browser tooling.

## Initial hypothesis

A compact versioned extraction instruction, bounded prior-memory context, a
supported lower reasoning effort, and conservative small batches could reduce
provider overhead without weakening semantic truth. Defensive presentation,
stable disclosure state, contextual history, an Ask conversation, and concise
sanitized lifecycle logs could remove the remaining visible dogfood friction
without changing the Host/API or persistence architecture.

## Important implementation decisions

- Inspected `codex exec --help` and `codex features list`; no unsupported fast
  or priority CLI flag was invented. `low` was selected after high/medium/low
  ordinary-case comparison because all five bounded semantic checks passed at
  each effort and low was fastest (`31.640s` vs `43.391s` and `48.859s`).
- Kept the Product V2 runtime batch size at conservative `2`, with bounded
  projection and prior-memory context and the compact prompt version.
- Preserved capture immediacy, ordered semantic commit/projection, persisted
  capture-time temporal anchoring through delay/retry/rebuild, provider-free
  deterministic Ask routes, provenance, semantic uncertainty/corrections,
  and permanent Undo.
- Added human-readable privacy-preserving lifecycle lines without logging
  capture/question content, provider payloads, credentials, full files, or
  giant output.
- Added Attention time/overdue copy, stable persistent disclosures and
  chevrons, contextual Memory history, defensive display normalization, Ask
  chat/examples/supporting-memory rendering, centered Capture alignment, and
  removed the active navigation underline.

## Tools/actions used

Read `AGENTS.md`, the complete supplied specification, relevant Product V2
contracts, the local skill instructions, and the installed CLI capability
surfaces. Edited only owned files with `apply_patch`. Ran focused deterministic
tests before the bounded provider comparison, then ran the separate bounded
live smoke in a fresh temporary Home and the two local viewport reviews.
Temporary Homes and the initially extra visual artifact were removed; the
allowed visual evidence and machine-readable live record were retained.

## Failures, retries, and changed approaches

- The first focused pass exposed an existing provider-diagnostic expectation
  for spaced JSON and an existing normal-launch expectation for two captures
  per provider call. The implementation restored default JSON spacing and kept
  conservative batch size `2`; focused tests then passed.
- The browser initially served the old PWA cache (`v7`), so the shell/cache
  version was bumped to `v8` and review was repeated against the updated local
  server.
- The final live launcher cleanup returned Windows status `3221225786` and did
  not capture child stop lines, although deterministic clean-stop coverage and
  a separate local visual server emitted clean worker/server stop lines.
- The live smoke's first useful state was observed at `23.031s`; the remaining
  burst was observed at `129.562s`. This did not establish a material
  end-to-end latency improvement, so the overall gate is PARTIAL/REVISE. No
  implementation or wording was changed after observing live outputs.

## Human feedback or checkpoints

The parent requested runtime metadata and brief phase checks during the
time-boxed run. Exact native runtime metadata was not exposed. No additional
scope, provider token, benchmark material, or protected worktree was supplied
or used.

## Evaluation performed

- Focused deterministic Product V2/UI regression: `103/103` passed before the
  final full suite.
- Full application suite: `python -m unittest discover -s app/tests -p
  "test_*.py" -v` — `170` tests passed.
- Acceptance harness: `python -m unittest discover -s product_acceptance/harness
  -p "test_*.py" -v` — `7` passed.
- Evaluator suite: `python -m unittest discover -s eval/tests -p "test_*.py"
  -v` — `10` passed.
- `python scripts/run_product_v2_integrated_acceptance.py` — `50/50 PASS`,
  `FAIL=0`, `PARTIAL=0`, `NOT TESTED=0`; latency probe PASS with capture
  return `7.489ms` and processing completion `140.295ms`.
- `python -m compileall -q app eval scripts`, `node --check app/web/app.js`,
  benchmark structure check (`200` events/`4` checkpoints), and contract smoke
  all passed. `git diff --check` passed aside from normal CRLF conversion
  warnings emitted by generated result files.
- Bounded diagnostic provider comparison: exactly `3` calls (limit `6`), all
  parsed and semantically correct for simple fact, relative action,
  uncertainty, correction, cross-language fact, and temporal normalization.
- Final live smoke: exactly `6` captures (all HTTP `200`, processed `6`, failed
  `0`) and exactly `4` Ask requests (all HTTP `200`, ready, provider-free,
  `15–16ms`). Capture #3 due time exactly matched capture time plus ten minutes
  with timezone. Evidence is in `live-validation.json`.
- Visual review: 390×844 and 1280×900 verified composer alignment/no underline,
  Attention time/overdue/Done/disclosure behavior, contextual Memory history,
  Ask examples/chat/supporting memories, and artifact-free display. Evidence
  is the two allowed PNGs in this trajectory.

## Result

The deterministic product repair is complete and keeps semantic truth intact.
The live product gate is **PARTIAL / REVISE**: the observed provider burst did
not demonstrate the required material latency improvement and launcher stop
evidence was incomplete, despite successful HTTP/semantic checks and clean
deterministic coverage.

## Regressions or unresolved issues

No deterministic, semantic, provenance, language-invariance, Ask-routing,
provider-diagnostic, retry, lifecycle, Undo/logging, HTTP, UI, compile, or
acceptance regression remains. The end-to-end burst attribution/latency result
and launcher shutdown capture need a separately authorized follow-up if a
PASS gate is required. No second live run was made and no benchmark or
holdout result was changed.

## Final decision

**KEEP** the compact prompt/context, low-effort selection, conservative
batching, UI presentation, and operational logging repairs. Mark the overall
human-dogfood gate **PARTIAL / REVISE** rather than claiming full completion.

## Related git commit

The implementation and evidence are committed on
`product/v2-final-dogfood-fixes` in `e5ca77f`
(`e5ca77f8f95be5363be0e88bb8b56e8eb05fe9ad`).

## Fix-first review correction — 2026-08-31

### Findings addressed

The correction stayed within the original architecture and made no provider
calls. Extraction context selection now scores deterministic overlap with the
current capture terms, then sequence/capture-time recency and canonical stable
ties, rather than taking list tails. The new over-limit test fills the Home
with unrelated facts, processes a correction, verifies the old matching fact
was supplied to the provider, and verifies current/history truth after rebuild.

Default human-readable learned summaries remain enabled. Concept/key/value
guards replace credential-like concepts, access codes, generic notes/captures,
nested payloads, long opaque strings, and raw-like echoes with non-content
placeholders; benign scalar location/cost values remain human-readable. The
human logger additionally redacts labeled private values.

The UI now exposes an opt-in, inert dependency-free Node hook for the same
production normalization/time/disclosure/example helpers. Tests execute
`[object Object]`/`undefined`/`null` omission, structured related memories,
contextual history, due/overdue copy, stable disclosure restoration, and Ask
example visibility. HTML and service-worker shell references, including the
manifest and Apple touch icon, are uniformly `v8`.

### Correction evaluation

The focused correction set is `12/12`; the combined focused Product V2/UI
regression is `105/105`. No live values in `live-validation.json` were
changed, and no new provider/live smoke was made. The overall gate remains
**PARTIAL / REVISE** for the already-recorded burst-latency and launcher
shutdown limitations.

## Configuration-boundary correction — 2026-08-31

### Goal

Correct the review-found configuration leak without changing the established
Product V2 architecture, semantic contract, or honest live PARTIAL/REVISE gate.

### Agent/tool used

Routine Luna/Max implementation lane in the same isolated
`product/v2-final-dogfood-fixes` worktree. Exact runtime metadata was not
exposed by this worker context; no model, effort, or native session ID is
inferred. No provider or live call was made for this correction.

### Important implementation decisions

- Restored shared/legacy `DEFAULT_REASONING_EFFORT` to `high`,
  `DEFAULT_BATCH_SIZE` to `10`, and legacy supported efforts to
  `max/high/medium`.
- Added independent Product V2 defaults (`low`, `2`), supported-effort
  validation, and `RuntimeConfig.product_reasoning_effort` /
  `product_batch_size` fields. Fresh config writes both boundaries; an old
  config without product fields retains its legacy values and supplies Product
  V2 defaults in memory. The config version and legacy field names are
  unchanged.
- Kept legacy Host engine/provider/status on legacy fields. Product V2 lazy
  Host construction, Product V2 discovery/readiness, queue utility, and direct
  ProductRuntime/ProductCodexProvider defaults use Product V2 fields. A
  Product V2 wrapper preserves low support without broadening legacy discovery.
- Added executable deterministic tests for fresh/existing config migration,
  Host/runtime separation, direct defaults, Product V2 readiness, and
  `product_process` wiring.

### Tools/actions used

Inspected the current isolated diff and runtime configuration; edited only the
owned implementation, test, decision, trajectory, and evaluation files with
`apply_patch`. Ran all provider-free suites and hard checks. The integrated
acceptance runner was allowed because it uses its existing deterministic
fixture provider; its time-varying historical result was restored immediately
afterward. No live smoke or diagnostic comparison was rerun.

### Failures, retries, and changed approaches

The first focused run after the split exposed one expected stale assertion
that still treated the shared defaults as Product V2 defaults. It was replaced
with boundary-aware executable tests. No test hung, no implementation retry
was needed, and no semantic wording or live measurement was changed.

### Human feedback or checkpoints

The parent required the correction to remain on the same branch, make no new
provider calls, preserve the PARTIAL/REVISE gate, and explicitly retain the
historical first-correction and parent acceptance evidence. Those values are
recorded below and were not rewritten.

### Evaluation performed

Historical evidence retained: first review correction `105/105` focused
Product V2/UI tests and `172/172` full application tests; parent
post-correction provider-free acceptance `50/50` with latency probe
`7.066 ms` capture return and `136.504 ms` processing completion.

New post-config-fix evidence:

- `python -m unittest app.tests.test_product_v2_final_dogfood app.tests.test_pwa_static -q`
  — `16/16`, `2.002s` wall.
- Combined focused Product V2/config/UI regression command — `120/120`,
  `22.358s` wall.
- `python -m unittest discover -s app/tests -p "test_*.py" -q` — `176/176`,
  `26.528s` wall.
- `python -m unittest discover -s product_acceptance/harness -p "test_*.py" -q`
  — `7/7`, `0.428s` wall; evaluator discovery — `10/10`, `2.430s` wall.
- `python scripts/run_product_v2_integrated_acceptance.py` — `50/50`, all
  reliability gates PASS; fixture latency probe `7.320 ms` capture return and
  `137.041 ms` processing completion, with processing complete and status
  pending at capture. The generated historical JSON was restored.
- `python -m compileall -q app eval scripts` PASS (`0.406s`), `node --check
  app/web/app.js` PASS (`0.422s`), qualification PASS with four pre-existing
  warnings (`3.701s`), benchmark structure PASS (`200` events/`4` checkpoints,
  `0.484s`), contract smoke PASS (`0.393s`), and `git diff --check` PASS.
- The prior visual evidence at `390x844` and `1280x900` remains unchanged;
  this correction introduced no UI or PWA changes.

### Result

The configuration-boundary correction is complete and keeps the prior live
gate **PARTIAL / REVISE**. The earlier live values remain first useful
`23.031s`, remaining burst `129.562s`, and incomplete Windows shutdown
evidence. No provider/live values were altered.

### Regressions or unresolved issues

No deterministic regression remains. Four qualification warnings are the
pre-existing repository warnings. The live provider burst latency and
Windows shutdown evidence remain unresolved and were intentionally not
retested under the exhausted live-call budget.

### Final decision

**KEEP** the narrow config split; do not upgrade the overall live gate.

### Related git commit

This correction is committed on `product/v2-final-dogfood-fixes` after the
final scope and boundary checks below.
