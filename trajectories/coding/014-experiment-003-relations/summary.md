# Experiment 003 summary

## Status

Completed. The application experiment and its evidence are recorded; no
benchmark artifact, expected output, evaluator, response contract, prompt, or
provider state was changed.

## Goal

Test whether generic deterministic relation recovery and, only if needed,
small raw-capture candidate retrieval plus selective relation resolution can
improve relation reconciliation while preserving the frozen benchmark and
current Experiment 002 result.

## Agent/tool used

Codex with the shared local workspace, PowerShell/`rg`/Python inspection,
`apply_patch`, the existing deterministic runner/evaluator, and stdlib unit
tests. No provider call was made because the bounded deterministic retrieval
treatment was sufficient; no provider token was requested, read, or persisted.

## Initial hypothesis

The semantic extractor lacks raw content for relevant prior captures. A small
candidate-retrieval layer may give a targeted resolver enough evidence to choose
duplicate, change, correction, reassignment, or no-relation outcomes without
reintroducing the complete history.

## Reference evidence

- Pre-experiment kept advanced LQA-0M: `0.7492295898545899`.
- Pre-experiment kept DSCR: `72`.
- Current relation-reconciliation score: `0.31690140845070425`.
- Relation reconciliation accounts for 39 of 72 DSCR defects.
- Checkpoint-200 duplicate/change score: `0.0666666667` (`TP=2`, `FP=14`, `FN=14`).

## Phase 0 record

The read-only audit used the recorded public development extraction under
`trajectories/runtime/experiment-001-full-v1/`, its SQLite state, the
Experiment 002 candidate/result artifacts, and the unchanged development
expected output only for scoring diagnostics. No expected output was changed,
and no holdout material was inspected.

The current state contains 200 raw events, 279 observations, 124 stored
relationships, and 83 projected current facts. Explicit supersession and
correction observations are generally represented by an existing
`meaningful_change` relationship, so the main failure is not absence of a
relationship row. The failures are semantic reconciliation errors:

| Failure class | Representative evidence | Audit conclusion |
| --- | --- | --- |
| Missing relation | No broad missing-row pattern among explicit supersessions | Not the primary defect in this slice |
| Wrong target | Receipt chain events `evt-126`, `evt-136`, and `evt-196`; quoted-amount events `evt-058` and `evt-088`; task reassignments `evt-074`, `evt-084`, and `evt-144` | Requires choosing the correct earlier capture, or preserving an intentionally unknown target |
| Wrong relation type | `evt-046` is extracted as `exact_duplicate` rather than expected `normalized_duplicate`; `evt-196` is extracted as `normalized_duplicate` rather than expected `exact_duplicate` | Source wording and lineage are not being reconciled consistently |
| Wrong changed fields / detail | Duplicate/change assertions lose expected `duplicate_group` detail on `evt-026`, `evt-056`, `evt-066`, `evt-106`, and `evt-156`; `evt-126` emits `receipt_id` although the expected public relation uses a note | Existing structured relation detail is incomplete or over-specific |
| Unnecessary relation | The public recent-change projection emits extra quoted-amount relations for `evt-098`, `evt-128`, and `evt-148` | The projector follows a local prior chain after an earlier wrong target instead of the intended storyline |
| Duplicate-group mismatch | Candidate checkpoint-200 count is 7 groups versus expected 6; receipt duplicate groups are named differently and are absent from some related relations | Group identity needs conservative lineage recovery, not new benchmark-specific rules |
| Deterministically recoverable | Explicit `supersedes_event_id` values; exact payload hash comparison; task source wording with no explicit event reference; stable receipt identifiers in raw text | Add generic recovery only where evidence is unambiguous |
| Prior raw content required | Receipt observations retain amounts but not receipt identifiers; `StateStore.extraction_context()` exposes current facts, relationships, and recent capture metadata, not raw content | Small candidate retrieval is justified for receipt lineage and ambiguity; do not retrieve complete history |

Raw payload hashes found only one collision (`evt-073` / `evt-183`), which is
not the receipt duplicate set. The receipt duplicates use different capture
wording, so exact hash or whitespace normalization alone cannot recover them.
The public raw text does, however, contain identifiers such as `R-1005` and
phrases such as “separate purchase” or “unchanged again”; this is sufficient
to test a generic, bounded candidate-retrieval layer. The task cases likewise
show that a source without an explicit event reference should not be forced
to a prior event merely because the subject is known.

The evaluator evidence confirms that relation reconciliation is the dominant
remaining weakness: LQA-0M is `0.7492295898545899`, DSCR is `72`, and relation
reconciliation is `0.31690140845070425` (39 of 72 DSCR defects). At checkpoint
200, `q-duplicates-changes` is `TP=2, FP=14, FN=14`, score
`0.0666666667`. These values are diagnostic references only; the official
baseline and frozen benchmark artifacts remain untouched.

Phase 0 decision: test the smallest generic deterministic recovery first,
then bounded raw candidate retrieval because the audit shows that prior raw
content is needed for the remaining wrong-target cases. A provider resolver is
not yet justified; it may be considered only after the deterministic and
retrieval variants are evaluated under the task instruction. No transcript will
be fabricated.

## Deterministic recovery variant

The first implementation added only generic fallback relationships when the
existing semantic extraction had not already supplied one. It covered explicit
supersession/correction links, duplicate-marked identical raw payloads, and
task-status transitions with an explicit superseded event. Neutral unit
fixtures passed, including the safety rule that repeated identical text is not
silently deduplicated without semantic duplicate evidence.

The 50-event FAST replay inserted three deterministic fallback relationships but
did not improve the score: `LQA-0M=0.8888888889`, `DSCR=4`, and no hard failure.
The relation-focused FAST replay likewise did not improve the diagnostic result:
`LQA-0M=0.7407407407`, `DSCR=7`. The audit showed that prior raw content was
still required, so the next variant was bounded raw candidate retrieval, still
without a provider call.

## Retrieval variant and implementation decisions

The kept treatment considers only receipt-like relation sources with one
existing relation, extracts the first stable identifier, and retrieves no more
than four earlier matching raw captures. Meaningful changes prefer the newest
earlier non-duplicate candidate; duplicate/similarity relations prefer the
newest candidate. Candidate raw text and metadata, selected targets, and
replacement digests are recorded per checkpoint. Replacement touches derived
relationship rows only; immutable raw events and observations remain intact.
The public projector was corrected to omit empty duplicate fields, count only
duplicate components as duplicate groups, and avoid emitting narrative
meaningful-change notes as duplicate detail. Neutral fixtures use unrelated
Harbor Market receipt data and contain no public benchmark identifiers.

The first full retrieval run exposed an interaction in which deterministic
fallback rows blocked some replacements. The corrected v2 run fixed that
coverage behavior; v3 then fixed generic merchant filtering and the remaining
serialization/grouping mismatches. All intermediate artifacts are preserved.

## Evaluation and result

Validation included full stdlib unit tests, the benchmark generator check, the
contract smoke test, Python compilation, `git diff --check`, and protected-file
hash checks. `python -m pytest -q` was attempted but the environment has no
pytest installation; the repository's stdlib suite was used instead and passed.
The unchanged deterministic evaluator scored the final v3 public replay:

- LQA-0M: `0.8157180034018269`, up from `0.7492295898545899` (`+0.0664884135`).
- Checkpoints 50/100/150/200: `0.8518518519 / 0.8189738502 / 0.7821654040 / 0.8098809075`.
- DSCR: `45`, down from `72` (`-27`; `22.5` per 100 events).
- Relation reconciliation: `0.6696428571`, up from `0.3169014085`.
- Duplicate/change: `1.0`; checkpoint-200 duplicate/change query score rose
  from `0.0666666667` to `0.8823529412`.
- Totals: `TP=311`, `FP=37`, `FN=64`; schema, safety, and source-integrity
  checks passed.

The relation-focused FAST result for the final treatment was
`LQA-0M=0.9629629630`, `DSCR=1`, with no hard failure. All replayed semantic
inputs were recorded public E001 extraction outputs; provider calls and added
provider tokens were `0`. The final runner invocation completed in under one
second of local wall time, excluding the separate evaluator invocation.

## Failures, human checkpoint, and final decision

The remaining known mismatch is an expected narrative note for one similar
receipt that the raw capture does not explicitly establish; it remains
unasserted rather than fabricated. Task-state and recent-change weaknesses
were outside this experiment's selected relation scope and were unchanged.
No material category, safety, schema, source-integrity, benchmark, baseline,
calibration, or holdout-boundary regression remains.

The human instruction authorized this experiment, required a new trajectory,
and required stopping before Experiment 004. No additional mid-run human
feedback or provider configuration was supplied. Final decision: **KEEP** the
bounded retrieval treatment. Do not start a provider resolver or Experiment
004 in this task.

## Related git commit

Related git commit: this commit, `experiment: add retrieval-assisted relation
reconciliation`. No authentic session transcript was available, and none was
fabricated.
