# Generalization V1R1 public archive

Status: archive assembled; publication verification pending.

## Goal

Preserve and publish the public-safe Generalization V1R1 evaluation history
without changing runtime behavior or benchmark semantics, while consolidating
the remote branch state exactly as authorized by the initiating instruction.

## Agent/tool used

Codex in the shared repository workspace. Work is being performed through the
repository shell and patch tools; no provider calls are authorized or needed.

## Initial hypothesis

Not an experiment. The archive can be produced from `origin/master`, the two
sealed public-safe V1R1 branches, and individually verified public-safe result
files, provided the remote safety gates and ancestry checks pass.

## Important implementation decisions

- Fetched `origin` before any publication work and verified the expected six
  remote heads. Old `origin/master` remained exactly
  `d21c0ce46dd7589c93eefa4b0dd07ee98063a66b`; the obsolete V1 tips discovered
  were public V1 `39d003cfe63dcba1e5ce701bca785963b9683157` and failed blind
  Blackhole V1 `3e1fcdde44853a188e6d2e74241e65531cece57b`.
- Created the fresh archive worktree at
  `C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-public-archive-v1r1`
  on local branch `maintenance/public-archive-v1r1`, based exactly on the old
  `origin/master`. The normal public worktree was not used for consolidation.
- Created the five required annotated archive tags at the exact discovered
  branch tips and preserved the existing annotated `implementation-freeze-v1`
  tag at its resolved target.
- Merged only the two sealed public-safe V1R1 branches with normal merge
  commits: baseline merge `d617d8c82f6ad2cbc30c19d20cc6e705d99fbf37` and
  Blackhole merge `21c31d7cc65a41913025088b9a76e3a69167bad4`. No conflicts
  occurred, and the local oracle/scoring tips are not ancestors of the sealed
  branches.
- Copied only the ten listed public-safe scoring/report/trajectory files from
  the local scoring worktree. Their six supplied score-artifact hashes matched
  exactly; inspection found only hashes, filenames, metrics, counts,
  chronology, and verification statements, with no expected-answer bodies.
- Preserved the sealed candidate Git blobs and manifests unchanged. The six
  manifest candidate hashes are the CRLF-normalized Windows checkout hashes;
  the archive worktree uses LF-normalized Git blobs, whose independent hashes
  are recorded in the scoring seal evidence. No candidate or manifest was
  rewritten.
- Updated only the archive-facing README, evaluation document, trajectory
  index, and required archive trajectory; no runtime, benchmark, evaluator,
  prompt, baseline, or protected application path was changed.

## Tools/actions used

- Read the referenced pasted instruction and the relevant repository guidance
  before acting.
- Used PowerShell/Git read-only checks for status, worktrees, ancestry, remote
  heads, tag targets, path inventories, Git-blob identity, and SHA-256 values.
- Used `git fetch origin`, `git worktree add`, annotated `git tag`, two
  `git merge --no-ff` operations, explicit ordinary filesystem copies for the
  authorized scoring files, and `apply_patch` for documentation/trajectory
  edits.
- Kept the oracle worktree and local scoring worktree untouched as Git
  histories; no provider or model calls were made.

## Failures encountered

- The first tag-check script compared `implementation-freeze-v1` to an
  incorrectly invented full SHA and stopped before creating any tag. The
  existing tag was then resolved directly and preserved without change.
- The first candidate hash check used the archive worktree materialization and
  reported LF hashes rather than the supplied CRLF checkout hashes. The
  discrepancy was isolated to line endings; all six CRLF-normalized hashes
  matched the sealed manifests and all six raw Git blobs matched their sealed
  source refs.
- One intermediate PowerShell raw-blob hash script had a parser error and was
  rerun corrected. No repository state was changed by either script failure.

## Retries or changed approaches

The hash verification approach changed from direct working-tree hashing to an
explicit comparison of sealed Git blobs and in-memory CRLF-normalized bytes;
the sealed files themselves were left untouched.

## Human feedback or checkpoints

The initiating instruction requires a stop/report if the remote master tip,
expected branch set, tag targets, worktree paths, or conflict/public-safety
checks do not match the specified conditions.

## Evaluation performed

Pre-publication deterministic checks are pending. No provider-backed run is
authorized or needed for this archive task.

## Result

The archive worktree contains both sealed V1R1 merge histories, the inspected
public-safe scoring evidence, and the required documentation updates. Remote
publication, tag push, obsolete-branch deletion, final deterministic checks,
and temporary-worktree cleanup remain pending.

## Regressions or unresolved issues

No runtime or benchmark regression has been observed. The supplied candidate
hashes require the documented CRLF checkout-byte interpretation; raw Git-blob
hashes are intentionally different because the repository stores LF-normalized
blobs.

## Final decision

Pending final publication gate.

## Related git commit

The planned public evidence commit message is
`generalization: archive sealed V1R1 evaluation`; the exact final SHA will be
recorded in the handoff after publication.
