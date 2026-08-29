# Gate A long-chat reassessment summary

## Goal

Reopen and prepare Gate A as a design-only review aligned with the current
master brief: one 60–100-event longitudinal timeline, a fair complete-history
long-chat baseline, zero-maintenance primary query accuracy, and a defensible
maintenance-intervention metric. Do not generate cases or implement the
evaluator, baseline, application, or infrastructure.

## Agent/tool used

Codex with PowerShell, `apply_patch`, Git, and read-only repository inspection.
No provider call, credential access, benchmark generation, evaluator execution,
baseline execution, or holdout access was performed for this task.

## Initial hypothesis

The prior 200-event/v2 design is valuable historical evidence but is not the
right current Gate A freeze target under the new brief. A dense 100-event,
roughly 90-day timeline with ten interleaved changing storylines should better
balance long-horizon state churn, complete-history fairness, and the two-day
hackathon timebox than either a short static case or a context-exhaustion test.

## Important design decisions

- Recommended a 100-event primary, checkpoints 20/40/60/80/100, and an
  optional separate 200-event stress track.
- Kept one synthetic timeline with ten interleaved storylines: subscriptions,
  bills, purchases versus consumption, tasks, insurance, receipts, ambiguous
  entities, correction/conflict, multi-date contracts, and approval boundaries.
- Defined the primary unit as one atomic assertion per checkpoint/query and
  proposed LQA-0M with explicit false-positive penalties and unit weights.
- Defined a public subject/predicate response boundary without evaluator-
  internal `state_key` values, while keeping expected maintenance manifests
  evaluator-owned.
- Proposed deterministic `MIR-90` intervention-equivalent scoring with a
  threshold-not-reached fallback rather than invented human-minute estimates.
- Preserved all prior benchmark, evaluator, baseline, and calibration artifacts
  as historical evidence; no existing case or expected value was rewritten.

## Tools/actions used

- Read the referenced human brief and current `AGENTS.md`.
- Read the current README, product, architecture, decisions, evaluation,
  benchmark, reproduction, calibration, prompt, and prior trajectory documents.
- Inspected the repository history, including the prior design commit
  `d5e9b40` and the later historical execution commits.
- Wrote `docs/GATE_A_PROPOSAL.md` and this coding trajectory.
- Updated repository status documentation to make the reopened human Gate A
  review explicit without changing benchmark facts or implementation code.

## Failures encountered

None during the design review. The main discovered issue was documentation
state drift: current documents described the prior 200-event package and Gate B
repair as approved, while the current human brief explicitly reopened Gate A.

## Retries or changed approaches

No implementation or runtime approach was attempted. The proposal was revised
from the prior 200-event freeze target to the recommended 100-event primary in
response to the current human brief, while retaining the prior artifacts rather
than rewriting or deleting them.

## Human feedback or checkpoints

The current human instruction says the previous contract is not approved,
requires a revised Gate A, prohibits implementation before approval, and asks
for no more than five critical questions followed by `GRILL ME — GATE A`.
Approval is still pending at the end of this task.

## Evaluation performed

No benchmark, evaluator, or model evaluation was run. Read-only validation will
confirm that the change contains design documentation and trajectory records
only, with no new cases, expected outputs, evaluator code, baseline code, app
code, infrastructure, or holdout material.

## Result

The revised Gate A proposal is ready for human review in
`docs/GATE_A_PROPOSAL.md`. It includes the benchmark overview, storylines,
example event/assertions, public data contract, known/inferred/unknown rules,
primary and secondary metrics, deterministic maintenance protocol, holdout
isolation, reproduction plan, and likely weaknesses.

## Regressions or unresolved issues

- The 100-event target may still be short for a very strong long-context model;
  this is explicitly treated as a benchmark limitation and optional stress-track
  question.
- The maintenance-intervention root-defect/repair-footprint manifest requires
  human adjudication before cases are generated.
- Exact provider/model configuration and context behavior remain to be pinned
  after Gate A approval.
- Existing 200-event/v2 execution artifacts remain historical and should not be
  called current Gate A approval.

## Final decision

**PENDING HUMAN REVIEW.** Do not generate benchmark cases, freeze the response
contract, implement the evaluator or baseline, or begin the advanced system
until the five Gate A questions in the proposal are answered.

No authentic coding-agent transcript was available or fabricated.

## Related git commit

`docs: reopen Gate A long-chat benchmark review` (this commit)
