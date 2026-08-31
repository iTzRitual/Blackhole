# Final Product V2 head-to-head report

This is a post-freeze generalization comparison, not a new V1 benchmark and
not a Product V2 optimization result. It uses four newly authored synthetic
worlds, independent of the frozen V1 scenario, Product V2 acceptance fixtures,
private dogfood captures, and evaluator-owned holdout material.

## Sealed run

- Run: `final-h2h-20260831T143014Z`
- Frozen tag: `hackathon-submission-demo-ready`
- Frozen Product V2 commit: `cc0cca8e8d9c3a5ab0955f365ea71c639cac7548`
- Sealed manifest SHA-256: `5b38b14aac4e3f4ab88a7cff6a5d5d411f7275c8579e501a3da0ec7128243393`
- Seed: `20260831`
- Shape: 4 worlds × 20 captures, checkpoints at 7/14/20, 13 total queries
- Runtime: `gpt-5.6-luna`, reasoning `low` for both systems

The ten declared families were current truth, history/correction,
Attention/lifecycle, temporal deadlines, occurrences/aggregation,
uncertainty/contradiction, multilingual retrieval, provenance/thread,
document/payment, and Undo/forget.

## Systems

System A was a fresh stateless raw-memory Codex call for every query. It saw
only the currently live raw captures, timestamps, timezone, question, and a
fixed strict response schema. It had no Blackhole database, derived state,
prior answer, or persistent conversation.

System B was the exact frozen Product V2 application through its normal local
HTTP path: `/api/v2/capture`, background processing, `/api/v2/state`,
`/api/v2/ask`, and `/api/v2/retract` for the Undo case. Each world used a
fresh temporary Home. Expected assertions were withheld from both systems and
read only by the deterministic scorer.

## Semantic results

The score is **PTS (Prompt-to-Truth Score)**: macro F1 across the ten families.
It must not be confused with the frozen V1 `LQA-0M` metric.

| System | Precision | Recall | PTS |
| --- | ---: | ---: | ---: |
| Raw-memory Codex | 0.9750 | 0.7927 | **0.8575** |
| Product V2 | 1.0000 | 0.6873 | **0.7928** |

Product V2 did not lead the aggregate PTS on this small set. It did lead
Attention F1 and maintained an auditable durable state, which are separate
product qualities rather than hidden score adjustments.

### Per-family P/R/F1

| Family | Raw-memory | Product V2 |
| --- | ---: | ---: |
| `current_truth` | 1.0000 / 0.9375 / 0.9677 | 1.0000 / 0.8750 / 0.9333 |
| `history_correction` | 1.0000 / 0.8571 / 0.9231 | 1.0000 / 0.8571 / 0.9231 |
| `attention_lifecycle` | 1.0000 / 0.8000 / 0.8889 | 1.0000 / 0.4000 / 0.5714 |
| `temporal_deadline` | 1.0000 / 0.9000 / 0.9474 | 1.0000 / 0.8000 / 0.8889 |
| `occurrences_aggregation` | 1.0000 / 0.6667 / 0.8000 | 1.0000 / 0.4167 / 0.5882 |
| `uncertainty_contradiction` | 1.0000 / 0.5714 / 0.7273 | 1.0000 / 0.8571 / 0.9231 |
| `multilingual_retrieval` | 1.0000 / 1.0000 / 1.0000 | 1.0000 / 1.0000 / 1.0000 |
| `provenance_thread` | 1.0000 / 0.4167 / 0.5882 | 1.0000 / 0.3333 / 0.5000 |
| `document_payment` | 1.0000 / 0.7778 / 0.8750 | 1.0000 / 0.6667 / 0.8000 |
| `undo_forget` | 0.7500 / 1.0000 / 0.8571 | 1.0000 / 0.6667 / 0.8000 |

Values in each cell are precision / recall / F1. The scorer uses exact
normalized assertions, fixed language markers, explicit unknown/negative
checks, and source-reference checks; it uses no LLM judge or fuzzy similarity.

## Attention

| System | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| Raw-memory Codex | 0.5385 | 0.6154 | 0.5641 |
| Product V2 | 0.6410 | 0.7692 | **0.6795** |

Product V2's active set came from the normal state Attention projection. The
raw-memory comparator returned structured active event IDs in its response.
Completed/cancelled lifecycle items and the post-checkpoint forgotten capture
were evaluated against the case-declared active sets.

## Operational results

| System | Wall time | Query median / max | Query failures | Schema-valid | Codex calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| Raw-memory Codex | 130.878 s | 10.276 / 12.065 s | 0 | 13/13 | 13 |
| Product V2 | 1217.334 s | 30.862 / 39.003 s | 0 | 13/13 | 80 extraction + 13 Ask requests |

Product V2 accepted all 80 captures immediately, processed all 80 on their
first attempt with zero processing failures, and used 80 one-capture
extraction calls in this run despite the normal batch-size-two configuration.
The call count was audited from the unique recorded processing success
boundaries at each world's final checkpoint. The raw-memory call and Product
V2 telemetry collision affected only the post-run logger label; semantic
responses and scores were unchanged.

## Failures and reproducibility

The first harness attempt stopped before producing a valid Product V2 result
because it referenced `query_id` instead of the sealed case schema's
`query_ids` list. The runner was corrected, the unchanged case/spec/scoring
inputs were resealed, and the full comparison was rerun from fresh Homes. No
provider failure, input change, prompt tuning, expected-output change, or
scoring change followed the valid sealed run.

The raw result, sealed cases, expected assertions, schema, and runner remain
in the disposable local clone used for execution. The main repository stores
only the sanitized machine-readable summary at
[`eval/results/final-h2h-001-summary.json`](../eval/results/final-h2h-001-summary.json)
and this report. The runtime evidence is summarized in
[`trajectories/runtime/050-final-h2h/summary.md`](../trajectories/runtime/050-final-h2h/summary.md).

## Decision and limits

**Decision: KEEP the comparison artifact as descriptive evidence; make no
Product V2 or V1 benchmark change.** The result is useful because it exposes a
real trade-off: the raw-memory comparator recalled more of these authored
assertions, while Product V2 provided better Attention set quality, permanent
Undo behavior, durable state, and an inspectable source/derived boundary.

This is not an official holdout, does not establish statistical significance,
does not prove production reliability, and does not replace the frozen V1
result. Four small synthetic worlds cannot represent the full range of real
personal language, documents, or operational load.
