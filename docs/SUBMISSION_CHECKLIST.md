# Submission checklist

This is an operational checklist for the final hours before submission. The
approved Host/PWA integration and submission hardening are now consolidated on
`master`; implementation freeze is being recorded. Post-freeze
generalization, presentation, and external submission remain open. Checked
items are facts verified in this checkout; unchecked items remain open.

## Repository

- [x] Isolated `submission/hardening` worktree created from backend foundation
  SHA `11d8a041fedc027ca705e8616085c05ef18d9b57`.
- [x] Qualification command is available: `python
  scripts/qualification_check.py`.
- [x] Protected benchmark, evaluator, expected-output, runtime, and narrative
  files were not modified by this hardening workstream.
- [x] The hardening branch's `eval/results/contract-smoke.json` has no
  committed diff from the pre-merge master version; the existing artifact was
  preserved rather than regenerated or overwritten as part of consolidation.
- [x] Record the final integrated implementation SHA:
  `171a6cc1c656d6ab901f41bda8440ee5d59967e3`.
- [x] Confirm the final integrated worktree has no unintended changes before
  the documentation-only freeze record.
- [ ] Create the final Git tag.
- [ ] Add an explicit README “main failure mode” statement.
- [ ] Add an explicit README “hot take” statement.

## Benchmark and evaluation

- [x] Preserve the frozen public 200-event development scenario and checkpoints
  at 50, 100, 150, and 200.
- [x] Preserve the official valid `baseline-v1` evidence (`LQA-0M` about
  `0.3014914553`, `DSCR=277`).
- [x] Preserve the current kept E005 evidence (`LQA-0M=0.8695006212469447`,
  `DSCR=40`).
- [x] Do not run benchmark optimization in this hardening workstream.
- [x] Verify that current DEV score claims in the submission-facing narrative
  point to the latest kept E005 evidence; older E002 passages are explicitly
  historical/superseded.
- [ ] Regenerate the final comparison artifact after implementation and
  post-freeze generalization are frozen.
- [ ] Ensure the future final comparison points to E005 or the explicitly
  approved post-freeze result, not the older E002 snapshot.
- [ ] Record the post-freeze generalization result, if authorized and run.
- [ ] Confirm no benchmark optimization occurred after the final freeze.

## Reproducibility

- [x] Keep `docs/REPRODUCTION.md` as the reproduction handoff and review it
  after integration edits land.
- [x] Keep provider requirements explicit: subscription-first local Codex CLI,
  external authentication, and no Blackhole token access.
- [x] Keep approximate runtime/token caveats documented where they are known;
  do not invent subscription dollar cost.
- [x] Define CI coverage for offline qualification, unit tests, compileall,
  benchmark generator determinism, and response-contract smoke; local
  equivalents pass.
- [ ] Test the complete reproduction commands from a clean environment after
  the integrated implementation SHA is frozen.
- [x] Verify all reproduction commands use repository-relative or user-supplied
  paths rather than developer-specific absolute paths.

## Agent trajectories

- [x] Keep `TRAJECTORY_INDEX.md` current with coding and runtime inventory.
- [x] Keep representative baseline, demo, and advanced runtime evidence
  discoverable.
- [x] Keep authentic prompt/summary records for meaningful coding trajectories;
  do not fabricate full transcripts.
- [x] Preserve failed/invalid attempts and their lessons, including the v0
  contract failure and superseded E002 final artifacts.
- [x] Add/finish the integration trajectory after the active integration task
  completed.
- [x] Update the index after final integration freeze; post-freeze
  generalization is intentionally not part of this task.
- [x] Ensure the removed/rejected experiment or treatment is mentioned in the
  final submission narrative where relevant.

## Security and privacy

- [x] Run the conservative tracked-text credential hygiene check.
- [x] Confirm no credential values are printed by the checker or committed to
  the repository.
- [x] Do not inspect or include home-directory, Codex-auth, browser, or OS
  credential-store data.
- [x] Keep holdout expected outputs and evaluator-owned ground truth outside
  implementation-facing evidence.
- [ ] Re-run credential hygiene on the final integrated tree.
- [ ] Review the final video, screenshots, logs, and repository history for
  personal data or credentials.

## Demo and video

- [ ] Record a realistic end-to-end flow: capture, later processing, attention,
  memory/history, unknown state, and approval-gated action.
- [ ] Keep the solution video at or below five minutes.
- [ ] Show the current approved metric/evidence artifact and its limitations.
- [ ] Verify the video URL works in an unauthenticated browser.
- [ ] Enter the final video URL into the HackerEarth submission.

## HackerEarth submission

- [ ] Confirm the repository URL is correct and publicly accessible as intended.
- [ ] Confirm the video URL is entered in the submission form.
- [ ] Confirm the final narrative distinguishes development evidence from
  holdout and production claims.
- [ ] Confirm the README, changelog, reproduction guide, trajectory index, and
  checklist are included in the submitted revision.
- [ ] Confirm the final submission description names the main failure mode and
  the concise product hot take.

## Final freeze

- [x] Freeze the integrated implementation SHA in
  `docs/IMPLEMENTATION_FREEZE.md`.
- [ ] Freeze the authorized post-freeze generalization result, if any.
- [ ] Regenerate and inspect `final-comparison.json` or its approved successor.
- [x] Confirm baseline evidence remains unchanged.
- [x] Confirm no benchmark optimization was performed after freeze.
- [x] Confirm the local CI-equivalent gate is green on the exact freeze SHA;
  no remote CI status is claimed here.
- [ ] Confirm `git status --short` is clean on the exact submission SHA.
- [ ] Create and record the final tag.

## Known finalization items from this audit

These are intentionally documented rather than overwritten in this workstream:

- `eval/results/final-advanced-candidate.json` is named as a final candidate
  but predates the kept E005 result.
- `eval/results/final-advanced.json` reports the older E002 replay at
  `LQA-0M=0.7492295899`, `DSCR=72`.
- `eval/results/final-comparison-v1.json` compares the baseline with the older
  E002 replay, not current E005 (`LQA-0M=0.8695006212`, `DSCR=40`).
- No authoritative final comparison is generated during this freeze; it
  remains a later post-freeze submission task if explicitly authorized.
- `docs/EVALUATION.md` section 24 and `docs/REPRODUCTION.md` section 14 now
  label the older E002 material as historical/superseded and retain it for
  auditability.

## Path and metric audit notes

- No developer-specific absolute paths were found in submission-facing Markdown
  outside trajectory evidence. Historical trajectory prompts/summaries contain
  local attachment or skill paths; those are retained as historical evidence,
  not reproduction instructions, and are not a submission blocker.
- The official baseline references are consistent at approximately
  `LQA-0M=0.3014914553` / `DSCR=277`. The current E005 references are
  consistent at `LQA-0M=0.8695006212` / `DSCR=40`. The three stale named
  artifacts are historical and are not contradictions in the current
  narrative; historical changelog scores are expected and are not current
  claims.

## Hardening gate result

- [x] Qualification hard checks pass after the hardening trajectory summary is
  present.
- [x] Qualification warnings are understood: three stale named artifacts
  remain; the stale E002 narrative references were relabeled historical.
- [x] Focused qualification tests pass (5 tests).
- [ ] Re-run and record the final integrated-tree gate before submission.
