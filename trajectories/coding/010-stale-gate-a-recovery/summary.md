# Stale Gate A recovery summary

## Goal

Recover the effect of the unapproved stale Gate A reassessment commit while
preserving that commit in git history and restoring the valid Gate B state.

## Agent/tool used

Codex using PowerShell, `apply_patch`, and local Git/Python validation tools.
No provider runtime or external service was used.

## Initial hypothesis

The stale commit is a documentation-only reopening of Gate A. Reverting its
effect should restore the valid `e3eff67` benchmark, response contract,
baseline, and evaluator state without changing benchmark or runtime artifacts.

## Important implementation decisions

This is a workflow/recovery event, not a benchmark experiment. The stale
commit will remain visible in history; its effect will be reversed with
`git revert --no-commit aa359c5`. The official 200-event benchmark, frozen
response contract, baseline-v1 result, evaluator behavior, and calibration
evidence remain protected.

The recovery cause was:

> Previously achieved Goal was manually resumed and executed stale planning instructions that reopened an already completed Gate A.

## Tools/actions used

Created this trajectory before changing the repository. Applied
`git revert --no-commit aa359c5`, then restored a narrow active-phase
clarification in the current guidance and status documents: Gate A remains
frozen, Gate B remains valid, the official baseline remains `baseline-v1`, and
advanced Blackhole application experimentation is the next authorized phase.
The clarification explicitly keeps the benchmark, evaluator, baseline,
calibration evidence, production infrastructure, Claude adapter, and holdout
boundary unchanged or prohibited as applicable.

The stale proposal and its coding trajectory were removed by the inverse of
`aa359c5`; the stale commit itself remains in history. No application,
benchmark-case, evaluator, infrastructure, or provider-runtime code was added
or changed.

## Failures encountered

The first combined PowerShell baseline comparison reported a false failure
because command exit statuses were used as Boolean expressions. The two Git
comparisons were rerun with explicit `$LASTEXITCODE` checks and passed. No
repository artifact was changed by the failed check.

## Retries or changed approaches

Replaced the combined Boolean-style shell check with separate explicit Git
exit-status checks. The recovery method itself was not changed: the stale
commit was reversed with `git revert --no-commit`.

## Human feedback or checkpoints

The human decision is that Gate A is not reopened, Gate B response-contract
repair is valid, baseline-v1 is the official baseline, and advanced
Blackhole experimentation is the next authorized phase.

## Evaluation performed

`python benchmark/dev/generate_benchmark.py --check` passed with `200 events`
and `4 checkpoints`. The evaluator test suite passed: `9` tests in `2.137s`.

The official baseline artifacts were checked against `e3eff67`:

- `eval/results/baseline-v1.json` Git blob:
  `e4e8e4e2803b06f6c975e126522bf44a64f401a0`
- `eval/results/baseline-v1-candidate.json` Git blob:
  `33353d79f76d591014ca914187e099dbce20eb2a`

Both current blobs match the corresponding `e3eff67` blobs. The JSON content
check confirmed `response-contract-v2`, official `LQA-0M=0.30149145529538973`,
checkpoint means `0.28938492063492066 / 0.26693214193214193 /
0.3127209711288995 / 0.33692778748559676`, totals `TP=146`, `FP=239`,
`FN=229`, DSCR count `277`, valid source integrity, passed safety, and no hard
failure.

The active documentation scan confirmed the frozen 200-event Gate A,
50 / 100 / 150 / 200 checkpoints, valid Gate B response-contract repair,
official baseline, and next authorized advanced-experiment phase. The stale
Gate A proposal and reassessment trajectory are absent from the resulting
tree. Staged and working-tree whitespace checks passed.

## Result

The stale Gate A reopening is discarded while its commit remains visible in
history. The valid pre-stale state is restored for benchmark, evaluator,
response-contract, baseline, and calibration artifacts, with the human-
authorized advanced-experiment transition stated explicitly in active docs.

## Regressions or unresolved issues

No benchmark, expected value, response-contract-v2, evaluator, baseline-v1,
or calibration regression was observed. No unresolved repository issue remains
for this recovery task.

## Final decision

KEEP the recovered project state. This was a workflow/recovery event, not a
benchmark experiment, so no improvement-changelog experiment entry or
behavioral KEEP/REVISE/REMOVE comparison is applicable.

## Related git commit

`revert: discard stale Gate A reassessment` (this coherent recovery commit).

No authentic session transcript was available, so no transcript file is
fabricated.
