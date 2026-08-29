# Experiment 002 genericity repair — full public replay

This runtime trajectory is a deterministic replay, not a fresh model
transcript. It uses the frozen 200-event public scenario, the unchanged
`response-contract-v2`, and all four recorded E001 semantic extraction
outputs. No expected output was supplied to the application runner.

## Execution

- State before execution: empty temporary SQLite state.
- Ingestion: four chronological 50-event segments, each replayed from the
  corresponding E001 extraction record; raw captures and derived history were
  rebuilt in the scoped store.
- Checkpoints: 50, 100, 150, and 200.
- Query path: deterministic response projection using public ontology kinds,
  generic query-family routing, and observation-semantic relation filtering.
- Provider calls: none; input/output/reasoning token usage was zero.

## Result

The unchanged public evaluator reported `LQA-0M=0.7492295899`, checkpoint
scores `0.7962962963 / 0.7523071836 / 0.7064078283 / 0.7419070513`,
`DSCR=72`, and totals `TP=279, FP=69, FN=96`. Schema validity, source
integrity, and safety checks passed. The result is numerically identical to
the E001 v4 replay and is not an official baseline result.

The first generic replay was intentionally retained as an intermediate coding
experiment record: its broad event filter counted entity-link-only chains as
duplicates. The final projector tightened that rule and was replayed into this
trajectory. No holdout material or authentic model transcript is present.
