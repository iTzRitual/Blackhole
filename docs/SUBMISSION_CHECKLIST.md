# Blackhole submission checklist

Status: local repository gate PASS; the exact remote/tag identifiers are
verified in the final handoff for the immutable submission commit. This is a
factual repository gate, not an aspirational feature backlog.

## Scope and authority

- [PASS] Work is being finalized directly on `master`.
- [PASS] The final documentation phase started from clean, identical
  `master` and `origin/master` at `73e0ad78498c3c5420d4e8ce0dcd7b44b22e6e1c`.
  The frozen Product V2 tag still peels to
  `cc0cca8e8d9c3a5ab0955f365ea71c639cac7548`.
- [PASS] The authorized Product V2 hotfix changed only current-question-first
  Ask routing/answer boundaries, generic occurrence projection/UI behavior,
  clarification action, and Capture/Attention/Memory presentation; the frozen
  V1 runtime and benchmark behavior remain unchanged.
- [PASS] No V1 oracle access, holdout inspection, prompt tuning, benchmark
  optimization, evaluator-ground-truth change, provider configuration change,
  or model/reasoning/batch policy change occurred. The separately authorized
  H2H used provider inference only on fresh synthetic worlds and did not feed
  its outputs back into Product V2 or V1 artifacts.
- [PASS] The frozen V1 benchmark, baseline, evaluator, calibration evidence,
  and recorded V1 metrics remain separate from Product V2 acceptance evidence.
- [PASS] No production hosting, Claude adapter, cloud sync, pairing, OCR
  guarantee, or consequential-action subsystem was added.

## Judge-facing package

- [PASS] [`README.md`](../README.md) leads with the product loop, quick start,
  subscription-first authentication boundary, final Product V2 defaults, V1
  versus Product V2 evidence separation, hot take, and known limitations.
- [PASS] [`docs/SUBMISSION.md`](SUBMISSION.md) contains the problem/user value,
  engineering solution, end-to-end quality, measured evidence, reproduction,
  insights, limitations, and privacy/claim boundaries.
- [PASS] [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) provides a realistic five-
  minute flow using synthetic prepared state plus one live immediate Capture.
- [PASS] The demo preparation utility populates a new/empty Home through the
  real Product V2 HTTP routes with the visible deterministic fixture provider;
  it does not write benchmark data, fake UI answers, or call a live provider.
- [PASS] The presentation-only `?fixture=1` browser mode is labeled as a
  visual-test fixture and is not presented as Product V2 state.

## Product V2 contract disclosure

- [PASS] Current Product V2 defaults are documented as model
  `gpt-5.6-luna`, low reasoning, and batch size `2`.
- [PASS] Legacy/V1-compatible high-reasoning and batch-size-ten settings remain
  described only as historical/separate configuration where applicable.
- [PASS] Capture is documented as immediate durable raw evidence; semantic
  processing is asynchronous and live latency is disclosed.
- [PASS] Attention is described as open/unresolved active state; completed and
  cancelled lifecycle records do not remain active by default.
- [PASS] Memory, provenance, language invariance, unknown values, correction,
  temporal meaning, deterministic aggregation, and bounded Ask context are
  disclosed without claiming universal language or OCR quality.
- [PASS] Undo is described accurately as explicit permanent forget for the
  selected Product V2 capture and source-linked state, without rewriting
  unrelated evidence.
- [PASS] The local single-user/trusted-LAN limitations and absence of public
  remote security are visible.

## Evidence and trajectories

- [PASS] Frozen V1 development benchmark: one public `200`-event scenario with
  checkpoints at `50`, `100`, `150`, and `200`.
- [PASS] Official stateless `baseline-v1`: LQA-0M
  `0.30149145529538973`, DSCR `277`.
- [PASS] Kept Experiment 005 V1 reference: LQA-0M
  `0.8695006212469447`, DSCR `40`, with zero provider calls in the recorded
  replay.
- [PASS] Post-freeze V1R1 is labeled as three fresh synthetic worlds and a
  shadow/generalization result, not an official holdout or significance claim.
- [PASS] Final H2H-001 is sealed at the frozen Product V2 commit with four new
  synthetic worlds, 80 captures, 13 queries, Prompt-to-Truth Score (PTS)
  scoring, and separate
  Attention metrics; raw-memory PTS is `0.8575`, Product V2 PTS is `0.7928`,
  and Product V2 Attention F1 is `0.6795` versus `0.5641`. It is explicitly
  descriptive post-freeze evidence, not V1 scoring, holdout ground truth, or
  E006 optimization.
- [PASS] Product V2 development acceptance remains labeled separately:
  application `216/216`, evaluator `10/10`, acceptance harness `7/7`, root
  suite `233/233`, integrated acceptance `50/50`, and quality gates `7/7`.
- [PASS] [`TRAJECTORY_INDEX.md`](../TRAJECTORY_INDEX.md) inventories `52`
  coding and `55` runtime trajectories, including the final live UX,
  relative-day correctness, and sealed H2H evidence.
- [PASS] The advisory ChatGPT role is documented in
  [`docs/process/CHATGPT_DECISION_LOG.md`](process/CHATGPT_DECISION_LOG.md),
  with [`docs/process/CHATGPT_TRANSCRIPT_NOTE.md`](process/CHATGPT_TRANSCRIPT_NOTE.md)
  explicitly declining to fabricate a transcript.
- [PASS] `IMPROVEMENT_CHANGELOG.md` contains the final live UX hotfix and
  H2H evidence; both are explicitly labeled post-freeze product evidence, not
  benchmark experiments.
- [PASS] `docs/DECISIONS.md` contains the durable D-051 current-question-first,
  occurrence-safe, and UI-boundary decision plus D-052 capture-local
  relative-day semantics; historical decisions remain authentic.

## Deterministic validation

- [PASS] `python3 -m unittest discover -s app/tests -p "test_*.py" -q` —
  `216/216`, including the focused live-UX, timezone, and relative-day
  regressions.
- [PASS] `python3 -m unittest discover -s eval/tests -q` — `10/10`.
- [PASS] `python3 -m unittest product_acceptance.harness.test_harness -q` —
  `7/7`.
- [PASS] `python3 -m unittest discover -s . -p "test_*.py" -q` — `233/233`.
- [PASS] `python3 scripts/run_product_v2_integrated_acceptance.py` — `50/50`
  PASS, no live provider; the generated result is
  `eval/results/product-v2-integrated-acceptance.json`.
- [PASS] `python3 -m compileall -q app eval product_acceptance scripts`.
- [PASS] `node --check app/web/app.js`.
- [PASS] `python3 benchmark/dev/generate_benchmark.py --check` — `200` events,
  `4` checkpoints.
- [PASS] `python3 eval/contract_smoke.py` — non-scored contract smoke passed.
- [PASS] `python3 scripts/qualification_check.py --inventory` — zero hard
  failures; `52` coding and `55` runtime trajectories indexed, with all
  coding trajectories documented and four known historical non-blocking
  warnings.
- [PASS] `git diff --check`.

## Qualification warnings retained intentionally

The qualification checker reports four understood non-blocking warnings:

- one authentic developer-specific absolute path in the historical
  `docs/audits/FROZEN_RUNTIME_AUDIT.md`;
- `eval/results/final-advanced-candidate.json`, a preserved historical named
  candidate that predates the kept E005 reference;
- `eval/results/final-advanced.json`, a preserved E002 result; and
- `eval/results/final-comparison-v1.json`, a preserved E002 comparison.

These artifacts are not used as current claims, are not silently rewritten,
and are called out so a judge can distinguish historical evidence from the
current E005/V1R1 narrative. No obvious committed credential was detected.

## Git finalization

- [PASS] The existing annotated `product-v2-submission` tag was preserved at
  tag object `1940c4c8537603981c26e51ba23f6ef6b3977bf2`, peeling to its
  historical target `e7341066fd00e6209b8b51b4087ea75c1609fc3a`.
- [PASS] The previous annotated `product-v2-submission-final` tag was preserved
  at tag object `07f0fcfb73785756dc509040a3b925aa6e46d445`, peeling to the
  clean pre-hotfix base `bcf43aed7870c69f0a2501f744641b5fda5778a7`.
- [PASS] The authorized live UX hotfix is committed directly on `master` as
  implementation/evidence commit
  `93e497abf10be08bc7186fa97f071c6d20c3a9aa`, followed by the trajectory and
  evidence handoff commit
  `36315bd10e2d2ffdae8836b9183cc430f8c1b176`.
- [PASS] The historical `product-v2-submission-release` tag remains at its
  existing peeled commit `ec7665a98082d0f343d0d8e587c5db7eea185fd0`; this
  handoff does not move it or any frozen tag.
- [PASS] The final documentation/evidence package is pushed on `master` as
  `191f0390d049e6a8003254800eff2c25dc947152`; the closing trajectory metadata
  commit is documentation-only and is checked separately below.
- [PASS] Remote preflight exposed only `master`; no temporary branch cleanup
  was necessary or safe to infer.
- [PASS] The final exact local and remote `master` SHA are verified together in
  the closing handoff. Historical submission tags are preserved and are not
  moved.

## External submission items

- [NOT VERIFIED IN REPOSITORY] A final narrated video, its unauthenticated URL,
  and HackerEarth form entry are external actions and cannot be verified from
  this checkout.
- [PASS] The repository package is ready for a judge to clone, understand,
  run, and inspect using the documented local deterministic path, subject to
  the local Codex CLI requirement for live semantic processing.
