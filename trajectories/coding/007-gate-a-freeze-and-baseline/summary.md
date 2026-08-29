# Gate A freeze and baseline summary

## Goal

Execute the human-approved Gate A transition: freeze the realistic 200-event
development benchmark, add deterministic evaluator tooling and tests, run the
fair Codex CLI baseline under checkpoint isolation, and stop before advanced
Blackhole application work.

## Agent/tool used

Codex in the shared Windows repository, using PowerShell, Python's standard
library, Git, and the locally installed/authenticated Codex CLI. No provider
credential value was read or stored.

## Initial hypothesis

The 200-event primary with ten interleaved high-churn storylines would provide a
practical longitudinal state-maintenance benchmark, while a 400-event run could
remain an optional secondary stress track. The baseline would use one persistent
canonical ingestion session and isolated checkpoint forks so query answers could
not contaminate later ingestion.

## Important implementation decisions

- Added the deterministic public development generator under
  `benchmark/dev/generate_benchmark.py`.
- Frozen contract `1.0-gate-a-dev` contains 200 events, checkpoints 50/100/150/200,
  12 fixed queries, typed assertions, explicit unknown/contradiction semantics,
  deterministic financial projections, and separate
  `duplicate_event_count`/`duplicate_group_count` fields.
- Used ten 20-event storylines interleaved round-robin. The public case contains
  normalized synthetic captures only; generator operations and storyline labels
  are not exposed in it.
- Added a human review artifact and visible development oracle. No holdout case,
  holdout expected output, or evaluator-owned ground truth was created.
- Added a stdlib-only exact assertion evaluator with LQA-0M, empty-set rules,
  source-hash validation, schema diagnostics, status/category metrics, DSCR, and
  a hard safety gate.
- Added a fair Codex CLI runner using model `gpt-5.6-luna`, reasoning `max`, a
  read-only empty workspace, one canonical session, four chronological capture
  batches, and atomic native `fork <parent> <prompt>` checkpoint queries. Forks
  were never resumed.
- Kept `prompts/runtime/baseline-v1.md` unchanged after the official run. The
  provider response schema is documented and validated by the deterministic
  evaluator; mixed JSON value types made strict provider-side schema enforcement
  incompatible with this contract.

## Tools/actions used

- Read the current repository guidance and the product, architecture, decision,
  evaluation, and reproduction documents before changing their subject areas.
- Generated and checked the public scenario and development expected output.
- Ran Python compilation and evaluator unit tests.
- Verified the local Codex CLI configuration and ran the official baseline using
  the existing subscription authentication.
- Scored the saved baseline candidate into `eval/results/baseline-v0.json`.
- Updated README, benchmark, architecture, evaluation, reproduction, product,
  decision, and improvement-history documentation.

## Failures encountered

1. The first baseline harness attempt sent Windows console-encoded stdin. Codex
   rejected the Unicode input as invalid UTF-8 before checkpoint queries ran.
2. The initial strict response schema was rejected by the provider because its
   schema dialect required explicit types, disallowed `minProperties`, and did
   not permit the mixed arbitrary JSON values needed by the assertion contract.
3. A two-step fork-then-resume diagnostic was unreliable and timed out for a
   substantive query. A minimal fork probe succeeded, and the runner was changed
   to the atomic native fork-with-prompt form.
4. A four-query diagnostic completed in about 235 seconds and returned a
   semantically different assertion vocabulary. This was recorded as a runtime
   diagnostic, not an official score.

## Retries or changed approaches

The runner was retried after the UTF-8 fix. Provider schema enforcement was
removed from the invocation while retaining prompt-constrained JSON and
deterministic validation. The official run was then completed with the atomic
fork protocol and no query-fork timeout.

## Human feedback or checkpoints

The human approved Gate A with the required 200-event primary, 400-event optional
stress track, Codex subscription runtime, duplicate-count definition, and
checkpoint query-isolation rule. The human explicitly prohibited an 800-event
track, advanced application/baseline-system work beyond the fair comparator,
holdout access, and prompt tuning based on individual calibration failures.

## Evaluation performed

- `python benchmark/dev/generate_benchmark.py --check` passed: 200 events and
  four checkpoints were generated deterministically.
- `python -m unittest discover -s eval/tests -v` passed: 7 tests.
- Official baseline completed all four checkpoints with return code 0 and no
  provider/context rejection.
- The canonical capture turns reported input tokens 21,112 / 29,987 / 37,789 /
  43,883 and output tokens 89 / 20 / 19 / 18. Query-fork input tokens were
  24,582 / 30,662 / 38,463 / 44,556 and output tokens were 35,031 / 32,201 /
  37,523 / 34,037 at checkpoints 50/100/150/200.
- Query-fork wall time was approximately 2,513 seconds; canonical capture turns
  were approximately 20 seconds. No dollar cost was inferred because provider
  subscription pricing was not exposed.
- Deterministic baseline result: LQA-0M `0.0000`, checkpoint scores all `0.0000`,
  totals `TP=0`, `FP=266`, `FN=375`, DSCR `336` (`168.0` per 100 events),
  schema validity `false` with six malformed query records, attention false-
  positive rate `1.0`, no safety violation, and no source-integrity failure.

## Result

Gate A development benchmark, evaluator, and fair baseline artifacts are present
and reproducible. The official baseline produced valid JSON containers and all
12 query IDs, but its state-key/assertion vocabulary did not match the frozen
exact contract. The zero score is therefore a recorded baseline observation and
not a claim that the product or benchmark is successful.

## Regressions or unresolved issues

- Baseline runtime is high for repeated hackathon runs.
- The baseline's schema/key mismatch is a Gate B investigation item. Expected
  outputs must not be changed to accommodate it after scoring.
- The Codex CLI did not expose a documented context limit or tokenizer; fit is
  reported empirically only.
- No advanced application, Blackhole memory layer, production infrastructure,
  Claude adapter, or holdout evaluation was implemented.

## Final decision

**KEEP** the approved 200-event benchmark contract, deterministic evaluator, and
checkpoint-isolated baseline evidence. Proceed to the human Gate B review of the
baseline failure and runtime tradeoffs. Do not begin advanced application work in
this task.

## Related git commit

The completed work is recorded in the coherent commit:
`benchmark: freeze Gate A development benchmark and baseline`.

No authentic coding-session transcript was available for export. This summary
records observed actions and results; it is not a reconstructed transcript.
