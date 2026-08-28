# Task summary: benchmark-size calibration

**Status:** Complete for the requested pre-freeze calibration design and data
creation; Gate A remains open.

## Goal

Add a small, non-scored benchmark-size calibration before freezing Gate A. The
calibration must test state quality under longitudinal churn while the history
remains reasonably available, rather than selecting an event count merely to
exhaust model context.

## Agent/tool used

The work was performed by the Codex coding agent using local file inspection,
`apply_patch` edits, a standard-library Python data generator, PowerShell
validation commands, and Git checks. No application runtime, baseline,
evaluator implementation, external service, or model API was used.

## Initial hypothesis

The earlier approximately 80-event target may be too short to expose
longitudinal state-maintenance failures in a strong long-context model. A
calibration sweep should compare 50, 100, 200, and 400 events with repeated
state churn and use the smallest practical length that shows degradation while
remaining within usable context.

## Important design decisions

- The calibration is isolated under `benchmark/calibration/` and is explicitly
  non-scored. It is not a final development case and does not reuse the final
  benchmark narrative or ground truth.
- Four histories are deterministic prefixes of one 400-event synthetic stream,
  making size comparisons comparable.
- The stream has ten fictional evolving storylines, uneven observation gaps,
  repeated updates, corrections, contradictions, supersession, cancellations,
  exact duplicate text, missing secondary fields, and ambiguous entity links.
- A calibration-only oracle records expected current/previous state, explicit
  known/inferred/unknown semantics, and relation summaries. It is allowed to be
  visible for this non-scored calibration but must not enter final benchmark
  artifacts or tune a baseline prompt.
- Token planning uses a transparent character-based estimate until the selected
  model tokenizer is pinned. Context fit is reported against a conservative 75%
  usable-context budget rather than treating the hard limit as the target.
- The current planning result is approximately 4.6k, 8.7k, 17.0k, and 33.5k
  final input tokens for 50, 100, 200, and 400 events. A 200-event primary
  remains the preferred candidate if the fixed-prompt model run supports it;
  400 is secondary stress material.
- Query correctness and temporal degradation must be measured later with one
  unchanged prompt/configuration across sizes. Individual calibration failures
  must not trigger prompt tuning.
- A model correctness score was intentionally not fabricated because the
  selected model, provider, tokenizer, context limit, and runtime configuration
  are not yet pinned.

## Files created or updated

Created:

- `benchmark/calibration/generate_calibration.py`
- `benchmark/calibration/manifest.json`
- `benchmark/calibration/histories/history-050.jsonl`
- `benchmark/calibration/histories/history-100.jsonl`
- `benchmark/calibration/histories/history-200.jsonl`
- `benchmark/calibration/histories/history-400.jsonl`
- `benchmark/calibration/oracle/oracle-050.json`
- `benchmark/calibration/oracle/oracle-100.json`
- `benchmark/calibration/oracle/oracle-200.json`
- `benchmark/calibration/oracle/oracle-400.json`
- `benchmark/calibration/reports/token-estimates.json`
- `benchmark/calibration/reports/SIZE_CALIBRATION.md`
- `trajectories/coding/004-benchmark-size-calibration/prompt.md`
- `trajectories/coding/004-benchmark-size-calibration/summary.md`

Updated:

- `AGENTS.md` to document the narrow calibration-oracle exception while
  preserving final/holdout protection;
- `README.md` and `benchmark/README.md` to describe the open calibration gate;
- `docs/DECISIONS.md` with the proposed size-calibration decision;
- `docs/EVALUATION.md` with the calibration protocol and revised Gate A status;
  and
- `docs/REPRODUCTION.md` with the calibration regeneration protocol.

## Tools/actions used

- Re-read the master goal, `AGENTS.md`, and the current benchmark/design
  documents before changing benchmark-facing material.
- Created the coding trajectory before continuing the meaningful task.
- Added and executed the deterministic calibration data generator.
- Added the non-scored calibration histories, visible calibration-only oracles,
  manifest, token report, proposal, and selection rule.
- Audited cross-document wording for old fixed 80-event claims and for the
  distinction between calibration oracle data and protected final/holdout
  ground truth.
- Validated JSON/JSONL parsing, exact event counts, sequence bounds, ten
  storyline entries, and shared prefixes across the four histories.
- Ran `git diff --check`; no whitespace errors were reported.

## Failures encountered

- The expected new trajectory directory was not present when the first patch
  was attempted. It was created explicitly, then the task prompt was recorded.
- The first generator run had an f-string quoting syntax error. It was fixed.
- The next run referenced a raw text field at the wrong JSON level for duplicate
  events. It was fixed to use the event payload.

## Retries or changed approaches

The initial trajectory-path assumption and two generator defects were corrected
through local inspection and small patches. The design itself did not change
because of those retries. An unresolved final contradiction was added at the
400-event cutoff so the calibration exercises an explicit final unknown rather
than only resolved conflicts.

## Human feedback or checkpoints

The human instruction explicitly requested calibration before Gate A freeze,
prioritized state churn over raw event count, prohibited prompt tuning from
individual failures, preferred approximately 150–200 events for the realistic
primary, and required a separate optional stress track. No human approval of a
final event count or Gate A freeze has occurred yet.

## Evaluation performed

The generated artifacts were structurally validated. The planning report
measured approximate serialized input tokens and conservative context-fit
matrices. The four final query-bundle calls are estimated at 63,817 aggregate
input tokens; three repeats would be approximately 191,451 input tokens before
outputs. No runtime-model correctness, degradation score, dollar cost, or
exact tokenizer measurement was performed because the selected runtime model
and evaluation runner do not yet exist in scope.

## Result

The repository now has a reproducible, non-scored size-calibration dataset and
documented pre-freeze protocol. The 200-event prefix is a supported primary
candidate, and the 400-event prefix is a supported secondary stress candidate,
subject to the fixed-prompt model run and human review. Gate A has not been
frozen.

## Regressions or unresolved issues

- The selected model/provider, tokenizer, context limit, pricing, output limit,
  and runtime seed are not pinned.
- Rough query correctness and temporal/state degradation still need an actual
  fixed-prompt runtime run; no score is claimed.
- The final primary event count, checkpoint schedule, and Gate A contract remain
  pending human approval.
- No final benchmark cases, final expected outputs, application code, baseline,
  evaluator implementation, infrastructure, or holdout material was created.
- No `IMPROVEMENT_CHANGELOG.md` entry was added because this was calibration
  design/data preparation, not a scored improvement experiment.
- No authentic coding-agent transcript was available; no transcript was
  fabricated or reconstructed.

## Final decision

`KEEP` the calibration design and dataset as the pre-freeze proposal. Keep Gate
A open until the selected-model run provides correctness/degradation evidence
and the human reviews the length-selection result.

## Related git commits

- Parent contract commit: `f5a6405 benchmark: prepare longitudinal Gate A contract`.
- This task: one coherent documentation/calibration commit,
  `docs: calibrate benchmark size before Gate A`.
