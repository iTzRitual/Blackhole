# Relative-day temporal hotfix — trajectory summary

## Status

In progress. The required starting-state gate passed before implementation.

## Goal

Repair the generic Product V2 relative-day normalization boundary so that
relative expressions resolve to the capture's local calendar date, preserve
capture timezone semantics across DST, and feed deterministic occurrence Ask
aggregation with the correct dates.

## Agent/tool used

Codex in the Blackhole repository, using shell inspection, `apply_patch`, the
repository's deterministic Python/Node validation commands, and Git. No live
provider call is planned for the main fix.

## Initial hypothesis

The observed Aug 29 result likely entered at the temporal normalization
boundary: `yesterday` is not handled as a generic local-day expression, while
a provider-supplied structured absolute date can survive because the current
normalizer prefers an available `normalized` field. The smallest safe repair
should anchor recognized relative-day expressions to capture-local calendar
dates and override only inconsistent provider absolutes when raw relative
meaning is explicit.

## Human feedback or checkpoints

The referenced pasted instruction is the scope checkpoint. Starting-state
verification passed: branch `master`, clean worktree, local `HEAD` and
`origin/master` both at `ec7665a98082d0f343d0d8e587c5db7eea185fd0`.

## Evaluation performed

Pre-change deterministic reproduction, after adding only the focused tests,
failed as expected: `python3 -m unittest app.tests.test_product_v2_timezone
-v` ran 12 tests with 8 failures and 1 error. Plain and structured
`yesterday` values returned no normalized timestamp; a temporal field remained
without `valid_from`; the wrong model absolute remained `2026-08-29`; the DST
regression failed; and the two-capture occurrence Ask reproduction retained
Aug 29. Existing timezone-discovery and relative-minute tests remained green.

No provider call was made.

## Related git commit

Pending.
