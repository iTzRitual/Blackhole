# Gate B contract repair summary

## Goal

Repair the invalid Gate A baseline response/evaluator boundary, preserve the
v0 evidence, prove the corrected path with a separate non-scored smoke test,
run one official corrected 200-event baseline, and stop without implementing
the advanced Blackhole application or baseline memory system.

## Agent/tool used

Codex working in the shared repository with PowerShell, `apply_patch`, the
Python standard library, the deterministic evaluator, and the locally
installed authenticated Codex CLI. No provider token was requested, read,
copied, exported, or persisted.

## Initial hypothesis

The v0 zero was primarily an interface failure: grouped model summaries and
private evaluator-oriented `state_key` values were compared as if they were the
same public semantic representation. A public subject/predicate contract with
deterministic canonicalization should make the baseline score interpretable,
while still retaining genuine state, recall, and reasoning errors.

## Important decisions

- Preserved and renamed v0 candidate/score artifacts as
  `baseline-v0-invalid-contract-*`; their exact reason is recorded as
  `response/evaluator contract mismatch`.
- Added diagnostic classification in `docs/GATE_B_CONTRACT_DIAGNOSTIC.md`.
- Froze `benchmark/dev/response-contract-v2.json` and paired
  `query-bundle-v2.json`. Candidate assertions use public subject/predicate;
  candidate `state_key` is rejected. Provenance is required and validated but
  scored secondarily to avoid exact-source-set confounding.
- Kept raw events, expected values, storylines, checkpoints, and the substantive
  `prompts/runtime/baseline-v1.md` prompt unchanged. Only public fields were
  added to generated development expected assertions.
- Added a non-scored parser → canonicalizer → evaluator smoke fixture and tests.
- Replayed a fresh official canonical session because the prior run had no
  provable reusable clean pre-query snapshot. Query children were not reused as
  parents.
- Added a labeled 50-event representative fast slice. It is not an official
  score and was not used to tune the prompt.

## Actions and tools

- Read the human Gate B blocker attachment and the repository guidance.
- Created this trajectory before changing benchmark/evaluator code.
- Inspected v0 raw checkpoint outputs, query bundle, v1 schema, expected
  assertions, canonicalization, and malformed records.
- Added public v2 contract/schema/query instructions and deterministic scorer
  normalization, matching, provenance diagnostics, and validation.
- Updated evaluator unit tests and regenerated the public development artifacts.
- Verified raw hashes and expected assertions against commit `64d4662`.
- Ran the independent smoke test and the development test suite.
- Ran the non-official fast slice and one official corrected baseline.
- Saved the official score under `eval/results/baseline-v1.json` and the raw
  runtime under `trajectories/runtime/003-baseline-v1/`.

## Failures, retries, and changed approaches

- A first fast invocation completed provider work but failed in runner metadata
  because a relative custom trajectory path was passed to `relative_to`.
  Absolute path normalization fixed the harness; the failed attempt remains in
  `trajectories/runtime/fast-dev-050/`.
- A subsequent fast response left an incomplete `-o` output file. The runner
  now falls back to a parseable `agent_message`; that attempt remains in
  `trajectories/runtime/fast-dev-050-rerun/`.
- The final fast retry parsed all four query responses successfully. The query
  prompt also received the exact public scenario ID, fixing a transport-level
  echo omission before the official run.
- No official model retry or prompt tuning occurred after the corrected
  contract was used.

## Human checkpoint

The human instruction explicitly blocked Gate B until the baseline contract was
repaired, required preservation of v0, required a smoke test and one corrected
official run, and prohibited advanced application implementation. This task
stopped at the requested `GRILL ME — GATE B VALID` boundary.

## Evaluation performed

- `python benchmark/dev/generate_benchmark.py --check`: passed for 200 events and
  four checkpoints.
- `python -m unittest discover -s eval/tests -p 'test_*.py'`: 9 tests passed.
- `python eval/contract_smoke.py`: passed; correct synthetic response scored
  1.0 with 6/0/0 TP/FP/FN, malformed unknown-with-value was diagnosed.
- Fast slice: 50 events, four selected queries, v2 parse success, diagnostic
  only.
- Official baseline: all 4 checkpoints, all 12 query IDs, schema-valid, source
  integrity valid, safety pass.

## Result

The official deterministic result is `LQA-0M=0.3014914553` with checkpoint
means `0.2894 / 0.2669 / 0.3127 / 0.3369`, totals `TP=146, FP=239, FN=229`,
and `DSCR=277` (`138.5` per 100 events). Category detail, runtime, tokens,
semantic examples, and the one proposed next experiment are in
`docs/GATE_B_VALID_REPORT.md`.

## Regressions or unresolved issues

The valid v2 run still has low relation-reconciliation and entity-resolution
accuracy, substantial current/temporal/task errors, and an attention false-
positive diagnostic of 1.0. Its checkpoint means rise rather than degrade
monotonically, so it does not prove a history-length degradation curve. The
provider emitted recurring non-fatal local hook warnings; no provider or
context rejection occurred. Dollar cost was unavailable from the subscription
runtime. No application, holdout case, holdout expected output, or advanced
baseline implementation was added.

## Final decision

**KEEP** the v2 public contract, deterministic evaluator, isolation protocol,
and corrected baseline evidence. **REVISE/REMOVE** the v0 result only as an
official measure; preserve it unchanged as invalid historical evidence. The
single next advanced experiment is proposed in the Gate B report but was not
implemented.

No authentic session transcript was available. This summary records observed
actions and outcomes and does not fabricate one.

## Related git commit

`0299a2c benchmark: repair baseline response contract`
