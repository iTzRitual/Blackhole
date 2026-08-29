# Generalization Public Seal — Trajectory Summary

## Goal

Prepare a blind post-freeze public-input-only branch from the immutable
implementation freeze, after verifying that the existing generalization oracle
package is frozen, tracked, reproducible, and byte/hash consistent. Runtime,
provider, baseline, semantic extraction, and scoring execution are prohibited.

## Agent/tool used

Codex in the shared local workspace using PowerShell, Git, `rg`, and the
repository patch tool. No authentic session transcript is available; none was
fabricated.

## Initial hypothesis

The oracle worktree contains the previously frozen generated package and can be
sealed for blind execution by copying only its public inputs and adding safe
metadata, without changing frozen Blackhole code or exposing private answer
material.

## Important implementation decisions

- The oracle worktree was audited read-only. All ten required frozen artifacts
  exist and are tracked; no oracle packaging follow-up commit was needed.
- `generalization/public-v1` is based on the immutable
  `implementation-freeze-v1` tag target `8d3b4ff7a1979540f2e65dd9b493f0731e006f72`.
- Only the public response contract, public query bundle, three public cases,
  `PUBLIC_MANIFEST.json`, and this coding trajectory are added to the branch.
- The public manifest contains public scenario metadata and public input hashes
  only. It contains no private answer hashes, generator, audit, or defect data.

## Tools/actions used

- Ran oracle `git status`, recent log, tracked-file listing, tag dereference,
  and worktree inspection.
- Ran `python benchmark/generalization/v1/generate_generalization.py --check`
  in the oracle worktree; it passed without runtime or scoring.
- Recomputed SHA-256 values for the response contract, query bundle, three
  public cases, and three private oracle-side expected files; all matched the
  frozen manifest. The public five input files also match the oracle bytes.
- Created the sibling worktree, copied only the five approved public inputs,
  and added the safe public manifest.
- Parsed the public JSON inputs and statically parsed both runner sources while
  verifying that each exposes `--scenario`, `--query-bundle`, and
  `--response-contract`. Neither runner was invoked.
- Audited the generalization package allowlist, forbidden paths, public
  manifest fields, oracle ancestry, and protected-path diff before commit.

## Failures encountered

- The first read-only PowerShell artifact-summary command had a pipeline syntax
  error; it was corrected and rerun successfully.
- The first ancestry check used unquoted PowerShell assignments for the commit
  IDs; it was corrected and rerun with explicit commit arguments.

## Retries or changed approaches

The retries were limited to read-only command syntax corrections. No generated
content, frozen implementation code, configuration, benchmark, evaluator, or
oracle artifact was regenerated or edited.

## Human feedback or checkpoints

The user-provided specification requires a local public branch, no runtime or
provider calls, no scoring, no merge, and a final gate report. The public branch
contains no generalization expected-output directory or oracle generator and
has no generalization candidate output.

## Frozen configuration evidence

The official baseline configuration is the frozen
`prompts/runtime/baseline-v1.md` prompt plus
`prompts/runtime/baseline-runner-v2.md`, Codex CLI with `gpt-5.6-luna` and
`max` reasoning, read-only empty-workspace isolation, one chronological capture
batch per checkpoint segment in one persistent canonical session, and native
atomic Codex query forks that are never resumed. The official reproduction
invocation used a 1200-second timeout.

The kept E005 advanced configuration is Codex CLI with `gpt-5.6-luna`, high
semantic reasoning, batch size 50, retrieval relation recovery, deterministic
completeness, duplicate-evidence `consolidate`, deterministic query
projection, and the runner's 900-second default timeout. The E005 candidate
metadata records this configuration and the reproduction command confirms the
same flags. Its replay call records marked `max` are inherited metadata from
the replayed E001 extraction helper, not live E005 provider settings.

## Evaluation performed

- Oracle artifact presence/tracking: PASS; oracle worktree remained clean.
- Oracle generator check: PASS; 3 scenarios, 80 events each, 240 total events,
  checkpoints 20/40/60/80, and 12 query IDs.
- Public input parsing: PASS; all five inputs parse and manifest hashes match.
- Public case hashes: g01
  `7d085476b63de804f6166e6b0e94491b3f0dbc537425816f3f7bfd5b44025eb6`, g02
  `2676f16f53636eb0613a427cc85e2a5dd2c9496d3e79096b172cfd225d788368`, g03
  `cf9d32d150dac64d34059cf07041d9e0a8d075fc827afad1b1758e9ecd5a2223`.
- Response-contract SHA-256:
  `c26d063189be0f44a7f099b49206d1731d0f933c60ece066c58630ce25ff0534`.
- Query-bundle SHA-256:
  `6e5a0295b239f1029e2f38b713e1cba9f6ca6c921e9f712c5022b5f34814d366`.
- Static runner compatibility: PASS for both custom-input option sets; no
  runner or provider execution occurred.
- Oracle ancestry check: PASS; neither oracle freeze commit is reachable from
  the public branch.

## Result

The public-input-only bundle is sealed locally on `generalization/public-v1`.
The branch is based on `implementation-freeze-v1`, contains the three public
cases plus their public contract/query inputs and safe manifest, and preserves
the frozen runtime code. No provider calls, model calls, baseline execution,
Blackhole processing, candidate output, or scoring were performed.

## Regressions or unresolved issues

No packaging, protected-path, hash, leakage, or compatibility regression was
observed. Generalization accuracy and score remain intentionally unevaluated.

## Final decision

**KEEP / SEAL** the local public-input-only branch. Do not run generalization,
merge the branch, or push the oracle branch as part of this task.

## Related git commit

The final public-seal commit SHA is recorded after commit completion in the
handoff and by `git rev-parse HEAD` on this branch.
