# Final deterministic advanced replay

This is a recorded public-development replay, not a fresh provider transcript.
It reuses the already-recorded Experiment 001 extraction outputs and evaluates
the kept generic Experiment 002 projector.

## Input and configuration

- Scenario: `blackhole-dev-001-state-churn`.
- Events: 200, processed in chronological batches of 50.
- Checkpoints: 50, 100, 150, 200.
- Contract: `benchmark/dev/response-contract-v2.json`.
- Replay source: `trajectories/runtime/experiment-001-full-v1/`.
- Query mode: deterministic projection; no model query.

## Operations and result

- Four recorded extraction prefixes were replayed into append-only SQLite state.
- Four deterministic query projections were generated.
- Reported provider usage: 0 input, 0 output, and 0 reasoning tokens.
- Final state counts: 83 current facts, 279 historical observations, and 124
  relationships.
- Scored result: `LQA-0M=0.7492295898545899`, `DSCR=72`.
- Checkpoint scores: 50=`0.7962962962962963`,
  100=`0.7523071835571836`, 150=`0.7064078282828282`,
  200=`0.7419070512820513`.
- Schema validity, source integrity, and safety checks passed.

## Evidence

The candidate and deterministic score are
`eval/results/final-advanced-candidate.json` and
`eval/results/final-advanced.json`. The final comparison with the unchanged
official baseline is `eval/results/final-comparison-v1.json`.

This replay does not change the frozen benchmark, expected values,
`response-contract-v2`, official `baseline-v1`, or calibration evidence.
