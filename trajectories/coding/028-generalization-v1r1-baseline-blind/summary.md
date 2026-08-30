# Summary

## Goal

Execute and seal the official blind post-freeze generalization V1R1 baseline
from a fresh clone at public HEAD
`79bea04e432e6566e3d6989e8fa411e7c613908b`, with one successful candidate for
each of g01, g02, and g03, structural validation only, no generalization
oracle access, and no scoring.

## Agent/tool used

Codex working in the fresh clone
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-gen-baseline-v1r1`,
using the existing `baseline/run_baseline.py` and the local Codex CLI.

## Initial hypothesis

Not applicable. This was a prescribed blind execution and sealing task, not a
benchmark-optimization experiment.

## Important implementation decisions

- Created a new single-branch clone of `generalization/public-v1r1` and verified
  the exact required public HEAD and supplied public hashes.
- Created `generalization/blind-baseline-v1r1` without modifying runtime code,
  prompts, benchmark inputs, or evaluator code.
- Used the frozen runner with Codex CLI, `gpt-5.6-luna`, reasoning `max`,
  read-only isolated workspace, 80 events, 900-second provider-call timeout,
  and native discarded checkpoint forks.
- Preserved operational failures in separate runtime-attempt directories and
  did not retry for semantic quality.
- Performed the requested metadata-only environment check before G03. The
  current runner environment resolved to Codex CLI 0.150.0-alpha.12.2 at
  `C:\Users\natan\AppData\Local\OpenAI\Codex\bin\fac60c5e9a2ae3df\codex.EXE`;
  preserved G01/G02 metadata matched the executable basename, provider, model,
  and reasoning effort. Historical full path/version fields were not present in
  the runner metadata.

## Tools/actions used

- Read the supplied pasted instruction file before continuing.
- Cloned the public branch and verified status, HEAD, required public files,
  payload object shape, public hashes, event counts, and public checkpoints.
- Ran the frozen baseline runner in order for g01, g02, and g03.
- Ran metadata-only inspection of candidate run metadata and the current Codex
  executable/version.
- Ran a structural-only validator for JSON, response contract, scenario ID,
  checkpoint keys/values, query object shape, assertion field shape, and public
  event source references.
- Computed SHA-256 hashes and created the candidate manifest.

## Failures encountered

- Two initial public verification commands used incorrect PowerShell/schema
  assumptions; they were corrected before any baseline run and did not alter
  repository content.
- An environment-evidence file was initially targeted at a misspelled path;
  the exact accidental file was removed and recreated inside the fresh clone.
- G02 initial attempt failed at checkpoint 40 and G02 retry 1 failed at
  checkpoint 80, both as runner-reported operational fork/query failures.
- G03 initial attempt failed at checkpoint 40 as a runner-reported operational
  fork/query failure.

## Retries and changed approaches

G01 succeeded on its initial attempt. G02 succeeded on retry 2 after two
operational failures. G03 succeeded on retry 1 after one operational failure.
All successful runs used the same frozen command/configuration; no runner,
prompt, model, reasoning, timeout, or baseline-protocol change was made.

## Human feedback/checkpoints

The human capped G02 retry 2 as the final allowed G02 attempt and prohibited a
third G02 run. The human allowed G03 one initial attempt plus at most one
operational retry, required the metadata-only environment consistency check,
and instructed autonomous continuation without semantic inspection or
scoring. A separately installed Codex CLI 0.151.0 was not selected by the
runner environment used for this run.

## Evaluation performed

Structural validation only; no `eval/score.py`, `eval/score_slice.py`, LQA,
DSCR, TP, FP, or FN calculation was performed. All candidates passed the
recorded structural checks. No generalization expected output, oracle, or
expected hash was accessed or recorded. Historical DEV expected material was
not used.

## Result

One candidate was sealed for each scenario:

- g01: SHA-256
  `943571f22882429a0518005ba41cbc9ffba3d3a73153ac2aae9f18e1287bc71b`,
  runtime 3060.775933 seconds, usage totals input 110669 / cached input 87040 /
  output 72 / reasoning output 32.
- g02: SHA-256
  `2bdc02ab4f0d51b612ede8281d9dedafba837c0e2d56608ba16248740626f59c`,
  runtime 2960.018914 seconds, usage totals input 110927 / cached input 92160 /
  output 97 / reasoning output 53.
- g03: SHA-256
  `0a1e1674aab9e80a59c3318e83693b151fab1f6c79a6b153024e33f1269f0e3f`,
  runtime 3178.631731 seconds, usage totals input 110857 / cached input 87040 /
  output 86 / reasoning output 42.

The candidate manifest is
`eval/results/generalization/v1/BASELINE_CANDIDATE_MANIFEST.json`. Runtime
trajectories are under the three `trajectories/runtime/generalization-v1r1-*`
directories. The manifest SHA-256 is computed immediately before commit.

## Regressions or unresolved issues

No execution blocker remains. The frozen runner does not preserve the full
Codex executable path or CLI version in candidate metadata, so the pre-G03
consistency comparison could verify only the preserved executable basename,
provider, model, and reasoning fields against the current exact path/version.
No semantic quality conclusion was made.

## Final decision

KEEP the sealed blind baseline candidates and evidence. This is a reproducible
submission artifact set, not a scored result.

## Related git commit

To be recorded after the sealing commit.
