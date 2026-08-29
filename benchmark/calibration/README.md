# Benchmark size calibration

**Status:** non-scored calibration data and Codex CLI runtime calibration complete;
Gate A remains open for human review and is not frozen.

This dataset measures whether longitudinal state quality degrades as changing
history accumulates while the history remains reasonably available to the
model. It is deliberately separate from `benchmark/dev/` and
`benchmark/holdout/`, and it must not be used to tune a baseline prompt.

The calibration stream is independent of the proposed Blackhole storylines
and contains no final-benchmark ground truth. It uses ten fictional entities
(`Aster` through `Jade`) with simple changing fields. The four histories are
prefixes of one deterministic 400-event stream so size comparisons are
comparable, not four unrelated samples.

## Contents

- `histories/history-050.jsonl`, `history-100.jsonl`, `history-200.jsonl`, and
  `history-400.jsonl` contain immutable-looking synthetic raw text events.
- `oracle/oracle-*.json` contains calibration-only expected state and query
  answers. It is intentionally not an official benchmark scorer or holdout.
- `query-bundle.md` freezes the calibration-only query wording and response
  semantics used for every size.
- `reports/token-estimates.json` contains the generated token and context-fit
  planning estimates.
- `reports/RUNTIME_CALIBRATION.md` records the completed pre-freeze run matrix,
  provider configuration, deterministic correctness readout, and length
  recommendation.
- `generate_calibration.py` deterministically regenerates the artifacts. It
  generates data only; it is not application, baseline, or evaluator code.
- `manifest.json` records the calibration boundary, sizes, and oracle hashes.

Every raw event has a stable event ID, chronological sequence, timestamps,
payload, and payload hash. The raw payload is never rewritten by a correction,
duplicate relation, or later state update.

## Churn design

The stream intentionally favors repeated state transitions over independent
static facts. Each storyline is observed repeatedly, with uneven gaps, and
the stream includes corrections, unresolved contradictions, supersession,
cancellations, exact duplicate text, missing secondary fields, and ambiguous
entity references.

| Events | Accepted state updates | Corrections | Contradictions | Ambiguous links | Duplicates | Explicit secondary unknowns | Longest observed gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 48 | 1 | 1 | 1 | 0 | 10 | 6 days |
| 100 | 95 | 2 | 2 | 2 | 1 | 10 | 7 days |
| 200 | 188 | 4 | 5 | 4 | 3 | 10 | 8 days |
| 400 | 374 | 9 | 11 | 8 | 7 | 10 | 10 days |

The 400-event cutoff deliberately ends on an unresolved contradiction for one
storyline. The secondary field for every storyline is unobserved and remains
`unknown` with reason `missing`; absence is never represented as zero or
false. Values for one storyline are tentative in order to exercise
`inferred`, while direct updates are `known`.

## Measurement protocol

The model-run portion used the pinned local Codex CLI configuration below. The
frozen baseline instruction is
[`prompts/runtime/baseline-v1.md`](../../prompts/runtime/baseline-v1.md). The
same prompt, tool policy, temperature, answer format, and fixed query bundle
must be used at all four sizes. No prompt or model setting may be changed in
response to an individual calibration failure.

The provider was Codex CLI `0.150.0-alpha.12.2`, authenticated through the
external CLI login flow, with model `gpt-5.6-luna` and reasoning effort `max`.
The exact combination was accepted by the CLI. No local Claude Code binary was
available. The CLI did not expose a documented context limit; all four full
histories completed without a context-warning or truncation signal.

For each size, run the fixed query bundle after the complete prefix. If budget
allows, also repeat the query at the nested prefix checkpoints. Record:

1. model/provider/version and documented context limit;
2. exact tokenizer-based input and output tokens, replacing the planning
   estimate below;
3. context utilization and whether the full history was accepted without
   truncation or summarization;
4. typed query correctness against the calibration-only oracle;
5. stale-value, missed-correction, conflict-collapse, false-certainty, and
   missed-duplicate errors; and
6. latency, retries, concurrency, and approximate provider cost.

The rough correctness readout should be a small fixed assertion comparison,
not an LLM judge. Report per-size current-state, previous-state, unknown,
and relation accuracy, plus a degradation delta from the 50-event prefix.
The calibration result is evidence for choosing a final event count, not a
benchmark score and not an improvement experiment.

## Current planning estimates

These are generated with `ceil(serialized characters / 4)` plus 160 fixed
system/protocol tokens and a 359-token query-bundle estimate. They are not a
provider tokenizer result.

| Events | Approx. history tokens | Approx. final query input | Fits within 75% of 16k | 32k | 64k | 128k | 200k |
| ---: | ---: | ---: | :---: | :---: | :---: | :---: | :---: |
| 50 | 5,159 | 5,678 | yes | yes | yes | yes | yes |
| 100 | 10,323 | 10,842 | yes | yes | yes | yes | yes |
| 200 | 20,682 | 21,201 | no | yes | yes | yes | yes |
| 400 | 41,395 | 41,914 | no | no | yes | yes | yes |

The actual selected model's context limit replaces this illustrative matrix.
The 75% column is a conservative usable-context planning budget, not a claim
that the remaining 25% is unusable.

## Runtime and cost envelope

One final query-bundle run at each size is four model turns in four fresh
persistent sessions and approximately 79,635 planning input tokens in total. A
three-repeat variance check would be twelve turns and approximately 238,905
planning input tokens, before model output tokens and provider-specific overhead.
The observed 400-event run took about 576 seconds versus about 277 seconds for
200; wall time is not linear because provider reasoning dominates. Local
generation is negligible compared with model calls. The subscription provider
did not expose a per-call dollar price.

Dollar cost remains expressible as the following formula, but the subscription
CLI did not expose provider rates for this run:

```text
cost = input_tokens * provider_input_rate
     + output_tokens * provider_output_rate
     + any fixed request/tool charges
```

The executed first pass used one run at each of the four sizes. Repeat only if
the first pass shows a potentially meaningful size effect and the result needs
variance evidence.

## Length-selection rule for Gate A

Do not choose the longest history merely because it consumes more context.
After the fixed-prompt model sweep:

1. Prefer the smallest length in the approximately 150–200-event range that
   shows a consistent state-quality decline relative to 50/100 events while
   remaining within the selected model's usable context and hackathon budget.
2. If 200 remains stable but 400 shows a meaningful decline while still fitting
   usable context, consider 400 for the primary only after human review and
   only if repeated execution remains practical.
3. If the only decline occurs when the context is truncated or over the
   usable-context budget, treat it as context stress: keep the realistic
   primary in the 150–200 range and place 400 in the secondary stress track.
4. If there is no meaningful degradation through 400, do not keep inflating
   the history to exhaust context. Review whether the churn pattern is
   sufficiently diagnostic before freezing Gate A.

The observed sweep had a non-monotonic state-only curve: 50 and 100 events had
two and zero current/previous-state defects respectively, 200 had one, and 400
had two. The 400-event run also took about 9.6 minutes. This is evidence of
additional degradation at 400 relative to 100, but not a repeatability claim;
only one run per size was made. The provisional Gate A recommendation is 200
events for the realistic primary and 400 events for a secondary stress track.
The optional 800-event condition was not met and was not run.

The 400-event history is the current optional stress candidate. A later
250–500-event stress track may be added only if cost and runtime allow; it
cannot replace a realistic primary benchmark. An approximately 800-event
calibration continuation is a separate, one-time option only after 400 has been
run and meets the documented fit, cost, and degradation conditions; it is not
generated by default. No final benchmark length is approved by this calibration
artifact alone.

## Reproduction

From the repository root, regenerate the calibration artifacts with:

```text
python benchmark/calibration/generate_calibration.py
```

The command is deterministic and idempotent. The official benchmark remains
uncreated, and the calibration oracle must not be copied into development or
holdout benchmark packages.
