# Size calibration report

**Status:** complete as preliminary, non-scored calibration evidence; Gate A
remains open for human review.

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
| 50 | 5,159 | 5,678 | 48 accepted updates, 1 correction, 1 contradiction, 1 ambiguity |
| 100 | 10,323 | 10,842 | 95 accepted updates, 2 corrections, 2 contradictions, 1 duplicate |
| 200 | 20,682 | 21,201 | 188 accepted updates, 4 corrections, 5 contradictions, 3 duplicates |
| 400 | 41,395 | 41,914 | 374 accepted updates, 9 corrections, 11 contradictions, 7 duplicates |

Across the prefixes there are also repeated cancellations, ten explicit
missing secondary fields, and uneven observation gaps. The 400-event cutoff
ends with one unresolved contradiction, so the calibration includes a final
unknown rather than silently selecting one conflicting value.

The token figures use `ceil(serialized characters / 4)` plus 160 fixed
system/protocol tokens and a 359-token query-bundle estimate. The selected CLI
did not expose its tokenizer; provider-reported usage is recorded separately in
[`RUNTIME_CALIBRATION.md`](RUNTIME_CALIBRATION.md).

## Context-fit planning

Using a conservative 75% usable-context budget, the 50-, 100-, and 200-event
prefixes fit within a 32k context; the 400-event prefix does not. All four fit
within 64k, 128k, or 200k under that planning rule. The local Codex CLI did not
expose a documented context limit. All four complete histories were accepted
without a context-warning or truncation signal, so the runtime result is
empirical fit evidence rather than a percentage of a known model window.

## Query-correctness result

The Codex CLI runtime was pinned for this calibration, but no baseline or
evaluator application was implemented. The frozen prompt and run matrix are
recorded in
[`prompts/runtime/baseline-v1.md`](../../../prompts/runtime/baseline-v1.md) and
[`RUNTIME_CALIBRATION.md`](RUNTIME_CALIBRATION.md). The detailed deterministic
readout is in that runtime report. In brief, LQA-style scores were 0.8167,
0.9000, 0.8545, and 0.8091 at 50, 100, 200, and 400 events. State-only means
were 0.8889, 1.0000, 0.9394, and 0.8788. The only systematic relation error
was duplicate-count overestimation; missing/unknown handling was correct at all
sizes.

The query and model configuration remained fixed across sizes. An early 50-event
pilot used an earlier query wording that asked for an unobservable field name;
it was discarded and the clean 50-event run was repeated after the query bundle
was corrected. The baseline prompt was not tuned from that pilot or from any
later calibration failure.

## Estimated execution envelope

One final query bundle at each size is four persistent-session model turns and
approximately 79,635 planning input tokens. Three repetitions for variance
would be twelve turns and approximately 238,905 planning input tokens, excluding
output tokens. The observed 400-event run took about 576 seconds versus about
277 seconds for 200. Local generation completed in under one second in this
workspace; model latency and reasoning dominated. Exact currency cost was not
exposed by the subscription CLI.

## Gate A recommendation

Keep the preferred primary target at approximately 150–200 events. The current
provisional choice is 200 events because it exercises substantial state churn
within the realistic target and remains much more practical than 400. Treat 400
as a secondary stress candidate: it was accepted without a context warning but
showed additional current/previous-state errors and took about 9.6 minutes.

The measured curve is non-monotonic and only one run per size was made, so the
evidence does not establish repeatable degradation. Human review is required
before the final benchmark length is frozen.

If degradation appears only with truncation or context overflow, it is a
context-stress result and should not replace the realistic primary. If no
degradation appears through 400, review churn design with the human owner
before increasing event count; do not inflate the benchmark solely to exhaust
the context window.

The optional 800-event continuation was not run: the 400-event condition of
comfortable runtime and little or no degradation was not met. It remains
calibration-only and cannot replace the realistic primary benchmark.
