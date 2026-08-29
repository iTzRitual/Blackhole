# Generalization Public V1R1 Seal — Trajectory Summary

## Goal

Create a new blind public branch `generalization/public-v1r1` from
`implementation-freeze-v1`, containing only the repaired public
generalization inputs, a safe public manifest, and seal trajectory evidence.
Preserve historical `generalization/public-v1` and all failed pre-runtime
branches; do not expose oracle information or run the baseline, Blackhole
runtime, provider/model calls, or scoring.

## Agent/tool used

Codex in the shared local workspace using PowerShell, Git, the repository patch
tool, and deterministic JSON/hash checks. No authentic session transcript is
available; none was fabricated.

## Initial hypothesis

The repaired oracle's three public cases, response contract, and query bundle
can be copied onto a branch rooted directly at `implementation-freeze-v1`
without bringing along oracle history or answer material.

## Important implementation decisions

- Created `generalization/public-v1r1` from the exact
  `implementation-freeze-v1` commit
  `8d3b4ff7a1979540f2e65dd9b493f0731e006f72`.
- Copied only `response-contract-v2.json`, `query-bundle-v2.json`, and
  `scenario-g01.json`, `scenario-g02.json`, and `scenario-g03.json` from the
  repaired oracle.
- Added only `PUBLIC_MANIFEST.json` and this public seal trajectory.
- The manifest contains public input hashes and the pre-runtime repair note;
  it contains no expected hashes, defect catalog, generator, audit, or oracle
  metadata.

## Tools/actions used

- Switched the existing public checkout from historical `generalization/public-v1`
  to the new branch without changing the historical branch reference.
- Copied the five approved public files from the repaired oracle.
- Parsed all public JSON files and recomputed their SHA-256 values.
- Audited the branch allowlist, forbidden generalization paths, public manifest
  fields, protected runtime paths, historical development expected material,
  and oracle ancestry.
- Did not run any baseline or advanced runner, provider/model call, evaluator,
  or scoring command.

## Failures encountered

None during public branch creation or audit.

## Retries or changed approaches

None.

## Human feedback or checkpoints

The human-provided pasted specification required a new branch from the
implementation freeze, preservation of historical failed branches, strict
generalization-oracle absence, and a public-only commit and push. No
additional human feedback was received.

## Evaluation performed

The final public audit passed before push:

- Branch: `generalization/public-v1r1`, rooted at the exact
  `implementation-freeze-v1` tag target
  `8d3b4ff7a1979540f2e65dd9b493f0731e006f72`.
- Generalization package allowlist: exact six files — public manifest, public
  response contract, public query bundle, and the three public cases.
- Forbidden generalization paths: absent — `expected/`, generator, `audit/`,
  oracle `MANIFEST.json`, and defect catalog material.
- Structural public case check: g01/g02/g03 each have 80 events and 80
  object payloads with string `text`; total events 240; checkpoints are
  20/40/60/80 for each scenario.
- Public files match the repaired oracle byte-for-byte, and all manifest hashes
  match the copied files.
- Historical `benchmark/dev/expected/**` exists as frozen repository material
  and has an empty diff from `implementation-freeze-v1`; it is allowed and
  unchanged.
- Oracle ancestry: original oracle commit and original oracle final HEAD are
  both unreachable from this branch.
- Historical `generalization/public-v1` and `origin/generalization/public-v1`
  remain at `39d003cfe63dcba1e5ce701bca785963b9683157`.
- No baseline runner, advanced runner, provider/model call, evaluator, or
  scoring command was run.

The required public hashes recorded in the manifest are:

- Response contract:
  `c26d063189be0f44a7f099b49206d1731d0f933c60ece066c58630ce25ff0534`.
- Query bundle:
  `6e5a0295b239f1029e2f38b713e1cba9f6ca6c921e9f712c5022b5f34814d366`.
- Public cases: g01
  `c0dd1c6255c3591fb4467e8ac6bb4e46bffbd37661cf38bcb6ba67a9247a3cb5`, g02
  `22747fe3e01b4ed4ae41e5a0682cc584e72c487f7c9cff53a29d233d9d35f938`, g03
  `ca19c548d60c0a77ba742aa6c00532fac26d335dadcfdca86d209786744c3fec`.

## Result

The public V1R1 input-only branch passed the blindness/provenance audit and was
committed locally at
`6efbacc4195bf90e7711c1663e725f508927ef75` (`benchmark: seal generalization
public v1r1 inputs`). Expected outputs remain absent from this branch, while
historical frozen `benchmark/dev/expected/**` material is allowed and remains
unchanged. The branch is ready for the authorized push; no runtime or scoring
execution occurred.

## Regressions or unresolved issues

No packaging, blindness, ancestry, protected-path, hash, or structural
regression was observed. Generalization accuracy and scores are intentionally
not available and must not be inferred.

## Final decision

**KEEP / SEAL** the public V1R1 input-only branch. Push only
`generalization/public-v1r1`; do not push the oracle branch, merge either
branch, run the baseline or advanced runner, or score the scenarios.

## Related git commit

`6efbacc4195bf90e7711c1663e725f508927ef75` — `benchmark: seal generalization
public v1r1 inputs`.
