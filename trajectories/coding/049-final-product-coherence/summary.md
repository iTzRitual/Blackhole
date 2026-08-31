# Final product coherence + demo-ready gate — trajectory summary

## Goal

Complete the authorized final BLACKHOLE Product V2 coherence task: make normal
READY Ask answers provider-rendered from bounded structured evidence, preserve
completed Attention lifecycle in Memory/history, reconcile clearly completed
open actions generically, improve document identity, repair the Attention and
processing layout defects, and pass the required deterministic, live, visual,
regression, and release gates without touching benchmark/evaluator/V1 oracle
material.

## Agent/tool used

Codex in the Blackhole repository, using the attached task specification,
repository guidance, the local design-foundations, UI-polish,
touch-and-accessibility, UI-review, and in-app-browser skills, shell inspection,
`apply_patch`, the repository test/gate commands, and the in-app browser for
the live visual review.

## Initial hypothesis

The observed product failures were boundary defects that could be repaired
without reopening the frozen benchmark architecture: keep retrieval,
provenance, deterministic calculations, lifecycle validation, and bounded
evidence in deterministic code; route normal semantic Ask responses through a
usable provider; retain terminal lifecycle state as inspectable history while
projecting only open items into active Attention; and fix layout at the CSS
cascade/container level rather than with visual offsets.

## Important implementation decisions

- Added a versioned Product V2 provider-answer boundary. Deterministic code
  performs retrieval, temporal normalization, arithmetic, occurrence totals,
  lifecycle reconciliation, provenance, and evidence validation. A ready
  provider selects bounded evidence IDs and owns normal human-facing prose.
  Unavailable, invalid, unsafe, or empty provider output is a logged and
  explicitly marked degraded fallback.
- Added document identity fields and stable document entity keys for type,
  reference, issuer/sender, recipient, service/product/subject,
  amount/currency, dates, payment status, and related account/reference. Raw
  attachment bytes and provenance remain intact; unreadable or unknown fields
  stay unknown.
- Added generic lifecycle proposals and deterministic matching via explicit
  lifecycle keys, related/superseded event IDs, or strong unique entity keys.
  Removed title-only consolidation. Terminal completed/cancelled Attention
  remains in history; active Attention and its badge expose open items only.
- Fixed the Attention Done misalignment at the CSS cascade boundary with
  `.quiet-button.attention-complete { margin-top: 0; }`, and centered the
  processing notice as a compact vertical stack with bounded text width.
- Updated the visible deterministic acceptance provider fixture to render
  structured money/change values as human text, so its provider-final contract
  remains a meaningful regression rather than a JSON-shaped answer.

## Tools/actions used

Read the referenced pasted task file in full before acting; verified the
starting branch, clean worktree, and exact `master`/`origin/master` SHA;
created this coding trajectory before implementation; inspected the Product V2
docs and decision history; edited only scoped application, test, fixture,
documentation, trajectory, and evaluation files with `apply_patch`; discovered
the installed authenticated local `codex-cli 0.151.0` through the Product V2
readiness path without reading or persisting tokens; ran the bounded synthetic
live scenario in a fresh temporary Home; reviewed the UI in the in-app browser
at 390×844 and 1280×900; stopped the temporary server; and ran every mandated
repository gate.

## Failures encountered

- The first full application run had five language-matrix failures because the
  deterministic test provider returned a raw ISO datetime in prose, which the
  new human-safety guard correctly rejected. The fixture now naturalizes that
  value while preserving the ISO value in structured supporting evidence.
- The first integrated acceptance rerun had four failures because its fixture
  rendered structured money as JSON and did not include both bounded values for
  a change question. The fixture now has generic structured-value and
  history-change rendering; the final integrated rerun passed 50/50.
- The first live attempt was discarded after the ordinary task's Done action
  was clicked before the payment lifecycle check. A second fresh run exposed
  an Attention title that lacked issuer context. The final run used the correct
  capture/payment/Done order and the generic title-enrichment implementation.
  Discarded temporary homes were not committed.

## Human feedback or checkpoints

The attached task specification was the authorization and scope checkpoint.
Required starting-state verification passed: branch `master`, clean worktree,
local HEAD, and `origin/master` all matched
`e71fa2190835063598fdcbc33bfc5835d3dabc25` before edits. No additional human
feedback was received during the run. The task's explicit benchmark/holdout,
provider-token, live-cap, viewport, commit, push, and tag requirements were
treated as release checkpoints.

## Evaluation performed

- Dedicated final coherence suite: `9/9` passing.
- Application suite: `216/216` passing.
- Evaluator suite: `10/10` passing.
- Product acceptance harness: `7/7` passing.
- Root discovery suite: `233/233` passing.
- Integrated visible Product V2 acceptance: `50/50 PASS`; the generated
  result is `eval/results/product-v2-integrated-acceptance.json`.
- Compileall and JavaScript syntax checks passed. The benchmark structural
  check inspected `200` events and `4` checkpoints and passed. The contract
  smoke passed as the explicitly non-scored contract smoke. Qualification
  passed with four pre-existing non-blocking warnings, and `git diff --check`
  passed.
- The final fresh synthetic live run used `5/6` captures and `4/8` Ask
  requests. The ready local provider rendered issuer/payment/current-history
  answers with `provider_used=true`; the payment event closed only the matching
  document Attention, explicit Done closed the ordinary task, and terminal
  history persisted through reload/rebuild/restart. Recorded API capture-return
  samples were `39ms`, `8ms`, and `36ms`; measured post-restart/API Ask samples
  were `11,706ms` and `11,514ms`. Browser review covered the required mobile and
  desktop viewports, including centered processing, centered Done geometry,
  document Memory, terminal history, and natural Ask answers.
- Machine-readable post-freeze evidence is stored in
  `eval/results/product-v2-final-coherence.json`; the runtime trace is stored
  in `trajectories/runtime/049-final-product-coherence/`.

## Result

PASS. The scoped Product V2 coherence implementation satisfies the final
demo-ready gate. The frozen development benchmark, official baseline and
evaluator evidence, calibration boundary, holdout material, and V1 oracle/
scoring semantics were not changed or accessed.

## Regressions or unresolved issues

No unresolved task-scoped deterministic regression remains. Qualification still
reports the four known historical non-blocking warnings. Live provider latency
was measured and recorded but deliberately not optimized because the task
forbids performance/model/reasoning/batch tuning. All live data was synthetic;
no private invoice or user content was committed.

## Final decision

KEEP. The final provider boundary, lifecycle/history projection, generic
document identity, and UI geometry repairs are supported by the passing
regressions, acceptance result, and bounded live/browser evidence.

## Related git commit

`94bc776` (`feat: complete product coherence demo gate`).
