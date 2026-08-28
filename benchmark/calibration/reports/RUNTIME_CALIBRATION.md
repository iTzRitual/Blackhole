# Gate A runtime calibration report

**Status:** Blocked pending a usable runtime provider/API configuration.

This is a report template and preparation record. No model correctness result is
claimed yet. The non-scored calibration histories and visible calibration-only
oracles are in the sibling directories. The frozen prompt is
[`prompts/runtime/baseline-v1.md`](../../../prompts/runtime/baseline-v1.md).

## Runtime configuration to record

| Field | Value |
| --- | --- |
| Provider | **pending** |
| Exact model identifier | **pending** |
| API base/endpoint, if non-default | **pending** |
| Credential availability | **pending; do not record secret values** |
| Documented context limit | **pending** |
| Tokenizer/token-counting method | **pending** |
| Temperature and generation settings | **pending** |
| Max output tokens | **pending** |
| Retry/concurrency policy | **pending** |
| Input/output pricing reference | **pending** |
| Baseline prompt revision | `baseline-v1` |

The same exact semantic model should be used for baseline and advanced semantic
reasoning calls where practical. The baseline has no structured state, hidden
summary, retrieval, or specialized reconciliation tools.

## Required run matrix

Run the same frozen prompt and fixed calibration query bundle against the complete
history at each prefix. Do not silently summarize or truncate a history that fits.

| Events | Input tokens | Output tokens | Context utilization | LQA-style score | Current errors | Stale errors | Previous errors | Missed corrections | Contradiction collapse | False certainty / UNKNOWN errors | Duplicate/change errors | Runtime | Cost | Notes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 50 | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | |
| 100 | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | |
| 200 | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | |
| 400 | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | pending | |
| 800 | not run unless authorized by the documented condition | | | | | | | | | | | | | |

Use deterministic canonical assertion comparison against the calibration-only
oracle. For each query:

```text
TP = correct supported assertions
FP = unsupported or incorrect assertions produced
FN = expected assertions omitted
query_score = TP / (TP + FP + FN)
```

When both expected and produced assertion sets are empty, `query_score = 1.0`.
When exactly one is empty, the score is `0.0`. LQA-0M is the arithmetic mean of
all fixed query scores across the primary checkpoints.

## Interpretation

Separate:

1. context exhaustion, truncation, or request rejection; from
2. state-maintenance degradation while the complete history remains available.

Only the second is evidence for the main benchmark hypothesis. A larger history
must not become the primary benchmark merely because it causes context failure.

After the zero-maintenance run, DSCR is the number of distinct underlying state
defects requiring correction, with repeated query symptoms counted once. Report
total DSCR, DSCR per 100 events, and correction categories; do not equate DSCR
with human minutes.

## 800-event condition

Do not generate or run the 800-event extension unless the 400-event run fits
comfortably in the selected model context, remains practical in cost/runtime,
and shows little or no meaningful state-quality degradation. If authorized, use
a prefix-compatible continuation and run it at most once before human review.
