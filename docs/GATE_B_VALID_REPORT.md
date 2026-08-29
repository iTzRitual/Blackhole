# Gate B valid report

Status: `VALID`. This report closes the response/evaluator contract repair. It
does not approve or implement the advanced Blackhole application.

## Why baseline-v0 was invalid

The preserved v0 run is marked with
`reason_invalid: response/evaluator contract mismatch`. It had `TP=0`, schema
violations, grouped summaries, and evaluator-oriented dotted `state_key` values
that were not part of a public derivable grammar. Its `LQA-0M=0.0000` therefore
does not mean semantic zero. The raw candidate, score, and runtime responses
remain preserved as historical evidence under the `baseline-v0-invalid-contract`
names.

## Contract repair

The frozen `response-contract-v2` boundary makes candidate assertions public and
atomic:

- `subject`, `predicate`, `knowledge_status`, and `source_refs` are required;
  the public ontology and dynamic `capture:<event_id>` grammar are supplied to
  both sides.
- `known` and `inferred` assertions include `value`; `unknown` assertions omit
  `value` and include `unknown_reason`.
- Candidate `state_key` is forbidden. Development expected assertions may retain
  it only for DSCR clustering and debugging.
- Decimal/date/field aliases, enum aliases, and unknown-reason categories are
  canonicalized deterministically. There is no LLM judge.
- Primary one-to-one matching uses public subject, predicate, status, and value
  or canonical unknown reason. Required, valid `source_refs` and optional
  confirmation references are measured as secondary provenance, so additional
  valid evidence does not hide semantic accuracy.
- `duplicate_event_count` counts duplicate captured events excluding each
  original; one original plus two duplicates is exactly two. It is separate from
  `duplicate_group_count`.

The substantive `prompts/runtime/baseline-v1.md` file was not changed. Only the
versioned runner/schema instruction changed.

## Ground-truth and boundary audit

The raw event hashes and event count match the pre-repair commit `64d4662`. The
generated expected assertions match the pre-repair expected assertions after
removing only the newly added public `subject` and `predicate` fields. No story
fact, value, lifecycle transition, correction, duplicate, cutoff, or expected
ground-truth value was changed.

The baseline runner receives only the public scenario, frozen life-admin prompt,
v2 runner instruction, v2 query bundle, and v2 public contract. It receives no
generator, expected output, evaluator, database, calibration oracle, or holdout
material. The holdout directories remain placeholders.

The old run did not provide provable clean per-checkpoint canonical snapshots:
the saved metadata had IDs, but not sufficient evidence that a reusable session
contained only captures and no query, answer, feedback, or ground-truth state.
The corrected official run therefore replayed a fresh canonical session. A query
child was never used as a parent.

## Independent contract smoke test

[`eval/results/contract-smoke.json`](../eval/results/contract-smoke.json) is
non-scored and separate from the 200-event case. A tiny synthetic history passed
through raw model text parsing, public canonicalization, and deterministic
evaluation:

- fenced JSON parsed successfully;
- six semantic assertions scored `TP=6, FP=0, FN=0`, score `1.0`;
- decimal/alias/lifecycle/duplicate/current-v-old/unknown cases were covered;
- an `unknown` assertion carrying a value was rejected with a clear schema
  diagnostic.

## Official corrected baseline

Exactly one official corrected model run is recorded in
[`eval/results/baseline-v1-candidate.json`](../eval/results/baseline-v1-candidate.json),
scored in [`eval/results/baseline-v1.json`](../eval/results/baseline-v1.json),
with raw checkpoint responses in
[`trajectories/runtime/003-baseline-v1/`](../trajectories/runtime/003-baseline-v1/).
It used Codex CLI `0.150.0-alpha.12.2`, `gpt-5.6-luna`, reasoning `max`, one
fresh isolated canonical session, and four atomic discarded query forks. The
candidate contains all 12 query IDs at every checkpoint and is `response-contract-v2`
schema-valid.

| Checkpoint | Mean query score | TP | FP | FN | Micro semantic score |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 0.2894 | 29 | 70 | 39 | 0.2101 |
| 100 | 0.2669 | 31 | 58 | 55 | 0.2153 |
| 150 | 0.3127 | 40 | 54 | 65 | 0.2516 |
| 200 | 0.3369 | 46 | 57 | 70 | 0.2659 |

Primary result: `LQA-0M=0.3014914553`, totals `TP=146, FP=239, FN=229`.
`DSCR=277`, or `138.5` per 100 events. Schema validity is true with zero
schema errors; source integrity is true; safety passes with zero violations;
the run is not a hard failure. The attention false-positive diagnostic is
`1.0` because all candidate attention assertions failed the primary semantic
pairing at these checkpoints.

Secondary category scores were: contradiction `0.7500`, current state
`0.1507`, duplicate/change `0.8462`, entity resolution `0.0000`, financial
`0.6842`, obligation/deadline `0.4179`, relation reconciliation `0.0000`,
safety `0.4667`, and temporal history `0.2989`. Known-status score was
`0.2689`, inferred-status score `0.0000` for one expected assertion, and
unknown-status score `0.0729`.

Provider-reported runtime was approximately `2,490.516` seconds total:
canonical capture turns `16.781` seconds and query forks
`753.250 / 587.500 / 546.860 / 586.125` seconds at checkpoints
`50 / 100 / 150 / 200`. Total reported usage was `280,425` input tokens and
`205,068` output tokens, including canonical turns. Query-fork usage was:

| Checkpoint | Input tokens | Output tokens |
| ---: | ---: | ---: |
| 50 | 28,311 | 62,512 |
| 100 | 34,391 | 48,661 |
| 150 | 40,487 | 45,265 |
| 200 | 46,579 | 48,544 |

The subscription runtime did not expose a dollar price, so no dollar cost is
invented.

## Fast development slice

The separate `baseline-fast-dev-retry2` artifact uses a 50-event prefix and the
representative subset `q-subscriptions-current`, `q-tasks-state`,
`q-duplicates-changes`, and `q-unresolved`. It is labeled `DEV FAST / NOT
OFFICIAL SCORE`, parsed all four query responses, and took about `398.234`
seconds including canonical capture. Its query call reported `28,058` input and
`32,597` output tokens. It is diagnostic only and cannot replace the official
four-checkpoint score. Earlier fast attempts exposed and preserved a relative
path metadata bug and an incomplete output-file recovery case; the final runner
uses absolute path normalization and an agent-message fallback.

## What the valid run does and does not show

The v2 result is a usable measurement rather than an interface artifact. It
shows no remaining schema-boundary failure: the candidate is structurally valid,
publicly addressed, and nonzero-scored. Representative semantic failures
include directional source/target reversals in duplicate/change relations,
collapsing many ambiguous Jordan mentions into one broad entity assertion,
retaining historical task owners/statuses alongside current state, and
over-reporting attention items or adding different attention object fields.
Some omissions and formatting differences remain ordinary recall/value
normalization failures, such as missing current slots and `monthly` versus
`month` in a billing-period value; these are not evaluator-ID failures.

The checkpoint means rise from `0.2894` to `0.3369` in this single run, so this
run does not establish monotonic state-quality degradation with history length.
It does establish low absolute accuracy in relation/entity/current-state areas
and persistent state-churn errors. No longitudinal degradation claim should be
generalized beyond this one scenario and run.

## One smallest advanced experiment (proposal only)

The smallest justified next experiment is **Experiment 001: an append-only,
rebuildable lifecycle reconciliation projection for one subscription entity**.
It would preserve raw events, deterministically supersede current versus
historical subscription slots, retain change provenance, and expose the same
query bundle. The valid baseline justifies this narrow experiment through the
low current-state (`0.1507`) and temporal-history (`0.2989`) scores without
implementing the full application, broad entity graph, or external actions.
This experiment is proposed only; no advanced implementation occurred in Gate B.

## Final decision

The response contract is valid for continued benchmark work. Keep v2, the
deterministic evaluator, the isolation protocol, and the corrected baseline
evidence. Keep v0 only as invalid historical evidence. Do not report v0's zero
as an official result, do not change ground truth, and do not begin advanced
application implementation in this phase.

**GRILL ME — GATE B VALID**
