# Product V2 master consolidation and final dogfood fixes

## Goal

Consolidate Product V2 source commit `602bc9848af1da02db1ee5809fb321aa9173959f`
into `master` at `68b7b15d353b12cffb65a770f8583aa0ebb849dd`, verify the
integrated application, implement the final generic human-dogfood corrections
directly on `master`, run the mandated provider-free gates, document evidence,
commit, and push without touching V1 oracle/scoring or holdout material.

## Agent/tool used

Codex desktop using PowerShell, `apply_patch`, Python unittest/evaluation
scripts, and Node syntax checks. Work stayed on the existing `master`
worktree. No parallel coding agent, new branch, or new worktree was used. No
authentic session transcript was exported or fabricated.

## Initial hypothesis

The observed duplicate Attention entries, raw display payloads, occurrence
conflicts, and missing Ask follow-up behavior were projection and presentation
boundary defects. Conservative identity consolidation, explicit occurrence
metadata, bounded temporary thread hints, and defensive UI formatting should
resolve them without changing provider performance policy, the frozen
benchmark, or Product V2's source/derived/evidence boundaries.

## Important implementation decisions

- Fast-forwarded the exact source branch into `master`; source worktree and
  Product V2 history were preserved.
- Consolidated raw and fact-derived Attention at the projection boundary using
  explicit lifecycle identity, strong same-occurrence keys, source-event
  links, and merged provenance. Completed/cancelled lifecycle status remains
  inspectable; active counts and the UI use open items only. Superseded old
  timelines are omitted from the current projection.
- Added an explicit occurrence/event/transaction distinction in the semantic
  metadata boundary. Occurrences are projected side by side and numeric totals
  use deterministic decimal arithmetic; state facts retain reconciliation and
  conflict behavior. A separate derived occurrence table avoids state-table
  uniqueness collisions.
- Added human-readable structured-value, uncertainty, provenance, capture-time,
  temporal, and lifecycle presentation. Memory is current-first with history
  grouped under the relevant entity/topic; the desktop grid uses CSS columns
  and mobile remains one column.
- Added live client-side Attention countdown/urgency refresh, open-only badge
  counting, optimistic Done removal, sticky Ask composition, near-bottom-only
  autoscroll, empty-thread examples, New thread reset, bounded eight-message
  thread context, and neutral reduced-motion-safe loading dots.
- Kept `PRODUCT_PROMPT_VERSION`, extraction configuration, provider model/
  reasoning/performance settings, benchmark content, evaluator artifacts,
  baseline evidence, calibration material, and holdout boundaries unchanged.
  The Ask answer-boundary instruction only states that temporary thread text
  is a non-evidence referent hint.

## Tools/actions used

- Read the authoritative pasted instruction before continuing.
- Verified clean `master`, exact source branch/worktree SHA, source cleanliness,
  and existing Product V2 trajectory directories.
- Fast-forwarded `master` to the exact source commit and pushed the consolidated
  commit to `origin/master` before final fixes.
- Added and ran deterministic backend, HTTP, semantic, UI, PWA, lifecycle,
  provenance, occurrence, aggregation, and Ask-thread regressions.
- Generated final integrated acceptance evidence from the visible public suite
  with its local deterministic provider fixture; copied it to the dedicated
  final result file and restored the historical integrated result artifact.
- Ran application/evaluator/acceptance tests, compileall, JavaScript syntax,
  benchmark structure, non-scored contract smoke, qualification, and diff
  checks.

## Failures, retries, and changed approaches

- The first occurrence implementation attempted to reuse the state projection
  table and hit its `(entity_key, concept)` uniqueness constraint. The derived
  `current_fact_occurrences` table was added so multiple explicit occurrences
  can coexist without weakening state reconciliation.
- Initial Attention grouping selected an incomplete duplicate's missing due
  time; group-level temporal merging now retains the strongest available time.
- Initial Ask thread coverage exceeded the intended bound; it was fixed to the
  last eight role/text messages with no evidence IDs.
- A generic appointment fact initially created an extra Attention lifecycle;
  non-occurrence actionable facts now receive a stable default lifecycle key,
  while occurrence facts remain separate.
- The first final acceptance rerun was `49/50` because terminal Attention rows
  had been filtered from the structured state itself. The state now retains
  explicit completed/cancelled lifecycle status for inspection, while the
  active count, badge, and UI filter remain open-only. The rerun became
  `50/50 PASS`.
- PWA shell expectations were updated consistently from `v8` to `v9`; no
  benchmark or provider behavior was changed.

## Human feedback or checkpoints

The human authorization and requirements were supplied in the pasted
instruction referenced by `prompt.md`. No additional human feedback or live
provider validation was needed after that instruction. The task explicitly
authorized direct master changes and prohibited holdout/V1 oracle access,
provider-performance work, and benchmark changes; those boundaries were
followed.

## Evaluation performed

- Pre-fix consolidated-source integration gates: application `176` tests,
  evaluator `10` tests, acceptance harness `7` tests, and visible integrated
  acceptance `50/50` before this final behavior pass.
- Final application suite: `184/184` tests passed.
- Final evaluator suite: `10/10` tests passed.
- Final Product V2 acceptance harness: `7/7` tests passed.
- Final integrated visible acceptance: `50/50 PASS`, `0` FAIL/PARTIAL/NOT
  TESTED; all `7/7` quality gates PASS; latency PASS with `7.192 ms` capture
  return and `134.981 ms` local-fixture processing completion.
- `compileall`, `node --check app/web/app.js`, benchmark structural check
  (`200` events and `4` checkpoints), non-scored contract smoke, and
  `git diff --check` passed. Qualification passed with four pre-existing
  non-blocking warnings about the frozen-runtime audit path and stale named
  final/comparison artifacts.
- No live provider call, provider token, V1 oracle, G01/G02/G03, holdout
  expected output, benchmark ground truth, baseline prompt, or calibration
  oracle was used.

## Result

The final dogfood failure classes are resolved generically in the Product V2
runtime and PWA. One logical actionable occurrence has one canonical active
Attention row with merged evidence; terminal lifecycle status remains
inspectable but does not count as active. Explicit occurrences coexist and
aggregate deterministically. Ask follow-ups use bounded temporary context
without turning assistant text into evidence or Product Memory. User-facing
structured output is human-readable and avoids internal IDs/raw objects.

## Regressions or unresolved issues

No unresolved deterministic or visible acceptance regression remains. The
qualification warnings are pre-existing and non-blocking. The final evidence
is visible development acceptance evidence, not unseen generalization or
benchmark performance evidence.

## Final decision

**KEEP.** The exact Product V2 source consolidation and final dogfood fixes are
kept on `master`. The final changes remain within the explicitly authorized
post-freeze product scope and do not reopen E006 or the frozen benchmark.

## Related git commit

The final implementation/documentation commit SHA will be recorded here after
the commit is created; the trajectory index will be updated in the same final
documentation handoff.
