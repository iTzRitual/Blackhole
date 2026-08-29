# Submission hardening gate

## Status

Complete for the isolated submission-hardening workstream. This is a
qualification/documentation task, not a benchmark experiment. The active Host
and PWA integration worktree was not changed or indexed as complete.

## Goal

Improve reproducibility and qualification-gate readiness with an offline CI
workflow, a deterministic repository audit, discoverable trajectory evidence,
and a final-hours submission checklist. Preserve runtime semantics, the frozen
benchmark and evaluator, historical artifacts, and the existing narrative
files until integration/generalization freeze.

## Agent/tool used

Codex working in the new sibling worktree
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-submission` using
PowerShell, `rg`, `apply_patch`, Python's standard library, and Git. No
provider, Codex CLI, network model call, home-directory inspection, or
credential-store inspection was used.

## Initial hypothesis

A small stdlib-only gate can make the repository easier to qualify from a
clean machine without coupling CI to provider authentication or changing any
Blackhole runtime behavior. A deterministic trajectory inventory and explicit
stale-artifact/path/credential findings should expose submission blockers
without rewriting historical evidence.

## Important implementation decisions

- Created `submission/hardening` from backend foundation SHA
  `11d8a041fedc027ca705e8616085c05ef18d9b57`; all edits stayed in the sibling
  worktree.
- Added one Python 3.11 GitHub Actions job because the repository declares no
  minimum version and the source uses Python 3.10+ union annotations and
  built-in generic types. The job runs only unit tests, compileall, benchmark
  determinism, contract smoke, and the qualification gate.
- Made missing required artifacts and missing `prompt.md`/`summary.md` in
  coding trajectories hard failures. Raw transcripts are never required;
  coding and runtime traces record their availability separately.
- Limited credential scanning to Git-tracked repository files and reported
  only relative path plus rule name. Documentation placeholders such as
  `OPENAI_API_KEY=<your-key>` are ignored.
- Kept stale named result artifacts and protected narrative files untouched;
  the checklist records the finalization work required after integration and
  generalization freeze.

## Tools/actions used

- Read the pasted task instructions before continuing.
- Inspected the primary, UI, and integration worktrees and verified the
  requested base commit and sibling path were available.
- Audited repository commands, result metadata, trajectory directories,
  submission-facing Markdown paths, and metric references.
- Added the qualification checker, focused temporary-fixture tests, CI
  workflow, trajectory index, checklist, and this trajectory summary.
- Did not modify `app/web/**`, active runtime modules, protected benchmark or
  evaluator material, `README.md`, `IMPROVEMENT_CHANGELOG.md`,
  `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, or `docs/REPRODUCTION.md`.

## Failures encountered

- The first qualification run failed as expected while this trajectory's
  `summary.md` was not yet present. It also exposed the intended five
  non-blocking warnings: three stale named result artifacts and two stale
  final/current narrative references.
- No implementation or validation failure remained after the summary was
  added.

## Retries or changed approaches

The initial metadata inspection used a PowerShell projection with both `DSCR`
and `dscr` property names, which collide case-insensitively. It was replaced
with a narrow Python JSON read for the exact result fields. No repository data
was changed by the failed inspection.

## Human feedback or checkpoints

The supplied task explicitly required a new sibling worktree, no merge, no
runtime/benchmark changes, and no final-comparison regeneration. Those
constraints were followed. Integration and post-freeze generalization remain
outside this workstream.

## Evaluation performed

- Focused qualification tests: 5 passed.
- The qualification gate passed after this summary was added, with five
  warnings and no hard failures.
- `python -m unittest discover -s . -p "test_*.py" -v`: 75 tests passed.
- `python -m compileall -q app eval scripts`: passed.
- `python benchmark/dev/generate_benchmark.py --check`: passed for 200 events
  and four checkpoints.
- `python eval/contract_smoke.py`: passed with semantic smoke score `1.0` and
  malformed output rejected.
- `git diff --check`, protected-file checks, and final worktree status were
  run for the handoff.
- No provider inference, official long-chat baseline, post-freeze
  generalization, or final-comparison regeneration was run.

## Result

The repository now has a fast offline qualification command,
`python scripts/qualification_check.py`, and CI coverage for the canonical
deterministic checks. The trajectory index records 19 coding and 40 runtime
trajectory directories at this checkout. The current kept E005 evidence is
recognized as `LQA-0M=0.8695006212` / `DSCR=40`; older files named
`final-advanced*` and `final-comparison-v1.json` remain visible as warnings
rather than being overwritten.

## Regressions or unresolved issues

- The named final/comparison artifacts and `docs/EVALUATION.md` section 24
  still describe the older E002 `.7492295899` / `DSCR=72` replay. The final
  comparison must be regenerated only after the integrated implementation and
  post-freeze generalization are frozen.
- `docs/REPRODUCTION.md` section 14 still points at the older
  `final-comparison-v1.json` snapshot; it is intentionally not edited here.
- The README has the current E005 metrics, but an explicit “main failure mode”
  and “hot take” are not separately labeled; final narrative work remains.
- No provider credentials are required for this gate. Credential hygiene is
  conservative and intentionally reports only obvious patterns.

## Final decision

**KEEP** the qualification gate, CI workflow, trajectory index, and
submission checklist. Defer narrative/artifact finalization to the
integration/generalization phase; do not merge this branch in this task.

## Related git commit

The coherent commit is recorded in the final handoff and in this section once
the isolated worktree is committed.
