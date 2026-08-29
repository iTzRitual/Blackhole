# Recovery task prompt summary

This is a faithful retrospective summary of the human-authorized recovery
instruction, not a verbatim historical prompt.

The task is to recover from stale planning instructions recorded by commit
`aa359c5` (`docs: reopen Gate A long-chat benchmark review`). That commit is
not approved project direction. Preserve it in history, but revert its effect
using `git revert --no-commit aa359c5`, with `e3eff67` (`benchmark: repair
baseline response contract`) treated as the valid prior state.

The recovered state must keep Gate A frozen at the 200-event benchmark with
50 / 100 / 150 / 200 checkpoints, keep `response-contract-v2` frozen, retain
LQA-0M as the primary metric and DSCR as the maintenance proxy, and not
restore MIR-90. Preserve the official `baseline-v1` result at
LQA-0M `0.3014914553`. Gate B remains valid, and the next authorized phase is
advanced Blackhole application experimentation.

Do not alter benchmark facts, expected values, response-contract-v2,
baseline-v1, evaluator behavior, or calibration evidence. Create this coding
trajectory, document the recovery cause, validate the generator, evaluator
tests, baseline-v1 artifact hashes and contents, repository phase
documentation, and the final clean git state, then make one coherent commit
such as `revert: discard stale Gate A reassessment` and stop.

The recovery cause must be documented exactly as follows:

> Previously achieved Goal was manually resumed and executed stale planning instructions that reopened an already completed Gate A.
