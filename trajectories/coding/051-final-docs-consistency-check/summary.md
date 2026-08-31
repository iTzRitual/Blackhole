# Documentation consistency check

## Goal

Complete the final Blackhole documentation consistency check without changing
product, benchmark, evaluator, or provider state.

## Agent/tool used

Codex in the Codex desktop app; shell inspection and `apply_patch` for local
documentation edits.

## Initial hypothesis

The remaining inconsistencies are stale judge-facing wording: the capture
success label is described as `Saved.`, provider-backed READY Ask is described
as optional, and some H2H prose uses PTS without the sealed expansion.

## Important implementation decisions

Work in the existing clean `master` checkout at the expected starting commit.
Use the sealed scoring file as the authority for PTS naming. Preserve the
frozen tag and all application, benchmark, evaluator, and result artifacts;
include the user's separately authorized screenshot deletion and README
cleanup.

## Tools/actions used

Read-only `git status`, `git rev-parse`, `git tag`, `git show-ref`, `rg`, and
`sed` audits; inspected the sealed `SCORING.md` and `SPEC.md`; read the final
video script end-to-end; applied minimal Markdown patches with `apply_patch`;
ran `git diff --check` and changed-path scope checks. No provider command,
benchmark command, or application test was run.

## Failures encountered

The first tag-peel command used invalid `^{peeled}` syntax and exited without
changing the repository. The first multi-file patch was rejected because one
surrounding line used lowercase `provider-independent`; it also made no file
changes. A later boundary check found two tracked documentation screenshots
deleted unexpectedly from the worktree; both were restored from `HEAD` before
staging. The user then explicitly authorized including that deletion and the
README screenshot-section removal.

## Retries or changed approaches

Used `hackathon-submission-demo-ready^{}` for the peeled tag commit, split and
corrected the Markdown patch context, restored the two explicitly named
tracked screenshot files while checking the original baseline, then deleted
those exact files again after the user's authorization. Removed the stale
checklist reference so the README cleanup and asset deletion remain coherent.

## Human feedback or checkpoints

The user explicitly required documentation-only changes, no benchmark rerun,
no provider calls, no app changes, direct commit to `master`, and no tag
movement.

## Evaluation performed

`SCORING.md` explicitly defines PTS as **Prompt-to-Truth Score**; `SPEC.md`
uses `PTS` without a competing expansion. The final video script was reread
end-to-end after editing. Targeted searches found no visible `Saved.` label in
the current submission/video instructions, and the current prose states the
provider-rendered READY Ask path, deterministic responsibilities, degraded
fallback boundary, mixed H2H result, and Attention/PTS comparison. `git diff
--check` passed. After the user explicitly authorized the separately noticed
screenshot/README changes, the two tracked screenshots were deleted and the
stale checklist reference was removed. No benchmark rerun or provider call was
made.

## Result

Current-facing documentation now uses `Out of mind` for normal Capture success,
describes asynchronous semantic understanding, states that a normal READY
semantic Ask is rendered by the configured provider from bounded deterministic
results, and names the sealed H2H macro score as Prompt-to-Truth Score (PTS).
The user-authorized screenshot deletion and README cleanup are also included;
all changed paths remain under documentation/trajectory scope. No app,
benchmark, evaluator, result, or tag files changed.

## Regressions or unresolved issues

No documentation regressions observed. Historical technical/audit records that
describe transport or earlier runtime behavior were left intact; the stale
current-facing presenter instructions were corrected. The published screenshot
section and its two assets were removed together under the user's explicit
authorization.

## Final decision

KEEP the documentation-only corrections. Commit directly to `master` and push;
the final commit SHA and frozen tag peeled SHA are reported in the handoff.

## Related git commit

The final docs-only commit on `master` for this task; SHA recorded in the final
handoff.
