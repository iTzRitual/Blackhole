# Task summary: benchmark contract design

This summary records the current benchmark-design task and the decisions available before human review. It does not describe an implementation run, and no benchmark cases or evaluator outputs were created.

## Goal

Move Life Inbox from documentation-scaffolding to benchmark-design phase with explicit human authorization, while keeping application and baseline implementation prohibited. Define a reviewable benchmark contract before any development cases or synthetic inputs are created.

## Agent/tool used

The work was performed by the Codex coding agent using local file inspection, patch-based edits, PowerShell checks, and Git. No application runtime, model evaluation, external service, or evaluator was used.

## Initial hypothesis

Not applicable. This is a design task, not a benchmark experiment.

## Important design decisions

- The exact evaluation unit is an isolated, ordered inbox-history scenario for one synthetic person at a fixed cutoff; the scoring atom is a typed canonical state assertion.
- The proposed primary metric is Macro Evidence-State F1 (MES-F1), with scenario-level F1 macro-averaged across scenarios and a hard safety gate for unapproved consequential actions.
- Secondary metrics cover per-type state quality, known/inferred/unknown handling, provenance, source fidelity, temporal and financial correctness, duplicates/changes/corrections, contradictions, attention quality, rebuild consistency, schema validity, safety, and run cost.
- Raw events are immutable, content-addressed source records. Expected final state is evaluator-owned and contains explicit scorable assertions, including required unknowns.
- Every scorable value carries `known`, `inferred`, or `unknown` semantics. Unknown values omit `value` and carry a reason; missing data is never treated as zero, false, empty, or complete.
- Entity links, tasks, obligations, deadlines, financial observations and aggregates, duplicate/change relations, corrections, contradictions, and attention items have typed representations with provenance.
- Scoring is deterministic: canonicalize, flatten, one-to-one match, count TP/FP/FN, compute scenario F1, macro-average, then apply the safety gate. LLMs are not used by the scorer.
- Contradictions remain explicit. Unresolved conflicts score as conflicting/unknown plus a contradiction record; user-confirmed corrections create new records and do not mutate raw events.
- Holdout cases and expected outputs remain evaluator-owned, outside the implementation-agent trust boundary, and are never returned through logs or diagnostics.
- Judges reproduce runs from frozen contract/scorer revisions, content-addressed inputs, versioned prompts/models/configuration, environment metadata, and private evaluator packages.

The complete proposal is recorded in [docs/EVALUATION.md](../../docs/EVALUATION.md#8-proposed-benchmark-contract), pending human approval.

## Tools/actions used

- Read `AGENTS.md`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/EVALUATION.md`, `benchmark/README.md`, and the trajectory guidance before editing.
- Created this coding trajectory and preserved the authentic human instruction in `prompt.md`.
- Updated `AGENTS.md` to authorize benchmark contract design, development benchmark cases, synthetic inputs, and evaluator design while retaining prohibitions on application, baseline, infrastructure, executable evaluator, and holdout-ground-truth work.
- Updated the repository status text and benchmark documentation to reflect the new phase and pending contract review.
- Added the proposed contract to `docs/EVALUATION.md` without creating cases or expected outputs.

## Failures encountered

None.

## Retries or changed approaches

None.

## Human feedback or checkpoints

- The human explicitly approved the phase transition.
- The human explicitly constrained this task to design only and prohibited application and baseline implementation.
- The human required the contract to be proposed for review before any benchmark cases are created.
- The human required the task to stop after presenting the proposal.

## Evaluation performed

- Audited the current documentation for contradictions across agent guidance, product, architecture, decisions, evaluation, benchmark, reproduction, trajectory, changelog, and repository status documents.
- No internal contradictions were found.
- Verified that no benchmark cases, expected outputs, ground truth, application code, baseline implementation, evaluator implementation, or infrastructure were added.
- Formatting and scope checks passed for the task changes.

No benchmark metrics were run because no implementation or cases exist yet.

## Result

The repository is now documented as being in the benchmark-design phase. A concrete benchmark contract is proposed for human review. Development cases and synthetic inputs remain uncreated until the contract is approved; holdout material remains evaluator-owned.

## Regressions or unresolved issues

- The contract is intentionally pending human review and is not yet frozen or versioned as an approved benchmark release.
- No benchmark cases, scorer, evaluator, application, baseline, or infrastructure exist yet.
- No authentic runtime or evaluation results exist.

## Final decision

Pause for human review of the proposed benchmark contract. Do not create benchmark cases or begin application/baseline implementation until the contract is approved.

## Related existing git commits

- `cc51392 docs: scaffold life inbox repository`
- `f1c60ac docs: update agent documentation protocols and task definitions`
