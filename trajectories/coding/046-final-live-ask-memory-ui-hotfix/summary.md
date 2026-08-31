# Summary

## Goal

Implement the authorized final Blackhole live Ask + Memory + UI hotfix on the verified `master` checkout, preserving the frozen benchmark/runtime and historical submission tags.

## Agent/tool used

Codex in the Blackhole repository, using shell inspection, `apply_patch`, the repository test/evaluation commands, and bounded live validation if the existing local provider CLI is usable.

## Initial hypothesis

The fresh dogfood failures are caused by current Ask routing allowing stale thread context to influence a self-contained question, answer formatting exposing retrieval/provenance internals, and the projection/UI layers treating valid occurrence events as competing state values. The UI defects are localized presentation/geometry issues.

## Important implementation decisions

- Made the current Ask question authoritative. Self-contained questions do not
  inherit stale thread topics; referential follow-ups use only bounded prior
  context as a referent hint, with the latest turn preferred. Prior assistant
  text is never evidence and public source references come from current
  selected facts.
- Kept the deterministic location, cost, time, and occurrence paths
  provider-free, while moving retrieval/provenance details out of the primary
  answer boundary. Supporting memory remains secondary/collapsible.
- Generalized occurrence detection across ordinary event verbs and guarded it
  against state qualifiers such as preferred drink, payment method, price, and
  recurring status. Occurrences coexist as current event facts and aggregate
  deterministically instead of becoming conflicts or false history.
- Added an actionable genuine-clarification response with a `Clarify in Ask`
  navigation/prefill action. It neither auto-submits nor persists a fact.
- Reworked Memory to show current state first with closed `History · N` and
  `Occurrences · N` disclosures, and refined Capture composer geometry and
  Attention's dedicated footer action area for mobile/desktop use.
- Added focused backend, planner, projection, and static/UI regressions. No
  provider configuration, model, reasoning, batch, frozen benchmark, evaluator,
  holdout, or V1 oracle changes were made.

## Tools/actions used

- Read the referenced pasted instruction in full.
- Verified branch, worktree, local HEAD, `origin/master`, and preserved tags before editing.
- Loaded the applicable design, forms/input, touch/accessibility, and UI-polish guidance.
- Created this trajectory before implementation.

## Failures encountered

The first attempted skill paths incorrectly included the root alias name and did not resolve. Correct absolute paths were then loaded successfully. No repository changes had been made at that point.

## Retries or changed approaches

None beyond correcting the skill file paths.

## Human feedback or checkpoints

The pasted instruction is the authorization and scope checkpoint. Starting state matched exactly: `master`, clean worktree, local and `origin/master` at `bcf43aed7870c69f0a2501f744641b5fda5778a7`.

## Evaluation performed

- Focused hotfix suite: `39/39`.
- Full application suite: `196/196`.
- Evaluator suite: `10/10`.
- Product acceptance harness: `7/7`.
- Root suite: `213/213`.
- Integrated Product V2 acceptance: `50/50 PASS`, all seven quality gates PASS,
  latency gate PASS, and no live provider in the integrated harness.
- Compileall, JavaScript syntax, benchmark structural check (`200` events and
  `4` checkpoints), non-scored contract smoke, qualification inventory, and
  `git diff --check` passed. Qualification retained four known historical
  warnings and no hard failures.
- Bounded live smoke used a fresh temporary Home with four synthetic captures
  and three Ask requests. All captures and asks returned HTTP 200; processing
  ended at `4` processed / `0` failed with one attempt each and zero retries.
  The topic-switch Ask stayed current-question-first, the real X occurrence
  Memory stayed known occurrence state without false clarification/conflict,
  and the follow-up retained only the latest occurrence topic. Exact outputs
  and state are recorded in the runtime trajectory.
- Browser review covered Capture, Attention, Memory, Ask, clarification
  navigation, and desktop/mobile dimensions; the viewport was reset after the
  review. Reduced-motion CSS/static checks remained green.

## Result

The authorized hotfix is implemented and the final live UX gate passes its
required criteria. The live provider rendered the two-unit event as `Aug 29`
in one aggregate label even though the capture text said yesterday; that exact
observation is preserved in the runtime trace and was not hidden or used to
change provider configuration, benchmark semantics, or model settings.

## Regressions or unresolved issues

No unresolved deterministic regression was observed. The four qualification
warnings are pre-existing historical-artifact/path warnings. The live
temporal-label wording noted above is an observed provider output and remains
disclosed; no follow-up live retry was run beyond the authorized bounded cap.

## Final decision

KEEP. This is an explicitly authorized post-freeze product UX/generalization
hotfix, not E006 and not a change to the frozen benchmark track. The
implementation/evidence stage is committed as
`93e497abf10be08bc7186fa97f071c6d20c3a9aa`; the final documentation/tag
handoff is recorded in the follow-up commit.

## Related git commit

Implementation/evidence commit:
`93e497abf10be08bc7186fa97f071c6d20c3a9aa`.
Final documentation/tag commit: recorded below after Git finalization.
