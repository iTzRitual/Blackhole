# Final demo presentation polish — trajectory summary

## Goal

Apply the explicitly authorized bounded BLACKHOLE final demo
presentation/UX hotfix to Ask, Capture, Attention, and Memory without
reopening Product V2 architecture, semantic extraction, model configuration,
benchmark/evaluator semantics, V1 behavior, or frozen runtime work.

## Agent/tool used

Codex in the Blackhole repository, using the referenced pasted instruction,
the applicable local design/form/accessibility/browser skills, shell
inspection, `apply_patch`, the repository's Python/Node gates, and the local
browser for visual review.

## Initial hypothesis

The remaining demo failures were presentation-boundary defects: structured
labels and values were being copied into awkward deterministic prose,
attribution was leaking into ordinary answers, the Ask footer duplicated the
grounding affordance, and the web surface needed bounded chat-scroll and
composer geometry corrections. The smallest safe repair was to keep selected
structured evidence and deterministic arithmetic intact, route only the
identified English lexical-gap surface through the existing semantic renderer,
and make feedback/scroll behavior transient and state-aware.

## Important implementation decisions

- Kept raw captures and provenance intact while making ordinary fact and
  occurrence prose omit attribution. The attribution value remains on the
  structured item and can be rendered explicitly for a provenance use case.
- Added natural location renderers for safe English/Polish deterministic
  paths. An English lexical gap with a known selected fact uses the existing
  bounded semantic answer provider, with no raw capture replay and with
  evidence IDs still required; unsupported provider output falls back to the
  deterministic selected evidence.
- Kept occurrence totals generic and deterministic, joining details with the
  current question's object hint when available and removing `reported by
  self` from ordinary prose.
- Removed the visible Ask grounding footer while retaining the supporting
  memories disclosure, changed Capture success to the transient `Out of mind`
  toast with Undo, moved Capture failures to accessible transient error toasts,
  and removed the reserved inline feedback row.
- Made Ask follow the latest message after a new send/answer or entering an
  existing thread, preserve deliberate upward reading, explicitly reset a new
  thread to the top, and reserve space above bottom navigation including safe
  area.
- Centered Capture controls without vertical translation hacks and vertically
  centered Attention's Done action while preserving lifecycle, badge, and
  touch-target behavior.
- Did not change provider configuration, prompts, batch size, V1/benchmark or
  evaluator artifacts. `IMPROVEMENT_CHANGELOG.md` was not changed because this
  was not a benchmarked optimization experiment; no new durable architecture
  decision required `docs/DECISIONS.md`.

## Tools/actions used

Read the attached pasted task and repository guidance; verified `master`, a
clean worktree, local `HEAD`, `origin/master`, and the existing final tag at
the required starting SHA; created this coding trajectory before
implementation; applied the scoped runtime/UI/test changes; ran focused and
full gates; reviewed the local app at 390×844 and 1280×900; attempted the
authorized synthetic live smoke; and prepared the runtime trace and trajectory
index updates.

## Failures encountered

- The first skill-path lookup used unresolved alias-shaped paths; the required
  skill files were then read successfully from their absolute paths.
- The first broader naturalization attempt routed too many paths and retried
  retrieval, which exposed provider fixtures with no answer. It was narrowed
  to the English generic lexical-gap case, preserved the already-selected
  evidence, and rejected provider prose without evidence IDs before falling
  back deterministically.
- In the browser, pressing Enter through the automation surface did not submit
  the fixture form; the same interaction was verified with the visible submit
  control. This was an automation interaction quirk, not a product failure.
- The live HTTP harness returned after its 30.2-second shell wait without a
  retained session handle or result. The temporary Home was removed and no
  second live run was made; the incomplete attempt is recorded separately in
  the runtime trajectory.
- The first qualification inventory correctly reported this summary as
  missing. The summary and runtime trace are now being added before the final
  inventory rerun.

## Human feedback or checkpoints

The referenced pasted instruction is the authorization and scope checkpoint.
Starting-state verification passed: branch `master`, clean worktree, local
`HEAD`, `origin/master`, and `hackathon-submission-final` all matched the
required starting SHA `0ecd49443ef7c85367a4375b0b8dacbcccc2d0c6` before edits.

## Evaluation performed

- Focused hotfix suites: `52/52 PASS` after the final focused assertions.
- Application suite: `206/206 PASS`.
- Evaluator suite: `10/10 PASS`.
- Product acceptance harness: `7/7 PASS`.
- Root discovery suite: `223/223 PASS`.
- Integrated Product V2 acceptance: `50/50 PASS`, all listed case gates
  passing, latency gate passing, and `live_provider_used=false`; result:
  `eval/results/product-v2-integrated-acceptance.json`.
- Compileall, Node syntax, benchmark structural check (`200` events and `4`
  checkpoints), non-scored contract smoke, and `git diff --check` passed.
- Qualification inventory passed after this trajectory was indexed, with four
  pre-existing warnings and no hard failures.
- Local browser review covered Capture, Ask (including a long thread and
  upward reading), Attention, Memory, the Capture success toast, and new-thread
  reset at both requested viewport sizes. The visual browser viewport was reset
  after review.
- The bounded live attempt is not counted as a PASS; its exact inputs and
  missing result are in
  `trajectories/runtime/048-final-demo-presentation-polish/trace.json`.

## Result

The scoped implementation is complete and the deterministic/local visual gate
is green. The user-visible presentation defects are addressed without
changing benchmark/evaluator semantics or raw/provenance boundaries. Overall
submission status remains `PARTIAL` only because the authorized live smoke did
not return a recoverable result; no live semantic success is claimed.

## Regressions or unresolved issues

No deterministic application, evaluator, acceptance, root, syntax, or
benchmark-structure regression was observed. Qualification retains the four
pre-existing historical warnings listed by the inventory checker. The live
smoke result is unresolved due to execution-context loss rather than an
observed application response; no additional live run was attempted.

## Final decision

KEEP the bounded presentation/UX hotfix. This is an explicitly authorized
post-freeze presentation/generalization change, not E006 and not a benchmark
optimization. Do not infer a live PASS from the incomplete attempt.

## Related git commit

Pending final commit and remote verification.
