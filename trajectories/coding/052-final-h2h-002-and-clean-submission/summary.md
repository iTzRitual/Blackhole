# Task summary

Status: complete.

## Goal

Run the authorized final H2H-002 comparison, record its authoritative result,
move submission-only human materials outside the repository, perform a
high-confidence cleanup, and produce a verified tracked-HEAD submission ZIP
without changing frozen Product V2 behavior or protected benchmark material.

## Agent/tool used

Codex desktop agent with shell inspection, `apply_patch`, Python validation,
Git, and the installed subscription-first Codex CLI used by the sealed
benchmark runner.

## Initial hypothesis

A native AI conversation would remain useful for simple recall, while the
stateful Product V2 path would provide a stronger active Attention projection,
query-free availability, durable source-linked state, and explicit Undo.
The hypothesis was recorded before the final comparison and did not assume a
semantic-score win.

## Important implementation decisions

- H2H-002 was isolated outside the source repository and sealed over three
  fresh synthetic worlds, 60 captures, checkpoints at 7/14/20, and 52 atomic
  assertions per system.
- Systems were fixed as native single-thread chat, augmented raw memory, and
  the frozen Product V2 normal HTTP path. The model was `gpt-5.6-luna` with low
  reasoning; no prompt, case, expected assertion, scoring, or Product V2 code
  changed after seal.
- Two pure runner defects were corrected before the final valid run: a missing
  System B harness function, then a logger field collision and incorrect
  checkpoint telemetry grouping. The cases, prompts, scoring rules, and
  expected assertions were rehashed and remained unchanged.
- The final cleanup removed only clearly submission-only tracked documents and
  ignored Python caches. Trajectories, tests, evaluation artifacts, app code,
  benchmark boundaries, and historical evidence were kept.

## Tools/actions used

- Inspected the frozen Product V2 tag, clean starting worktree, existing H2H-001
  evidence, repository layout, and the provided task instructions.
- Created the sealed H2H-002 specification, system protocols, schema, cases,
  expected assertions, manifest, runner, and final external result.
- Ran the final valid H2H-002 execution once after the runner corrections and
  did not rerun it afterward.
- Added the compact H2H-002 report, changelog entry, trajectory entry, and
  current README/reproduction references.
- Created external `VIDEO_SCRIPT.md`, `SUBMISSION_COPY.md`, and
  `RECORDING_CHECKLIST.md`; removed the redundant tracked submission and video
  documents; checked for dead references.
- Removed confirmed ignored `__pycache__` directories. No local Home, database,
  provider credential, private transcript, holdout output, or raw private
  dogfood data was added to the repository.

## Failures encountered

- The first H2H-002 execution stopped before result writing because the runner
  referenced a missing System B function. No benchmark result was used.
- The next consistent execution exposed a logger event-name collision and
  incorrectly positioned context telemetry. Its result was discarded. These
  were harness-only defects; processing state and semantic inputs were not
  changed.
- The final valid execution completed successfully with no provider or schema
  failures. The sealed scorer reports zero recognized truthful abstentions and
  forget leakage through its fixed token proxies; these limitations are
  disclosed rather than altered after the run.

## Retries or changed approaches

The runner was patched only to restore the preregistered execution and telemetry
contract, then the manifest was resealed. No case, expected output, prompt,
model, configuration, or scoring retry was introduced after the final seal.
Repository cleanup was intentionally narrowed under deadline mode; uncertain
historical trajectories and tests were retained.

## Human feedback or checkpoints

The task was authorized through the two pasted instruction files. The final
deadline instruction explicitly prohibited any further benchmark, live
provider, full-suite, optional-telemetry, or product work and selected the
Attention result for the recording because the resolved-task threshold was not
met.

## Evaluation performed

Authoritative final H2H-002 run:

- native single thread: resolved assertion rate `0.5962`, semantic macro F1
  `0.7712`, Attention F1 `0.2222`;
- augmented raw memory: resolved assertion rate `0.6731`, semantic macro F1
  `0.7857`, Attention F1 `1.0000`; and
- Blackhole Product V2: resolved assertion rate `0.6154`, semantic macro F1
  `0.7257`, Attention F1 `0.9407`.

All 60 Product V2 captures completed with zero extraction errors; the native
and augmented legs each had 18 schema-valid query attempts, and Product V2 had
9 schema-valid Ask calls. The manifest SHA-256 is
`91cfe29865cdecec62d1759b29a8845e40ee8c54bf378d148f3e5f008f1064fd`.

Cleanup validation was limited as instructed to `git diff --check` and
`python3 -m compileall -q app`; archive verification additionally checked the
tracked file list, excluded external materials and ignored caches, extracted
the ZIP into a fresh directory, and ran the offline archive sanity commands.

## Result

H2H-002 is preserved as descriptive post-freeze evidence. The semantic result
is mixed, while Product V2 materially leads native single-thread chat on active
Attention F1 and supplies Attention without a query. The final source tree has
no tracked submission-only video/form documents, and the human materials remain
outside Git.

## Regressions or unresolved issues

No Product V2 or frozen scientific regression was introduced. H2H-002 remains
limited to three small synthetic worlds; its claim and forget metrics are
deterministic proxies, and exact Product V2 provider-context bytes were not
exposed by the normal HTTP contract. No binary attachment stress was included.

## Final decision

**KEEP** the sealed H2H-002 comparison and the final cleanup. Do not tune the
product, baseline, benchmark, evaluator, or scoring contract from this result.

## Related git commit

The final cleanup commit is recorded after the archive is built and pushed.
