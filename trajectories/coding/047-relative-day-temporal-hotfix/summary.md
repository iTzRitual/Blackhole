# Relative-day temporal hotfix — trajectory summary

## Status

Complete. The deterministic fix is kept; no live provider call was made.

## Goal

Repair the generic Product V2 relative-day normalization boundary so that
relative expressions resolve to the capture's local calendar date, preserve
capture timezone semantics across DST, and feed deterministic occurrence Ask
aggregation with the correct dates.

## Agent/tool used

Codex in the Blackhole repository, using shell inspection, `apply_patch`, the
repository's deterministic Python/Node validation commands, and Git. The
authorized main fix used no live provider call.

## Initial hypothesis

The observed Aug 29 result entered at the temporal normalization boundary:
`yesterday` was not handled as a generic local-day expression, while a
provider-supplied structured absolute date could survive because the old
normalizer preferred an available `normalized` field. The smallest safe repair
was to anchor recognized relative-day expressions to capture-local calendar
dates and override an inconsistent provider absolute only when raw relative
meaning is explicit.

## Important implementation decisions

- Added one bounded relative-day normalizer for English `today`/`yesterday`/
  `tomorrow` and Polish `dzisiaj`/`wczoraj`/`jutro` (including `dzis`). It
  handles the existing compact provider shapes and gives raw `expression`
  precedence over an inconsistent absolute proposal.
- Derived the target from the persisted capture timestamp's local date with
  calendar-day arithmetic and `datetime.combine`, preserving the capture
  `ZoneInfo` across DST. No current wall clock, provider retry time, or
  arbitrary UTC 24-hour subtraction is used.
- Preserved the event timezone in current occurrence projections and made the
  deterministic occurrence renderer compare dates in that timezone.
- Left absolute timestamps, relative minutes/hours, weekdays, deadlines,
  reschedule behavior, provider configuration, UI, benchmark/evaluator
  semantics, and frozen V1 artifacts unchanged.

## Tools/actions used

Read the referenced attachment and relevant repository guidance/docs; verified
the exact `master`/clean-worktree/origin starting gate; added focused
reproductions before implementation; applied the code/test repair; ran the
required regression and static gates; regenerated the Product V2 integrated
acceptance result; updated the decision, dogfood, README, submission checklist,
and trajectory index records; and committed directly to `master`.

## Failures, retries, and changed approaches

- The first combined implementation patch had an incorrect context for the
  earlier occurrence-renderer function, so it applied no changes. The repair
  was split into focused patches.
- The first broader post-fix targeted run caught a `NameError` because the
  existing `_natural_date` folded-text variable had been removed while
  refactoring. The variable was restored and the focused suite was rerun.
- The pre-change reproduction was intentionally red: the 12-test focused run
  had 8 failures and 1 error, including missing relative-day normalization,
  the wrong Aug 29 absolute date, a failed DST case, and the incorrect
  occurrence Ask date.

## Human feedback or checkpoints

The referenced pasted instruction was the scope checkpoint and identified the
final Mac dogfood failure: a deterministic occurrence Ask response for an Aug
31 capture rendered `yesterday` as Aug 29. Starting-state verification passed:
branch `master`, clean worktree, local `HEAD`, and `origin/master` were all at
`ec7665a98082d0f343d0d8e587c5db7eea185fd0`.

## Evaluation performed

- Focused temporal suite: `12/12 PASS`.
- Targeted Product V2/timezone/semantic suites: `47/47 PASS`.
- Application suite: `200/200 PASS`.
- Evaluator suite: `10/10 PASS`.
- Acceptance harness: `7/7 PASS`.
- Root discovery suite: `217/217 PASS`.
- Integrated Product V2 acceptance: `50/50 PASS`, all `7/7` quality gates
  PASS, `live_provider_used=false`; the report is
  `eval/results/product-v2-integrated-acceptance.json`.
- Compile, Node syntax, benchmark integrity (`200` events/`4` checkpoints),
  contract smoke, qualification inventory, and `git diff --check` all passed.

The deterministic reproduction now resolves the requested values to:

```text
yesterday/wczoraj  -> 2026-08-30T00:00:00+02:00
today/dzisiaj      -> 2026-08-31T00:00:00+02:00
tomorrow/jutro     -> 2026-09-01T00:00:00+02:00
```

The occurrence Ask result is `You recorded 3 unit across 2 instances of X —
2 unit yesterday; 1 unit today.` with `mode=occurrence_totals`,
`provider_used=False`, and no Aug 29 mention. The DST regression preserves
`+01:00` for March 28 and `+02:00` for March 30 in Europe/Warsaw.

## Result

The original relative-day reproduction is gone. Captured relative temporal
meaning is now deterministic, capture-anchored, timezone-preserving, and
occurrence-safe.

## Regressions or unresolved issues

No regression was observed in the required deterministic suites. The
qualification checker retained four pre-existing non-blocking historical
warnings; none was introduced by this task. No live-provider behavior was
claimed or validated.

## Final decision

KEEP. This is a final correctness hotfix and not a benchmark optimization or
E006 experiment; `IMPROVEMENT_CHANGELOG.md` and frozen benchmark/evaluator
artifacts were not changed.

## Related git commit

Implementation/evidence commit: `c9aba33` (`fix: anchor relative-day
semantics to capture time`).
