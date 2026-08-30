# Product V2 Ask routing trajectory

## Goal

Repair the Product V2 Ask route in an isolated post-freeze generalization
worktree. The live failure was a Polish basement-key question being routed to
an unrelated children-pickup Attention item because the standalone preposition
`do` was treated as a task/time marker. The authorized goal was a general
open-world Ask planner and scoped retrieval path, not a phrase-specific key
patch or a benchmark change.

## Agent/tool used

Codex in the local shared workspace. Repository inspection and validation used
PowerShell, Python's unittest/compileall commands, Node syntax checking, the
public acceptance runner, and the local Product V2 HTTP surface. File changes
were applied with `apply_patch`.

## Initial hypothesis

The failure was caused by routing before generic retrieval: a short token
collision selected Attention even when relevant current Memory matched. A
whole-word, language-aware planner plus scoped ranking should reserve
deterministic fast paths for high-confidence intents and leave ordinary
questions on generic retrieval or bounded synthesis.

## Important implementation decisions

- Added `app/ask_planner.py` with whole-word tokenization, accent folding,
  conservative English/Polish aliases, explicit intent plans, and no
  standalone `do` Attention cue.
- Replaced Product V2's broad Ask context with plan-aware retrieval over
  current facts, matching history, matching relations, matching/open
  Attention, and source references only. Generic matching supports inflections,
  same-entity fact expansion, multi-object ties, location-list observations,
  ambiguity, corrections, retractions, and unknown values.
- Kept deterministic Attention, cost, change, and last-mention paths. Future
  advice phrased as a recommendation is kept on generic Memory rather than
  being mistaken for a recorded correction.
- Added distinct `no_data` and processed-memory `no_match` responses, including
  the PWA's visible no-data state. Pending and failed processing behavior was
  preserved.
- The provider adapter and its source worktree were not changed.

## Tools/actions used

- Read the user-referenced attachment before continuing.
- Verified the provider-fix source worktree and exact base SHA, then created
  only the target `product/v2-ask-fix` worktree from that SHA.
- Audited the V2 HTTP route, Host facade, ProductRuntime Ask path, PWA answer
  normalization, and existing tests.
- Added a deterministic 36-case multilingual corpus, mocked HTTP E2E checks,
  and provider-context/no-data/retraction assertions. The corpus grew to 37
  cases after adding a last-mention regression.
- Ran the visible 50-case integrated acceptance in a disposable working
  directory so the historical repository result was not rewritten.
- Ran the authorized fresh normal-launch live smoke with four captures and
  six Ask requests, then stopped the server normally. No provider token was
  read, copied, exported, or persisted.

## Failures encountered and changed approaches

- The initial implementation reproduced the known routing issue as
  `mode=attention` for the Polish basement-key question; the planner removed
  the standalone preposition collision.
- An early generic ranking rule required every content term to occur in one
  fact. This broke natural inflections and legitimate multi-fact questions;
  it was replaced with qualified best-candidate ranking, entity expansion,
  aliases, and a field-oriented location-list path.
- A change-history pass initially returned only the corrected value and once
  duplicated it. Changed-entity history expansion and shared identity keys
  now retain the prior value once and the correction once.
- The first post-change disposable integrated acceptance run was 30 PASS / 20
  FAIL. The failures identified the over-strict ranking and future-advice
  misclassification. After the smallest general fixes, the rerun was 50/50
  PASS with every quality gate and the latency probe passing.
- The planner review also found an untested last-mention term-filter issue;
  it was corrected and covered by a regression.

## Human feedback or checkpoints

The initiating authorization was supplied in the referenced pasted text file.
No additional human feedback or live wording change occurred during the
implementation. The live questions were issued as the six authorized strings
without changing code between requests.

## Evaluation performed

- Baseline before the change: the focused Product V2 suite had 16 passing
  tests, and the prescribed Polish key question returned unrelated Attention.
- Final focused Ask/UI/Product V2 run: 32 tests passed; the dedicated Ask
  routing suite contains 37 routing cases and passed all 5 test methods.
- Final repository checks: application, evaluator, and acceptance-harness
  suites; compileall; JavaScript syntax; public benchmark structure
  (`200` events, `4` checkpoints); and non-scored contract smoke.
- Disposable integrated acceptance: `50/50 PASS`, all seven reliability
  gates `PASS`, and the asynchronous latency probe `PASS` (`9.352 ms` capture
  return and `141.023 ms` completion with a `120 ms` fixture delay).
- Live smoke: 4/4 captures processed on attempt 1 (`4` provider extraction
  calls, `0` retries); 6/6 authorized Ask requests returned useful `ready`
  results with source references and `0` Ask-time provider calls.
- No frozen V1 score, official baseline, holdout result, or benchmark metric
  was rerun or changed. This task has no benchmark metric after/before claim.

## Result

PASS. The original live Polish and English basement-key questions now retrieve
the key Memory, the two Kuba questions retrieve the preference, the car
question retrieves the condition note, and the near-term question returns the
children-pickup Attention item. The detailed live record is in
`live-validation.json`.

## Regressions or unresolved issues

No application, evaluator, visible acceptance, benchmark-structure, or
provider-boundary regression remained after the final validation. The
deterministic integrated acceptance is visible development evidence, not
unseen generalization or a new benchmark result. No new visual browser review
was performed in this task; the existing PWA visual evidence remains
historical.

## Final decision

KEEP the general Product V2 Ask planner/retrieval/UI change for the explicitly
authorized post-freeze product scope. Do not label it E006 or use it to tune
the frozen baseline.

## Related git commit

`046ffa8` (`fix: generalize Product V2 Ask routing`). This summary-reference
update is recorded in the following documentation-only commit.
