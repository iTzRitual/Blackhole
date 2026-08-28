# Size calibration report

**Status:** preliminary, non-scored, pending the selected-model run.

## Question

Does state quality fall as a changing longitudinal history grows while the
complete history is still reasonably available to the model? The calibration
is not intended to maximize context consumption.

## Dataset result

The deterministic generator produced four prefixes—50, 100, 200, and 400
events—from one calibration-only stream. The stream has ten evolving
storylines and does not reuse the final benchmark narrative or ground truth.

| Prefix | Approx. history tokens | Approx. final input tokens | Churn observations |
| ---: | ---: | ---: | --- |
| 50 | 4,109 | 4,611 | 48 accepted updates, 1 correction, 1 contradiction, 1 ambiguity |
| 100 | 8,223 | 8,725 | 95 accepted updates, 2 corrections, 2 contradictions, 1 duplicate |
| 200 | 16,482 | 16,984 | 188 accepted updates, 4 corrections, 5 contradictions, 3 duplicates |
| 400 | 32,995 | 33,497 | 374 accepted updates, 9 corrections, 11 contradictions, 7 duplicates |

Across the prefixes there are also repeated cancellations, ten explicit
missing secondary fields, and uneven observation gaps. The 400-event cutoff
ends with one unresolved contradiction, so the calibration includes a final
unknown rather than silently selecting one conflicting value.

The token figures use `ceil(serialized characters / 4)` plus 160 fixed
system/protocol tokens and an estimated 342-token query bundle. Replace them
with the selected model tokenizer before the model run.

## Context-fit planning

Using a conservative 75% usable-context budget, the 50-, 100-, and 200-event
prefixes fit within a 32k context; the 400-event prefix does not. All four fit
within 64k, 128k, or 200k under that planning rule. This is a planning matrix,
not a claim about the eventual selected model. The selected model's documented
context limit and actual tokenizer must be recorded before Gate A is frozen.

## Query-correctness run still required

No model correctness score is reported here. The repository does not yet pin a
model/provider/context configuration, and no baseline or evaluator has been
implemented. The frozen prompt and run matrix are prepared in
[`prompts/runtime/baseline-v1.md`](../../../prompts/runtime/baseline-v1.md) and
[`RUNTIME_CALIBRATION.md`](RUNTIME_CALIBRATION.md). Reporting a score from the
coding agent itself would not be a valid measurement of the intended runtime
setup.

The authorized calibration run should use one unchanged prompt and one fixed
query bundle at all four sizes. Compare typed answers with the calibration-only
oracle and report:

- current-value accuracy;
- previous-value accuracy;
- known/inferred/unknown accuracy;
- relation accuracy for corrections, contradictions, duplicates, and
  ambiguities;
- stale-value, false-certainty, and conflict-collapse counts; and
- accuracy delta from 50 events to each longer prefix.

The prompt and model configuration must remain fixed across sizes. A failure
may be recorded as evidence of degradation, but it must not trigger prompt
tuning during calibration.

## Estimated execution envelope

One final query bundle at each size is four model calls and approximately
63,817 input tokens. Three repetitions for variance would be twelve calls and
approximately 191,451 input tokens, excluding output tokens. The 400-event
call is approximately 1.97 times the input volume of the 200-event call.
Local generation completed in under one second in this workspace; model
latency and cost will dominate. Exact currency cost is deferred until model
pricing and output limits are pinned.

## Gate A recommendation

Keep the preferred primary target at approximately 150–200 events pending the
fixed-prompt model run. Choose the smallest length in that band that produces
a repeatable state-quality decline while remaining inside the selected model's
usable context and execution budget. Treat 400 as a secondary stress candidate.

If degradation appears only with truncation or context overflow, it is a
context-stress result and should not replace the realistic primary. If no
degradation appears through 400, review churn design with the human owner
before increasing event count; do not inflate the benchmark solely to exhaust
the context window.

An approximately 800-event continuation is not generated or run yet. It may be
considered once, only if the actual 400-event run fits comfortably, remains
practical, and shows little degradation; it remains calibration evidence and
cannot replace the realistic primary benchmark.
