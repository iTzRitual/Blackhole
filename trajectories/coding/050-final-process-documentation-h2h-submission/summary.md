# Summary

## Status

Complete after the final documentation/evidence commit. The final H2H is a
descriptive post-freeze comparison; no application or V1 benchmark artifact
was changed.

## Goal

Execute the final Blackhole process-documentation, frozen head-to-head,
video-script, and hackathon-submission package specification without changing
the frozen application or V1 benchmark artifacts.

## Agent/tool used

Codex desktop agent with local shell and repository tools.

## Initial hypothesis

The final H2H hypothesis was that durable Product V2 projection, Attention
lifecycle, provenance, multilingual identity, document state, and permanent
Undo would improve cross-capture coherence over a stateless raw-memory prompt,
while raw memory could remain competitive on simple recall. The benchmark was
preregistered as descriptive evidence, not as a Product V2 optimization.

## Phase 1 work completed

- Verified clean `master`, `origin/master`, and the peeled
  `hackathon-submission-demo-ready` tag at
  `cc0cca8e8d9c3a5ab0955f365ea71c639cac7548`.
- Read the complete private advisory transcript locally and used it only as
  decision context. The raw transcript remains outside the repository.
- Inspected the README, process notes, Product V2 dogfood record, evaluation
  plan, implementation freeze, generalization report, decision log, changelog,
  trajectory index, and coding trajectory summaries.
- Added the sanitized chronological decision history, iteration map, transcript
  note clarification, advisory decision-log clarification, and trajectory 050
  index entry.
- Confirmed with `git diff --check` and path inspection that Phase 1 changes are
  documentation/trajectory files only; no application, benchmark, evaluator,
  baseline, prompt, or script code changed.

## Important implementation decisions

- Kept the complete private advisory transcript outside the repository. The
  repository contains only a sanitized history and evidence map; no transcript
  was fabricated or published.
- Created the H2H package in a separate disposable clone outside the main
  worktree, checked out at the peeled frozen tag
  `cc0cca8e8d9c3a5ab0955f365ea71c639cac7548`.
- Sealed a new contract before execution: four fresh synthetic worlds, 20
  captures per world, checkpoints at 7/14/20, ten assertion families, strict
  response schema, raw-memory prompt, deterministic PTS scorer, and isolated
  Product V2 Homes. Expected assertions were not supplied to either system.
- Ran the exact frozen Product V2 HTTP path and a fresh stateless Codex CLI
  comparator with the same `gpt-5.6-luna` / low configuration. The w03 Undo
  operation used normal `/api/v2/retract`.
- Copied only a sanitized result summary into the main repository; raw cases,
  expected assertions, provider outputs, and full processing records remain in
  the disposable clone.

## Tools and actions used

- Read the complete user-referenced pasted brief and the complete private
  advisory transcript locally; inspected repository process/evaluation/product
  documents and the frozen tag.
- Used local shell/repository tools, `apply_patch`, `git`, the authenticated
  `codex` CLI, the frozen Product V2 Host/PWA transport, deterministic JSON
  hashing, and a local scorer. No credential value was requested, read,
  copied, exported, or persisted.
- Wrote the sanitized process history, iteration map, transcript notes, final
  H2H report, submission copy, video script, result summary, and runtime trace.

## Failures and changed approaches

- The first H2H runner attempt completed the raw-memory leg but stopped before a
  valid Product V2 result because the harness referenced `query_id` instead of
  the sealed `query_ids` list. No semantic output from that attempt was used.
- Corrected only the runner field access, resealed the manifest, and reran from
  fresh Homes. Cases, expected assertions, scoring rules, and prompts were not
  changed.
- A post-run logger-label collision caused Product V2 extraction-call telemetry
  to report zero. The count was deterministically recovered from the recorded
  unique `last_successful_at` processing boundaries; semantic scores and
  responses were unchanged.

## Human feedback or checkpoints

- Scope was constrained by the repository owner/AGENTS.md freeze: no `app/**`,
  frozen tag, V1 evaluator semantics, baseline result, calibration evidence,
  holdout material, or private transcript publication.
- The first phase was committed and pushed before the H2H run. The final H2H
  result was retained even though Product V2 did not lead aggregate PTS; this
  was an evidence checkpoint against tuning the product after observing the
  result.

## Evaluation performed

- Verified frozen tag and commit before sealing and before execution.
- Sealed manifest SHA-256 for the final run:
  `5b38b14aac4e3f4ab88a7cff6a5d5d411f7275c8579e501a3da0ec7128243393`.
- Raw-memory Codex: 13/13 schema-valid fresh queries, PTS `0.8574727047`,
  Attention F1 `0.5641025641`, 13 Codex calls, `130.878 s` wall time.
- Product V2: 80/80 captures processed on first attempt, zero processing
  failures, 13/13 schema-valid queries, PTS `0.7928039934`, Attention F1
  `0.6794871795`, 80 extraction calls plus 13 Ask requests, `1217.334 s` wall
  time.
- Ran deterministic repository validation after documentation changes; final
  exact counts and any understood qualification warnings are recorded in the
  final checklist and handoff.

## Result

The raw-memory comparator recalled more of the small authored assertion set,
but Product V2 had the better active Attention F1 and preserved durable,
inspectable state plus permanent Undo. The result is mixed and descriptive;
it is not LQA-0M, not an official holdout, and not a significance claim.

## Regressions or unresolved issues

- No Product V2, V1 benchmark, evaluator, baseline, calibration, or holdout
  regression was introduced by this documentation/evidence task.
- Product V2's lower aggregate PTS and slower operational path are unresolved
  observations, not bugs authorized for a post-freeze optimization pass.
- The H2H package's initial logger collision is documented and audited; the
  sanitized main-repository summary reports the corrected count basis.

## Final decision

**KEEP** the final H2H as a sanitized descriptive post-freeze evidence layer.
Make no Product V2 or V1 benchmark change based on the score. Preserve the
separation between V1 science, Product V2 acceptance/dogfood, and this fresh
generalization comparison.

## Related git commit

Phase 1 process documentation was committed and pushed as `73e0ad7`. The final
submission/evidence documentation package was committed and pushed as
`191f0390d049e6a8003254800eff2c25dc947152`. The subsequent documentation-only
commit containing this completed trajectory is the closure commit for the
task.
