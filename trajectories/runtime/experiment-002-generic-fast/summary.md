# Experiment 002 genericity repair — FAST replay

This runtime trajectory is a deterministic replay, not a fresh model
transcript. It uses the public 50-event prefix, `response-contract-v2`, and
the previously recorded E001 extraction for the first 50-event batch.

## Execution

- State before execution: empty temporary SQLite state.
- Ingestion: one replayed semantic extraction batch; raw captures were inserted
  into the append-only store and the projection was rebuilt.
- Query path: deterministic response projection using public ontology kinds and
  generic query-family routing.
- Provider calls: none; input/output/reasoning token usage was zero.
- Query slice: subscriptions current/history, 14-day attention, and recent
  changes.

## Result

The unchanged development slice scorer reported `LQA-0M=0.8888888889`,
`DSCR=4`, and no hard failure. This is a non-official diagnostic and does not
change the frozen benchmark or official baseline.
