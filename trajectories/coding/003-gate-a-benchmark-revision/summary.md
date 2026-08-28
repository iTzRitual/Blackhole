# Task summary: Gate A benchmark-contract revision

This summary records the benchmark-design revision driven by the master-goal text in the referenced pasted file. It is not an implementation report and does not fabricate benchmark results, cases, or a transcript.

## Goal

Re-evaluate the previous unapproved benchmark-contract draft against the long-horizon hackathon goal, especially the fair one-long-chat baseline, longitudinal timeline, zero-maintenance primary evaluation, and human-maintenance secondary metric. Prepare Gate A for human review while keeping application and baseline implementation prohibited.

## Agent/tool used

The work was performed by the Codex coding agent using local file inspection, patch-based edits, PowerShell checks, and Git. The referenced pasted task file was read before continuing. No application runtime, model evaluation, external service, or evaluator was used.

## Initial hypothesis

The previous `d5e9b40` contract draft was not aligned with the master goal because it made final-state MES-F1 the primary metric and described mostly isolated scenario scoring. The revision therefore makes zero-maintenance longitudinal query accuracy primary and retains final-state assertion scoring only as a possible diagnostic. This is a design hypothesis, not a measured experiment.

## Important design decisions

- The benchmark unit is one isolated synthetic life timeline, with checkpoint query bundles and weighted atomic assertions as the scoring units.
- The proposed primary metric is Longitudinal Query Accuracy at Zero Maintenance (LQA-0M): correct weighted query assertions divided by total expected weighted assertions, reported overall and at 20, 40, 60, and final checkpoints.
- The proposed timeline targets approximately 80 interleaved events over 90 synthetic days, within the requested 60–100 event range.
- The fair baseline is one continuous general-purpose AI conversation with the same chronological captures, complete history whenever it fits, no structured memory or external state, and recorded token usage. Context overflow is a separate stress condition.
- The proposed secondary maintenance metric is MIR-90: the minimum deterministic canonical assertion repairs needed to reach 90% LQA-0M, with detected intervention count as the fallback if dependency mapping is not reliable within the timebox.
- Storylines cover changing subscriptions, incomplete bills, purchases versus consumption, reassigned tasks, authoritative/replacement insurance, duplicate versus changed receipts, irrelevant notes, ambiguous entities, contradictions/corrections, multi-date contracts, financial observations, and approval-required actions.
- Raw events remain immutable and content-addressed. Expected final state and checkpoint query assertions remain evaluator-owned and include explicit known, inferred, and unknown semantics.
- Deterministic scoring handles exact dates, decimals, IDs, statuses, duplicate relations, contradictions, and missing information; no LLM judge is used for those values.
- Holdout inputs and expected outputs remain outside the implementation-agent trust boundary.

## Tools/actions used

- Read the referenced master-goal file before continuing.
- Inspected the current worktree, `AGENTS.md`, `docs/EVALUATION.md`, `benchmark/README.md`, and recent Git history.
- Created `trajectories/coding/003-gate-a-benchmark-revision/prompt.md` with the authorized task extract.
- Replaced the unapproved MES-F1-led proposal in `docs/EVALUATION.md` with the Gate A long-horizon contract proposal.
- Updated `benchmark/README.md` to point to the Gate A contract and long-horizon shape.
- Did not create benchmark cases, expected outputs, ground truth, application code, baseline code, evaluator code, or infrastructure.

## Failures encountered

An initial patch attempt to replace `docs/EVALUATION.md` reported that the file was missing. A worktree inspection confirmed the file had been removed by that attempted replacement, so the revised document was recreated from the content read earlier. A subsequent benchmark-README patch was rejected because its context used a stale anchor; the file was re-read and patched against its exact current text.

## Retries or changed approaches

After the patch inconsistencies, the approach changed to explicit worktree inspection followed by full-file recreation for `docs/EVALUATION.md` and exact-context patching for `benchmark/README.md`. No design decision changed because of these retries.

## Human feedback or checkpoints

- The master-goal instruction explicitly revoked approval of `d5e9b40` and classified that contract as a draft.
- The human-required correction prioritizes a fair long-chat baseline, one long synthetic timeline, zero-maintenance query accuracy, and maintenance burden.
- Gate A must be prepared and then stopped for human review before cases, baseline, or application work.

## Evaluation performed

- Compared the previous contract against the master-goal requirements.
- Audited the revised documentation for consistency of phase, metric, timeline, baseline, missing-data, contradiction, holdout, and reproduction rules.
- Verified the proposal contains a benchmark overview, storyline list, illustrative event, illustrative expected assertions, metric formulas, maintenance protocol, holdout protection, judge reproduction plan, and likely weaknesses.
- No benchmark metrics were run because no implementation or cases exist.

## Result

The repository now contains a Gate A benchmark-contract proposal aligned to the long-chat/longitudinal/zero-maintenance goal. The repository remains design-only. No actual cases have been created.

## Regressions or unresolved issues

- The contract is pending human approval and is not frozen.
- Timeline size, checkpoint schedule, assertion weights, MIR-90 proxy, baseline protocol, and ground-truth adjudication require Gate A confirmation.
- One synthetic timeline has limited statistical power; fixed queries, subjective obligations/inferences, and the maintenance proxy are documented benchmark weaknesses.
- No application, baseline, evaluator, benchmark data, or evaluation results exist yet.

## Final decision

Enter `GRILL ME — GATE A` and stop. Do not create benchmark cases or implement the baseline/application until the human approves the revised contract.

## Related git commits

- `cc51392 docs: scaffold life inbox repository`
- `d9d7698 docs: record design scaffold trajectory`
- `d5e9b40 docs: define benchmark design contract` (draft revised by this task)
- `f1c60ac docs: update agent documentation protocols and task definitions`
