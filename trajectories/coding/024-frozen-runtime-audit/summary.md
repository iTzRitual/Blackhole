# Frozen runtime audit trajectory summary

## Goal

Perform a rigorous read-only pre-submission audit of the frozen Blackhole
runtime without changing runtime behavior, accessing generalization material,
running a provider/baseline/scorer, or optimizing metrics.

## Agent/tool used

Codex primary agent using PowerShell, Git, Python's deterministic unittest
runner, temporary Python probes with fake providers/temporary SQLite stores,
repository search, local CLI help/version output, and the W3C Secure Contexts
specification. No subagent was used.

## Initial hypothesis

The documented processing-row limitation was likely real but its effect on Ask
freshness, retry ordering, and partial derived commits needed direct failure
injection. Capture-provider independence, benchmark isolation, and the absence
of consequential action paths were expected to hold.

## Important implementation decisions

- Created an isolated worktree/branch from the peeled
  `implementation-freeze-v1` commit.
- Treated this as evidence collection only; no discovered issue was fixed.
- Restricted all repository access to allowed frozen paths and public DEV
  contract/query artifacts.
- Used fake providers and temporary stores for failure injection.
- Classified findings by submission impact and distinguished benchmark
  invalidation from product hardening.

## Tools/actions used

- Read the human instruction from the supplied pasted-text attachment.
- Verified the annotated tag and base commit, branch, worktree, and clean
  primary worktree.
- Inspected the requested runtime, Host/PWA, provider, baseline, prompt,
  evaluator, test, architecture, evaluation, freeze, README, and reproduction
  files.
- Searched allowed paths for DEV names, event/scenario IDs, `state_key`,
  expected-output references, and evaluator imports.
- Ran the full deterministic test suite: 85 tests.
- Probed stuck `processing`, later-pending behavior after failure, partial
  commits/retry, corrupted config, invalid Unicode, cross-origin writes,
  side-effecting GET Ask, and arbitrary Host handling.
- Checked local `codex exec --help` without invoking a model; confirmed the
  meanings of `--ephemeral` and `--ignore-user-config`.
- Verified service-worker secure-context behavior against the W3C specification.

## Failures encountered

- The short name `implementation-freeze-v1` initially appeared to resolve to
  two hashes. Investigation showed `daa3e4d...` is the annotated tag object and
  `8d3b4ff...` is its peeled commit; the worktree is correctly based on the
  peeled commit.
- One broad source dump was truncated, so review continued with targeted line
  ranges and searches.
- A PowerShell/`rg` glob expression produced a Windows path parsing error; it
  was replaced with explicit paths and `-g` filters.

## Retries or changed approaches

- Rechecked tag references and common Git directory before code review.
- Replaced broad concatenated reads with focused function ranges.
- Added direct temporary probes after the passing suite showed that crash and
  cross-request failure states were not covered.

## Human feedback or checkpoints

The initiating human instruction explicitly required no fixes, absolute
generalization-oracle isolation, deterministic tests only, three tracked output
files, an isolated audit commit, and a final YES/NO freeze-abandon decision.
No later human checkpoint changed scope.

## Evaluation performed

- `python -m unittest discover -s . -p "test_*.py" -v`: 85/85 passed in
  13.191 seconds.
- Deterministic temporary failure injection confirmed stuck processing,
  cross-call chronology bypass, partial-commit double-counting, stale Ask,
  corrupt-config failure, invalid-Unicode rejection, cross-origin capture, GET
  provider triggering, and arbitrary Host acceptance.
- No official baseline, scorer, benchmark generator, provider inference, or
  generalization evaluation was run.

## Result

0 P0, 10 P1, 4 P2, and 1 P3 findings. Capture-provider independence,
immutable raw evidence, no consequential action path, no hidden DEV identifier
coupling, and frozen public evaluation fairness were confirmed. Product runtime
hardening is required before final submission.

## Regressions or unresolved issues

No runtime regression was introduced because no runtime code changed. All
findings remain unresolved by design in this audit. The highest-risk unresolved
areas are processing recovery/atomicity, stale Ask semantics, loopback API
origin security, non-ephemeral provider sessions, attachment truthfulness,
LAN-PWA claims, and stale quickstart instructions.

## Final decision

**REVISE after generalization, before final submission.** Do not abandon or
mutate the frozen reference before opening the isolated generalization oracle;
no P0 benchmark/evaluation invalidator was found.

## Related git commit

Commit message: `audit: review frozen Blackhole runtime` (the commit containing
this trajectory and `docs/audits/FROZEN_RUNTIME_AUDIT.md`).
