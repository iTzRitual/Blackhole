# Deferred ingestion fake-provider trace

This is a deterministic integration trace, not a provider transcript. It was
produced by `app.tests.test_deferred_ingestion` with a neutral in-memory-style
SQLite fixture and an injected fake semantic provider. No benchmark scenario,
expected output, evaluator data, or provider credentials were supplied.

## Input and initial state

The fixture submitted neutral captures for a renewal date, a changing monthly
cost, an incomplete insurance renewal month, a proposed payment, two identical
purchase captures, and a failure/retry sequence. Each capture was inserted as
an immutable raw event and received a separate `processing_state=pending` row.

## Observable processing

- Capture returned `Saved.` with no provider call and no semantic observations.
- Pending events were claimed in sequence order using bounded batches.
- The fake provider returned only public observations and relationships.
- Correction processing retained the earlier value in history and projected
  the later value as current.
- The incomplete renewal remained `unknown/not_stated`; no exact date was
  fabricated.
- The proposed payment remained a derived proposal; no action was executed.
- Two raw duplicate captures remained present while the duplicate component
  projected one occurrence.
- A provider failure marked the event `failed`, stopped later chronological
  work, preserved prior valid state, and succeeded after `retry_failed()`.
- A second `process_pending()` made zero provider calls and zero semantic
  effects.

## Result

Seven deferred-ingestion tests passed. The test suite recorded successful
processing status, attempt counts, version fields, retry behavior, raw-source
preservation, duplicate count invariants, and ask-time freshness. A real Codex
CLI smoke was not run; the mandatory fake-provider path was sufficient and
provider availability was not required for capture.
