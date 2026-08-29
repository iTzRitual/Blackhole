# Final product and submission summary

## Status

Complete after final validation and the coherent commit recorded below.

## Goal

Turn the validated Blackhole state-projection core into a minimal,
reproducible, video-ready hackathon submission without reopening frozen
benchmark or baseline decisions.

## Agent/tool used

Codex used the shared local workspace, `apply_patch` for repository edits,
PowerShell/Python for deterministic checks, and the in-app browser control
surface for a rendered local-demo smoke check. No external provider call was
used for the product demo or the final advanced replay.

## Initial hypothesis

A small local web surface backed by the existing immutable SQLite boundary could
make universal capture, longitudinal state, uncertainty, attention, and
approval boundaries inspectable without introducing production infrastructure or
hidden provider behavior.

## Important implementation decisions

- The recorded relation-detail audit did not satisfy the condition for a
  deterministic-only repair. The exact decision was: “Relation detail requires
  richer semantic extraction and is deferred.” Experiment 003 was not run.
- The demo uses a separate committed 14-event synthetic seed and the existing
  `StateStore`/`ResponseProjector` boundaries.
- New captures are appended as immutable raw events with pending semantic status;
  the capture path does not classify input or call a provider.
- The local HTTP server is stdlib-only and exposes state, fixed query families,
  capture, reset, and static UI routes.
- Provider discovery in the demo checks only for a `codex` executable. Login and
  credentials remain outside Blackhole.
- The final comparison uses the existing official `baseline-v1` and a
  deterministic replay of the kept generic Experiment 002 projector.

## Tools/actions used

- Inspected the approved attachment, current instructions, recorded extraction,
  SQLite state, benchmark expectations, and existing evidence.
- Added `app/demo.py`, `app/web_app.py`, static web assets, demo seed/reset
  tooling, and focused demo tests.
- Added four representative local-demo runtime trajectories and one final
  deterministic advanced-replay trajectory.
- Updated README, architecture, evaluation, decision, reproduction, changelog,
  and video documentation.
- Ran the final advanced replay and deterministic scorer without provider calls.

## Failures encountered

- The initial combined documentation patch was rejected because it attempted two
  operations on the same README path in one patch. The edit was split into
  delete/add and append patches; no repository content was lost.
- The relation-detail audit showed missing or differently targeted expected
  relation edges, so the proposed bounded repair could not proceed under the
  authorized rule.

## Retries or changed approaches

The README patch was retried using separate file operations. The relation
experiment was not retried or broadened. Product work proceeded with the
validated projector and a separate deterministic demo seed.

## Human feedback or checkpoints

The human-authorized final-phase instruction froze Gate A at 200 events,
preserved Gate B, `response-contract-v2`, `baseline-v1`, calibration evidence,
and the latest kept advanced result, and authorized only scoped product/demo
work. The implementation followed those boundaries and did not access holdout
material.

## Evaluation performed

- Demo unit and HTTP tests: 4 passed.
- Browser smoke check: page load, Capture, Attention, Memory, Ask, suggested
  change lookup, `Saved.` feedback, and visual layout all verified.
- Final deterministic advanced replay: `LQA-0M=0.7492295898545899`,
  `DSCR=72`, checkpoints 50/100/150/200 as recorded in the final result;
  schema, safety, and source-integrity checks passed.
- The full repository test suite, benchmark generator check, contract smoke,
  compile check, hash audit, and clean-diff audit were run before commit.

## Result

The repository contains a runnable local demo, a deterministic synthetic seed,
judge-facing reproduction instructions, representative runtime evidence, a
final comparison artifact, and a five-minute video script/shot list. The
official baseline remains unchanged at `LQA-0M=0.30149145529538973`; the latest
kept advanced replay remains `0.7492295898545899`.

## Regressions or unresolved issues

- The demo is not production infrastructure and does not provide OCR, a hosted
  account system, live semantic interpretation on capture, or an external-action
  executor.
- Newly captured text remains pending until a separately authorized semantic
  runtime processes it.
- Relation-detail recall remains the clearest measured weakness; richer
  extraction was deliberately deferred.
- The benchmark is one public synthetic scenario and the comparison is not
  holdout evidence. The checkpoint curve is not monotonic.

## Final decision

**KEEP** the scoped local demo and final submission package. Preserve the frozen
benchmark, official baseline, evaluator, response contract, and calibration
evidence unchanged. Do not infer production readiness from the demo.

## Related git commit

This trajectory is included in the final coherent product/submission commit;
the commit SHA is reported in the completion message.
