# Gate B contract diagnostic

This is a diagnostic of the preserved `baseline-v0` run. It does not alter the
public benchmark facts or expected values. The raw model responses are in
`trajectories/runtime/002-baseline-v0/`; the v1 score is historical invalid
evidence only.

## Findings

| Representative observation | Classification | Why it matters | Repair decision |
| --- | --- | --- | --- |
| The model used descriptive dotted keys such as `subscription.streamly.current` while the evaluator required exact colon/slash keys such as `subscription:streamly/current_price`. | C — evaluator-internal ID mismatch; also B for output shape | The public v1 contract did not expose a derivable slot grammar. Semantically plausible assertions received no match. | Replace candidate `state_key` with public `subject` + `predicate`; canonicalize both sides deterministically. |
| Current subscription answers were often emitted as one object containing status, price, and renewal instead of separate typed assertions. | B — response representation/granularity | The model answered the question in a reasonable report shape, but v1 compared atomic hidden slots. | Require atomic v2 assertions and compare public semantic tuples; do not use an LLM judge. |
| At checkpoint 50 the model treated the announced 14.00 EUR price as not yet current and labeled its 12.00 EUR current price as inferred. | A/F — true temporal/knowledge-status error | This is a genuine state-reconciliation and status error visible from the public history, independent of identifier spelling. | Preserve as a valid-baseline failure if it recurs; do not change expected state. |
| Unknown assertions sometimes included a `value` alongside `knowledge_status: unknown`. | B/F — schema and knowledge-status violation | The value is not a valid unknown representation, even when its explanation is useful. | v2 requires unknown assertions to omit `value` and include `unknown_reason`. |
| Orange totals and MarketOne totals were commonly reported as grouped summaries with numeric amounts rather than the v1 atomic fields and decimal strings. | B/D — granularity and value normalization | Some arithmetic appears consistent, but v1 could not distinguish grouping, numeric formatting, and semantic error. | v2 defines public predicates, deterministic decimal/date normalization, and atomic aggregate assertions. |
| Duplicate answers used phrases such as “duplicate capture count” and grouped pair lists; at early checkpoints the count represented both members rather than duplicate uploads only. | A/C — semantic count error plus v1 key mismatch | The query wording did not repeat the frozen `duplicate_event_count` definition, and the model’s early count was not the required measure. | Repeat the exact duplicate-count rule in the public v2 query instructions; keep expected counts unchanged. |
| Task and unresolved answers used broad history objects and aggregate identity explanations rather than one assertion per task/mention. | B, with possible A — representation ambiguity; semantic correctness cannot be fully isolated | The content can contain correct evidence while omitting or merging scorable slots. | Use atomic public subjects/predicates and retain exact source references; score any remaining omissions as ordinary recall/state errors. |
| The parser’s list-to-object compatibility path was not the main cause: preserved raw responses already had a 12-key query object. | B — harmless parser compatibility | The outer query container was not the substantive v1 failure in this run. | Keep parser diagnostics explicit; do not silently reinterpret assertion semantics. |

## Conclusion

The v1 result is invalid as an official semantic baseline because the public
answer contract did not provide a fair, derivable representation of assertion
identity. The repair changes only the measurement interface: public ontology,
atomic semantic assertions, deterministic normalization, and explicit schema
diagnostics. It does not change raw events, checkpoint cutoffs, expected values,
duplicate facts, or the substantive `baseline-v1` life-admin prompt.

The corrected run reports genuine errors under a non-zero, schema-valid score:
the official v2 result is `LQA-0M=0.3014914553` with `TP=146`, `FP=239`, and
`FN=229`. The full Gate B report records which misses are semantic and confirms
that the interface no longer produces the v0 all-zero artifact.
