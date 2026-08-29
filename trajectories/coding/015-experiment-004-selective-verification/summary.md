# Experiment 004 summary

## Status

Complete. No benchmark, expected output, query bundle, response contract,
evaluator, baseline, calibration artifact, holdout material, or prior
experiment result was modified.

## Goal

Test whether generic deterministic raw-source evidence coverage plus selective
semantic verification can recover explicitly stated facts omitted by semantic
extraction, without redesigning Experiment 003 relation reconciliation or
reprocessing every capture.

## Agent/tool used

Codex with the shared local workspace, PowerShell/`rg`/Python inspection,
`apply_patch`, the existing runner/evaluator, and the subscription-first replay
boundary. No provider call was needed for the kept treatment. No authentic
session transcript was available and none was fabricated.

## Hypothesis

High-confidence raw anchors for dates, amounts, identifiers, lifecycle cues,
and approval/action language can expose selective extraction gaps. Conservative
deterministic completion should repair only unambiguous gaps; a one-capture
semantic verifier should be reserved for residual flagged gaps.

## Reference

The frozen Experiment 003 reference is LQA-0M `0.8157180034018269`, DSCR `45`,
with checkpoints `0.8518518519 / 0.8189738502 / 0.7821654040 / 0.8098809075`.
The official benchmark, evaluator, baseline-v1, response-contract-v2, query
bundle, and all prior experiment result artifacts are protected.

## Phase 0 read-only failure audit

The audit compared the final E003 public candidate with the public development
expected output for diagnosis, then traced representative mismatches back to
the immutable raw capture and the recorded E003 SQLite observations. Expected
data was not passed to runtime code or any provider prompt. E003 has 45 unique
DSCR defects: 10 current-state, 3 obligation/deadline, 15 relation
reconciliation, 5 safety, 4 task/deadline, and 8 temporal/history defects.

| Error class | Representative evidence | Audit classification and E004 scope |
| --- | --- | --- |
| Source explicitly contains a missing structural fact | `evt-049` contains `GYM-NEW` and signed date `2026-02-15` but stores only status/executed; `evt-055` says `per month` but its premium object lacks `billing_period`; `evt-099` repeats an explicit signed date; `evt-179` repeats the current contract identifier | High-confidence completeness gaps; eligible for generic anchor coverage and deterministic completion. |
| Source explicitly contains a lifecycle cue but role mapping is required | `evt-010` says a standing-order change should be requested and no request was sent; `evt-030` says prepare a transfer but do not send; `evt-080` says the change is only a proposal; `evt-134` says reopen the pickup task | Plausible lifecycle omissions, but status mapping must remain conservative and generic; eligible for deterministic completion when an existing subject/status context makes the mapping unambiguous. |
| Source contains a fact but semantic role is ambiguous or wrong | `evt-021` stores `historical_price` although the notice supplies a future/current price; `evt-019` and `evt-059` store `next_renewal` while the public expected projection asks for `expiry_date`; `evt-029` stores an old contract fee as `historical_price` | Not a pure completeness gap; do not redesign role resolution in E004. A verifier may only correct such a fact if raw wording and existing subject context clearly establish the replacement. |
| Extracted fact exists but projector loses it | `evt-081` has a termination date but reactivation projects an unknown; `evt-191` has `next_renewal` but its duplicate-marked event is excluded from current state; `evt-199` has an expiry date marked duplicate | Projector/current-state reconciliation defects; explicitly outside the completeness experiment. |
| Extracted fact exists with a shape/status mismatch | `evt-174` stores the explicit blocker as `known` while the expected assertion labels it `inferred`; `evt-055` has amount/currency but lacks only the monthly period field | The blocker is not omitted; the premium period is a completeness gap. Do not tune knowledge status to the expected output. |
| Expected assertion is not defensibly recoverable from this raw capture | `evt-011` does not state the expected 12 EUR charge amount; `evt-111` says only “from March,” not an ISO day; `evt-169` says the signed date did not change but supplies no date; `evt-041` does not explicitly state the expected task status | Preserve unknown or existing state; no deterministic or verifier completion from this capture alone. |
| Other / excluded from E004 | The remaining relation mismatches are wrong target/type/detail choices; obligation extras include already extracted facts; task reassignment edges remain E003 behavior | Do not redesign relation reconciliation or alter benchmark semantics. |

Approximately **7 of the 45 DSCR defect IDs** are plausibly downstream of
extraction completeness omissions: six underlying state gaps (contract ID,
signed date, premium billing period, two action lifecycle states, and the
replacement-task lifecycle) plus one attention defect caused by the missing
task state. The lifecycle estimate is less certain than the four structural
anchor gaps. Relation defects, role mismatches, projector losses, and
non-recoverable expected values are not counted as completeness omissions.

The audit therefore supports a generic scanner and a deterministic completion
variant first. It does not yet justify a provider call or any relation
reconciliation change. The scanner must report anchors and reasons, not emit
facts merely because a number or date appears in prose.

## Required record

## Important implementation decisions

- `app/completeness.py` scans raw text for structural dates, amounts/currencies,
  conservative identifiers, and temporal/lifecycle/action cues. It emits
  anchors, not semantic facts.
- The coverage detector compares anchors with same-event observations and
  relevant current subject state. It avoids treating arbitrary numbers or
  dates as gaps.
- Deterministic completion admits only generic, unambiguous mappings, including
  contract identifiers/dates, an explicit monthly billing-period field, and
  clearly supported lifecycle statuses. Added observations retain the raw event
  as provenance, pass existing public normalization, and never mutate raw data.
- Experiment 003 retrieval reconciliation remains unchanged and runs before the
  completeness pass.
- A versioned verifier prompt and output validator were added and tested with
  neutral fixtures. The verifier receives one capture, its observations,
  anchors, public ontology/value shapes, and relevant current facts only. It
  rejects evaluator/state-key/cross-event content and has a NO CHANGE bias.
- The verifier was not invoked because deterministic FAST and full replay met
  the predeclared keep rule.

## Tools/actions, failures, and retries

Created or changed: `app/completeness.py`, `app/advanced_runner.py`,
`app/tests/test_completeness.py`,
`prompts/runtime/advanced-e004-verifier-v1.md`, the E004 evaluation/runtime
artifacts, and the current documentation/changelog updates.

The first 50-event diagnostic was initially sent through the full evaluator,
which expects all four approved checkpoints and reported missing later
checkpoints. It was immediately replaced with the existing `eval.score_slice`
wrapper; no benchmark file changed. A second completeness-focused FAST slice
used five public query families so the tested fields were represented.

## Evaluation performed

- Neutral completeness fixtures: 6 tests passed.
- Full repository tests: 44 tests passed.
- `python -m compileall -q app`: passed.
- Public generator `--check`: passed for 200 events and 4 checkpoints.
- Contract smoke: passed with the expected non-scored malformed fixture result.
- Standard four-query FAST diagnostic: unchanged at LQA-0M `0.8888888889`,
  DSCR `4`.
- Completeness-focused FAST: E003 reference LQA-0M `0.6444444444`, DSCR `16`;
  E004 LQA-0M `0.7333333333`, DSCR `12` over five public query families.
- Full public deterministic replay used the recorded E001 extraction, the
  unchanged E003 retrieval treatment, and the frozen public evaluator.

## Result

The full E004 replay scored LQA-0M `0.8630770101`, up `0.0473590067` from
E003, with checkpoint scores
`0.8888888889 / 0.8713728401 / 0.8321654040 / 0.8598809075`.
Totals were `TP=327, FP=35, FN=48`; DSCR was `41` (`20.5` per 100 events),
down 4 from E003. Current-state improved from `0.6842105263` to `0.7222222222`,
temporal-history from `0.6984126984` to `0.8730158730`, and safety from
`0.6595744681` to `0.75`. Financial, relation reconciliation,
duplicate/change, entity resolution, obligation/deadline, and contradiction
metrics were unchanged. Schema validity, source integrity, and the safety scan
passed.

The completeness counters recorded 200/200 captures scanned, 10 flagged, 6
captures repaired deterministically, 8 observations added including 1
correction, 0 verifier calls, 0 provider input/output/reasoning tokens, and 0
provider runtime. The runner took about 0.61 seconds by its metadata; the FAST
run took about 0.17 seconds. Four conservative lifecycle flags remained
residual and were not escalated.

## Regressions or unresolved issues

The safety category gained one false-positive assertion even though its score
improved; no consequential execution was present. The remaining strongest
failures are semantic role/projection losses and relation reconciliation, not
generic structural-anchor discovery. The optional verifier has only neutral
fixture coverage and no live provider result. No holdout result is claimed.

## Final decision

**KEEP** deterministic selective completeness. It exceeded the predeclared
threshold through both LQA improvement and DSCR reduction. Keep the verifier
available as a scoped future option, but do not start Experiment 005 in this
task.

## Evidence

- Full candidate: `eval/results/experiment-004-deterministic-full-candidate.json`
- Full score: `eval/results/experiment-004-deterministic-full.json`
- Completeness FAST score: `eval/results/experiment-004-deterministic-completeness-fast.json`
- E003 FAST comparison reference: `eval/results/experiment-004-e003-completeness-fast-reference.json`
- Full runtime trajectory: `trajectories/runtime/experiment-004-deterministic-full/`
- Coding trajectory prompt: `trajectories/coding/015-experiment-004-selective-verification/prompt.md`

## Related git commit

The coherent commit containing this trajectory is
`experiment: add selective completeness verification`.
