# Blackhole submission checklist

Status: local repository gate PASS; the exact remote/tag identifiers are
verified in the final handoff for the immutable submission commit. This is a
factual repository gate, not an aspirational feature backlog.

## Scope and authority

- [PASS] Work is being finalized directly on `master`.
- [PASS] Starting `master` and `origin/master` were the exact expected clean
  SHA: `e7341066fd00e6209b8b51b4087ea75c1609fc3a`.
- [PASS] Product V2 runtime changes were limited to cross-platform local
  timezone discovery; explicit timezone precedence and capture-time temporal
  semantics remain unchanged. The one unrelated macOS path correction is
  test-only and canonicalizes an already-resolved database path.
- [PASS] No provider inference, V1 oracle access, holdout inspection, prompt
  tuning, benchmark optimization, or evaluator-ground-truth change occurred.
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
- [PASS] `docs/assets/product-v2-capture-desktop.png` and
  `docs/assets/product-v2-ask-mobile.png` are synthetic copies of the final UI
  review; no private human dogfood data is published.
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
- [PASS] Product V2 development acceptance remains labeled separately:
  application `192/192`, evaluator `10/10`, acceptance harness `7/7`,
  integrated acceptance `50/50`, and quality gates `7/7`.
- [PASS] [`TRAJECTORY_INDEX.md`](../TRAJECTORY_INDEX.md) inventories `46`
  coding and `51` runtime trajectories, including the finalization and Mac
  portability-hotfix trajectories.
- [PASS] The advisory ChatGPT role is documented in
  [`docs/process/CHATGPT_DECISION_LOG.md`](process/CHATGPT_DECISION_LOG.md),
  with [`docs/process/CHATGPT_TRANSCRIPT_NOTE.md`](process/CHATGPT_TRANSCRIPT_NOTE.md)
  explicitly declining to fabricate a transcript.
- [PASS] `IMPROVEMENT_CHANGELOG.md` was not altered: this is submission
  preparation, not a benchmark or product experiment.
- [PASS] `docs/DECISIONS.md` was not rewritten: historical decisions remain
  authentic, while current submission-facing contract text is explicit.

## Deterministic validation

- [PASS] `python -m unittest discover -s app/tests -p "test_*.py" -v` —
  `192/192` on macOS, including the focused timezone regressions.
- [PASS] `python -m unittest discover -s eval/tests -v` — `10/10`.
- [PASS] `python -m unittest product_acceptance.harness.test_harness -v` —
  `7/7`.
- [PASS] `python -m unittest discover -s . -p "test_*.py" -v` — `209/209`.
- [PASS] `python scripts/run_product_v2_integrated_acceptance.py` — `50/50`
  PASS, no live provider; the generated result is
  `eval/results/product-v2-integrated-acceptance.json`.
- [PASS] `python -m compileall -q app eval product_acceptance scripts`.
- [PASS] `node --check app/web/app.js`.
- [PASS] `python benchmark/dev/generate_benchmark.py --check` — `200` events,
  `4` checkpoints.
- [PASS] `python eval/contract_smoke.py` — non-scored contract smoke passed.
- [PASS] `python scripts/qualification_check.py --inventory` — zero hard
  failures; `46` coding and `51` runtime trajectories documented.
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

- [PASS] The existing annotated `product-v2-submission` tag was preserved and
  still dereferences to the pre-Mac snapshot
  `e7341066fd00e6209b8b51b4087ea75c1609fc3a`.
- [PASS] The timezone portability hotfix was committed directly on `master` as
  `8eb8158c9177114ff66122f98c5bfef1ccd0aeb4`.
- [PASS] The authoritative final tag is the new
  `product-v2-submission-final`; it must point to the final pushed `master`.
- [PASS] The local tree was clean after the hotfix commit before final
  submission-documentation finalization.
- [PASS] Remote preflight exposed only `master`; no temporary branch cleanup
  was necessary or safe to infer.
- [PASS] The final exact local SHA, remote SHA, and
  `product-v2-submission-final` tag target are verified together in the final
  handoff; the tag is the immutable pointer for the submitted tree. The old
  `product-v2-submission` tag is historical and is not moved.

## External submission items

- [NOT VERIFIED IN REPOSITORY] A final narrated video, its unauthenticated URL,
  and HackerEarth form entry are external actions and cannot be verified from
  this checkout.
- [PASS] The repository package is ready for a judge to clone, understand,
  run, and inspect using the documented local deterministic path, subject to
  the local Codex CLI requirement for live semantic processing.
