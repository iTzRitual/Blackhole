# Product V2 dogfood acceptance — trajectory summary

## Goal

Create an independent, black-box Product V2 dogfood and acceptance system in
the dedicated `product/v2-dogfood` worktree without changing the frozen product
implementation or V1 benchmark artifacts.

## Agent/tool used

Codex in the local repository worktree. Tools used and their outputs will be
recorded as observed below.

## Initial hypothesis

Not a benchmark experiment. The acceptance boundary should expose whether
ordinary captures become reliable, evidence-backed, user-visible memory and
attention outcomes, including uncertainty and recovery behavior, without
depending on internal schema details or live providers.

## Important implementation decisions

- Keep the suite visible and explicitly labeled as Product V2 dogfood / product
  acceptance, never as an unseen benchmark or V1 LQA result.
- Use five JSON case collections with 50 natural-language cases. The case
  contract contains timezone-aware timestamps, capture sequences, optional
  attachment fixtures, time advances, Ask/Attention/Memory checks, retry and
  restart steps, Undo, and evidence/uncertainty expectations.
- Use `case.schema.json` as the public shape and a dependency-free Python
  validator for semantic checks that include duplicate IDs, IANA timezones,
  explicit timestamp offsets, safe fixture resolution, capture references, and
  required step fields.
- Keep the harness black-box. `HttpHostAdapter` speaks JSON over the logical
  Host routes without importing `app`; missing routes become `NOT TESTED` and
  reachable failing routes remain failures.
- Keep the deterministic `MockHostAdapter` intentionally non-semantic. It
  proves capture receipts, attachment fingerprints, duplicate submission,
  provider-failure/retry, repeated processing, and restart preservation, but it
  does not impersonate product understanding.
- Add separate product-quality gates and a plain-language human protocol rather
  than one aggregate score. Record the acceptance boundary in D-036.

## Tools/actions used

- Read the pasted task brief and repository guidance.
- Created the dedicated worktree from the required base SHA.
- Created this trajectory before implementation.
- Added the corpus, schema, fixtures, adapters, runner, tests, CI checks,
  dogfood protocol, documentation, decision record, and generated mock result.
- Ran Git scope checks and the offline qualification audit.

## Failures encountered

The first targeted test run rejected the valid `en-US` and `pl-PL` locale
values because the initial regex expected a three-letter region. The schema and
validator were corrected to accept the standard two-letter country form, and
the targeted suite passed on the next run.

## Retries or changed approaches

- Coverage was reviewed after the first report and changed from tag-only counts
  to counts derived from actual case step types; this makes capture, Ask,
  Attention, attachment, and reliability coverage reflect executable cases.
- The first mock report was regenerated after the coverage and corpus updates.

## Human feedback or checkpoints

No additional human feedback beyond the initiating task brief.

## Evaluation performed

- `python -m unittest product_acceptance.harness.test_harness -v`: 7 tests,
  all passed.
- `python -m unittest discover -s . -p "test_*.py" -v`: 92 tests, all passed.
- `python -m compileall -q app eval scripts product_acceptance`: passed.
- `python scripts/qualification_check.py`: passed with four pre-existing
  repository warnings; no credential warning was introduced.
- `python -m product_acceptance.harness.run --adapter mock
  --report eval/results/product-v2-dogfood-mock.json`: exit 0; 50 cases, 2
  `PASS`, 48 expected `PARTIAL`, 0 `FAIL`; all seven mock quality gates
  `PASS`; `live_provider_used=false`.
- Reported coverage: capture 50, memory 30, Attention 19, Ask 46, Undo 1,
  attachments 6, reliability 9, open-world 11, and false-positive Attention
  4.

## Result

The independent acceptance foundation is complete. It can validate the visible
corpus and safely exercise transport/reliability behavior now, and it has a
single HTTP adapter seam for a future integrated Product V2 Host.

## Regressions or unresolved issues

- The deterministic mock does not test semantic Ask, Attention, or Memory
  behavior; those steps are intentionally `NOT TESTED`, making the relevant
  cases `PARTIAL`.
- The required base exposes only a subset of the logical V2 routes. The HTTP
  adapter cannot reset or restart a target, so real integration runs need
  explicit external isolation.
- No human dogfood session or integrated Product V2 Host run was performed in
  this task.
- No benchmark, V1 oracle, live provider, or evaluator-owned holdout material
  was used.

## Final decision

KEEP as the independent Product V2 dogfood / acceptance foundation. Do not use
the visible case corpus as unseen generalization evidence or as a prompt-tuning
oracle.

## Related git commit

- `90cb5ff` — `acceptance: add Product V2 dogfood gate`
- The trajectory index update is the final documentation follow-up on this
  branch.
