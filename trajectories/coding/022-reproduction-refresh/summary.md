# Judge-facing reproduction refresh summary

## Goal

Refresh judge-facing reproduction documentation so it describes the current
integrated Blackhole Host + PWA rather than the superseded seeded-demo
transport. Keep the task documentation-only and preserve the frozen runtime,
benchmark, evaluator, baseline, calibration evidence, metrics, and
generalization boundary.

## Agent/tool used

Codex in the Codex desktop app using PowerShell, Git worktrees, `apply_patch`,
the repository's Python CLI checks, and the deterministic unit-test suite. No
authentic session transcript was available for export; none was fabricated.

## Initial hypothesis

The current README and the old local-demo section of the reproduction and
architecture docs still presented the seeded demo as the normal product path.
The current `app/host.py`, `app/runtime_config.py`, `app/codex_discovery.py`,
`app/ingestion_engine.py`, `app/query_service.py`, `app/web_app.py`,
`app/web/`, and `scripts/host_smoke.py` should be the authority for the
judge-facing instructions. The documentation can be corrected without
changing runtime or benchmark behavior.

## Important implementation decisions

- Work only in `../Blackhole-reproduction-refresh` on
  `submission/reproduction-refresh`, based on
  `8d3b4ff7a1979540f2e65dd9b493f0731e006f72`; the primary worktree and the
  independent generalization worktree were not switched or modified.
- Make the current quickstart `app.host init`, `app.host doctor`, and
  `app.web_app --host 127.0.0.1 --port 8080`, with `BLACKHOLE_HOME`/SQLite and
  deferred semantic processing explained.
- State that Codex authentication is external, no `OPENAI_API_KEY` is needed,
  capture remains provider-free, and pending Ask freshness requires an
  authenticated Codex CLI.
- Document the explicit trusted-LAN phone path as private-network-only,
  unauthenticated, unpaired, non-TLS, and not Internet-safe.
- Keep `app/demo.py` and `scripts/seed_demo.py` as a clearly labeled
  historical deterministic demo utility. Explicitly remove the implication
  that current Host startup auto-seeds it or exposes `POST /api/reset`.
- Mark `final-comparison-v1.json` as historical/superseded and do not add a
  generalization score or call E005 holdout evidence.
- Leave `docs/VIDEO_SCRIPT.md` and `docs/VIDEO_SHOT_LIST.md` unchanged because
  the final measured post-freeze story is not yet known.

## Tools/actions used

- Read the supplied task file before continuing.
- Inspected the current repository, worktrees, code, docs, and Git tag state.
- Created the requested worktree and branch from the remote master handoff.
- Updated `README.md`, `docs/REPRODUCTION.md`,
  `docs/SUBMISSION_CHECKLIST.md`, and the stale current-facing section of
  `docs/ARCHITECTURE.md`.
- Created this trajectory's `prompt.md` and `summary.md` and updated the
  judge-facing `TRAJECTORY_INDEX.md` inventory.
- Verified the existing local freeze tag and pushed only that existing tag
  after confirming its target.

## Failures encountered

- A first combined tag-inspection shell invocation emitted an ambiguous
  argument error and did not provide a usable remote result. The tag checks
  were rerun as individual quoted commands.
- A first broad reproduction-document patch failed its context check and made
  no file changes. The same work was applied in smaller verified patches.
- The first recursive temporary-directory cleanup command was rejected by the
  shell safety wrapper. The exact temporary validation home created by this
  task was then removed with an explicit .NET directory-delete call.

## Retries or changed approaches

The reproduction refresh was split into independently matching sections after
the failed broad patch. Validation was also split into safe help/setup checks,
deterministic tests, and read-only scope/tag checks so no real smoke or model
inference was consumed.

## Human feedback or checkpoints

The pasted task instruction authorized this documentation-only refresh and
required the isolated worktree, freeze-tag handling, trajectory, validation,
and stop conditions. No additional human feedback was provided. The
generalization worktree was not inspected or used.

## Evaluation performed

The following checks passed without semantic provider inference:

- `python -m app.host --help`;
- `python -m app.web_app --help`;
- `python scripts/seed_demo.py --help`;
- `python -m scripts.host_smoke --help`;
- temporary-`BLACKHOLE_HOME` `python -m app.host init`, `doctor`, and
  `process` (`0` processed; state fresh); `init` used only safe Codex
  discovery/status checks;
- `python -m unittest discover -s . -p "test_*.py" -v`: 85 tests passed;
- `python -m compileall -q app eval scripts`;
- `python benchmark/dev/generate_benchmark.py --check`: 200 events and four
  checkpoints checked; and
- `git diff --check`.

The real `scripts/host_smoke.py` was not run because this task did not require
a model-inference call. No benchmark replay, score, baseline run, evaluation
artifact, or runtime trajectory was created or changed.

## Result

The current README and reproduction instructions now distinguish the
historical seeded demo, the integrated Host/PWA, frozen benchmark reproduction,
and real Codex smoke. The current quickstart and CLI options are grounded in
the implemented code, and the checklist records only the reproduction facts
resolved here.

The freeze tag status is now complete: local
`implementation-freeze-v1^{commit}` and the remote peeled tag both point to
`8d3b4ff7a1979540f2e65dd9b493f0731e006f72`. The tag was missing remotely at
first and was pushed once with `git push origin implementation-freeze-v1`.

## Regressions or unresolved issues

No runtime, benchmark, evaluator, baseline, metric, or generalization
regression was introduced. The video script and shot list remain stale by
design. Post-freeze generalization and an authoritative final comparison remain
open and were not marked complete. Full provider-backed benchmark reproduction
and the real Codex smoke remain outside this documentation-only validation.

## Final decision

KEEP the documentation refresh. This is submission preparation, not a new
benchmark optimization experiment; no KEEP/REVISE/REMOVE metric decision was
created.

## Related git commits

- `abb8f803a86aad23ac5579109f8700352ebeeb7b` — `docs: refresh Host
  reproduction instructions` (the documentation and trajectory prompt).
- The final trajectory/index evidence commit is the follow-up commit on this
  branch; its SHA is reported in the task handoff.
