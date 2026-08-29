# Runtime trajectory summary: baseline-v1

## Run identity

- Treatment: official corrected fair Codex CLI baseline
- Scenario: `blackhole-dev-001-state-churn`
- Contract: `response-contract-v2`
- Model: `gpt-5.6-luna`
- Reasoning effort: `max`
- CLI: `0.150.0-alpha.12.2` (safe basename recorded by the runner)
- Sandbox: read-only, fresh temporary workspace, no Blackhole application state
- Authentication: existing local Codex subscription; no credential value was read or persisted

## Input and state before execution

The runner supplied the unchanged public 200-event scenario chronologically in
four batches: 1–50, 51–100, 101–150, and 151–200. The canonical session
received the unchanged substantive `baseline-v1` life-admin prompt and the v2
runner instruction. It received no expected output, generator metadata,
defect catalog, evaluator code, database, retrieval layer, calibration oracle,
or holdout material.

## Checkpoint protocol

At checkpoints 50, 100, 150, and 200, the runner used the native atomic Codex
CLI fork operation, supplied the public v2 contract and fixed public query
bundle, recorded the response, and discarded the child. No query fork was
resumed into canonical ingestion. All four responses parsed as v2 JSON with all
12 query IDs; the evaluator reported zero schema errors.

## Result

The deterministic evaluator recorded `LQA-0M=0.3014914553`, checkpoint mean
scores `0.2894 / 0.2669 / 0.3127 / 0.3369`, and totals `TP=146, FP=239, FN=229`.
DSCR was `277` (`138.5` per 100 events). Source integrity passed, safety
passed with zero violations, and the v2 response schema was valid. Category and
runtime detail is in `docs/GATE_B_VALID_REPORT.md` and
`eval/results/baseline-v1.json`.

## Runtime and usage

Canonical capture turns took `16.781` seconds total. Query forks took
`753.250 / 587.500 / 546.860 / 586.125` seconds at checkpoints
`50 / 100 / 150 / 200`, for `2,490.516` seconds total including capture.
Provider-reported total usage was `280,425` input tokens and `205,068` output
tokens, including canonical turns. Query-fork input/output tokens were
`28,311/62,512`, `34,391/48,661`, `40,487/45,265`, and `46,579/48,544`.
Subscription dollar pricing was not exposed and was not inferred.

## Interpretation and unresolved limits

The repaired interface is valid, so the remaining errors are semantic rather
than v1 state-key/schema failures. Relations and entity resolution were the
weakest areas; task/current-state/attention and temporal reconciliation also
showed persistent errors. The single run's checkpoint means did not decrease
monotonically, so it does not prove a history-length degradation curve. A
single scenario/run must not be generalized beyond this benchmark.

No authentic provider transcript was exported. The JSON checkpoint files are
the representative runtime artifacts; this summary does not fabricate a
transcript or hidden reasoning.
