# Summary

## Status

Completed after focused tests, FAST replay, full public replay, documentation
audit, and one coherent commit.

## Goal

Repair the E001 response projector's benchmark-specific entity routing while
preserving the frozen Gate A benchmark and the validated state-projection
evidence.

## Initial finding

The committed projector contained literal synthetic subject identifiers and
question branches for several public benchmark storylines. This violates the
experiment's requirement that the state-maintenance mechanism be generic.

## Scope boundary

No benchmark cases, expected values, response-contract-v2, evaluator behavior,
official baseline-v1 result, calibration evidence, or holdout material will be
changed.

## Agent/tool used

Codex used PowerShell, `apply_patch`, Python unit-test/replay commands, the
existing SQLite state/replay harness, and the unchanged public evaluator. No
provider authentication or provider calls were used for this repair.

## Initial hypothesis

Selecting subjects by public ontology kind, routing by generic query-family
vocabulary, and filtering event relations using observation semantics would
remove benchmark-specific coupling while preserving the validated E001 state
quality.

## Important implementation decisions

- Added ontology-kind subject discovery and aggregate-subject selection to the
  deterministic projector.
- Generalized subscription, insurance, contract, observation, service, and
  merchant projections to operate over all subjects of the relevant public
  kind. Service and merchant calculations now group results per subject.
- Replaced brand-name query routing with generic terms such as policy, bill,
  purchase, consumption, contract, and approval.
- Kept arithmetic, date handling, state transitions, and response shaping
  deterministic. Entity-link-only event endpoints are excluded from duplicate
  or change capture projections because they are not receipt-like evidence.
- Added generic unit fixtures using synthetic neutral subject names. The
  projector contains no benchmark entity IDs or brand names.

## Tools/actions used

- Audited `AGENTS.md`, the frozen public contract/query bundle, the current
  projector, existing E001 artifacts, and repository status.
- Created this coding trajectory before implementation.
- Edited `app/response_projector.py` and
  `app/tests/test_response_projector.py` with `apply_patch`.
- Added E002 evidence to `IMPROVEMENT_CHANGELOG.md`, `docs/DECISIONS.md`,
  `docs/ARCHITECTURE.md`, `docs/EVALUATION.md`, `docs/REPRODUCTION.md`, and
  `README.md`.
- Recorded final FAST and full runtime summaries under
  `trajectories/runtime/experiment-002-generic-fast/` and
  `trajectories/runtime/experiment-002-generic-full/`.

## Failures encountered

The first full replay of the broad source-type-agnostic duplicate rule scored
`LQA-0M=0.7472666121` with `DSCR=82` because entity-link-only similarity chains
were counted as capture duplicates. This was a projector regression, not a
benchmark or evaluator failure.

## Retries or changed approaches

The duplicate filter was tightened to reject endpoints whose observed
predicates consist only of `entity_link`. The same recorded semantic extraction
was replayed again. No provider prompt, baseline prompt, benchmark, expected
output, or evaluator code was tuned or changed.

## Human feedback or checkpoints

The authorized project direction keeps Gate A frozen at 200 events with
50/100/150/200 checkpoints, keeps Gate B and `response-contract-v2` valid, and
preserves the official `baseline-v1`. Advanced application experimentation is
authorized; holdout material and production infrastructure remain prohibited.

## Evaluation performed

- `python -m unittest discover -s app/tests -v`: 15 tests passed.
- Final FAST public replay and unchanged `eval.score_slice`: `LQA-0M=0.8888888889`, `DSCR=4`, no hard failure.
- Final full public replay and unchanged `eval.score.py`: `LQA-0M=0.7492295899`, checkpoint scores `0.7962962963 / 0.7523071836 / 0.7064078283 / 0.7419070513`, `DSCR=72`, totals `TP=279, FP=69, FN=96`.
- Full replay schema, safety, and source-integrity checks passed. Both final
  replays used zero provider tokens and no new provider calls.
- The full E002 result is numerically identical to the preserved E001 v4
  result. The official baseline remains `LQA-0M=0.3014914553`, `DSCR=277`.

## Result

The hypothesis was supported. The projector is generic with respect to public
ontology subject names, while the final full public replay preserves the E001
score exactly. The repair adds no official benchmark or baseline treatment.

## Regressions or unresolved issues

The broad first relation filter was rejected and is not the final behavior. No
remaining regression from this repair was observed. Relation-detail recall
remains the next evidence-backed application weakness, as documented in E001;
this task did not attempt to solve it.

## Final decision

**KEEP.** Keep the genericity repair and its evidence. Preserve all prior E001
artifacts, the frozen benchmark, response contract, evaluator, calibration
evidence, and official baseline unchanged.

## Related git commit

This trajectory is finalized in the single coherent commit
`experiment: generalize state projections`; its final SHA is reported in the
task handoff.

No authentic session transcript is available; no transcript is fabricated.
