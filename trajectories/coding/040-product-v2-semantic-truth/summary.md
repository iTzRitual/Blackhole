# Product V2 semantic truth

## Goal

Implement and verify the explicitly authorized Product V2 semantic-truth
generalization in the isolated `product/v2-semantic-truth` worktree. Preserve
the exact source/base boundary, immutable raw evidence, rebuildability,
unknown/uncertain semantics, provenance, the frozen V1 benchmark and baseline,
and the holdout boundary.

Source/base: `product/v2-provenance-fix` at
`7a76a1b660b49d28cb5aa29ab9e9b5099238aaee`.

## Agent/tool used

Codex desktop agent using PowerShell, `apply_patch`, local Python/Node
validation commands, the existing Product V2 test/acceptance runners, and the
authorized local subscription-first Codex CLI through the normal application
worker. No provider token was read, copied, exported, or persisted.

## Initial hypothesis

A strict semantic extraction contract plus a deterministic evidence-led
projection can preserve raw history while distinguishing targeted corrections,
ordinary changes, future effective values, uncertainty, attribution,
negation, contradiction, temporal occurrence, and Attention lifecycle. These
semantics should remain rebuildable and should not depend on last-write-wins,
localized capability tables, or exact live-smoke wording.

## Important implementation decisions

- Versioned Product V2 runtime, prompt, store, projection, and extractor
  contracts for the semantic-truth slice.
- Kept raw source events immutable and added persisted semantic metadata for
  certainty, claim type, confidence, attribution, negation, relation, and
  structured temporal meaning.
- Projected current truth by entity/concept using only targeted semantic
  supersession and explicit effective/valid times. Preserved duplicate
  support, ordinary history, unresolved contradictions, and retracted source
  history.
- Normalized relative and structured temporal values deterministically from
  the capture timestamp and timezone. Preserved coarse intervals rather than
  inventing points. Nullable strict-schema fields are treated as absent when a
  deterministic point or interval can be computed.
- Used stable Attention lifecycle keys and related-event links for
  correction, reschedule, completion, and cancellation.
- Kept the semantic provider as the language-neutral interpretation boundary;
  the fast path has no per-language semantic capability table or exact
  phrase-specific live repair. Multi-unknown money questions are handed to
  semantic synthesis while numeric/currency tokens remain searchable.
- Kept Ask candidate context separate from validated supporting evidence and
  rendered temporal details in change answers.

## Tools/actions used

- Read the referenced pasted task before work and preserved its initiating
  instruction verbatim in `prompt.md`.
- Verified the exact source worktree, source branch/SHA, target worktree, and
  target branch before implementation. Worked only in the target worktree.
- Added the semantic sequence suite, non-scored semantic result runner, and
  UTF-8 file-backed live validation runner.
- Updated the Product V2 implementation, prompt, architecture/spec/decision
  documentation, changelog, and machine-readable evaluation results.
- Ran the authorized live sequence through normal `create_server` lifecycle
  with `auto_start_product_worker=true`; did not call the manual processing
  endpoint.

## Failures, retries, and changed approaches

- The first inline live runner completed structurally but its console display
  rendered Unicode as replacement glyphs; it was not used as authoritative
  evidence. A file-backed UTF-8 runner was added.
- The file-backed runner initially failed twice before capture because its
  `app` import path was initialized after importing the application module.
  The runner-only bootstrap was moved before the import; no captures or
  provider calls occurred in those failed launches.
- The first post-change integrated acceptance rerun was `49/50` because a
  new lexical-gap branch treated a currency question as semantic synthesis.
  Numeric/currency tokens were excluded from gap detection; the final rerun
  returned `50/50 PASS`.
- The authoritative live run was capped at 10 captures and 8 asks as
  authorized. No second live run was started after final offline refinements.

## Human feedback or checkpoints

The user-authorized task supplied the exact source/base SHA, isolated target
branch, post-freeze scope, live limits, normal lifecycle requirement, and
prohibitions on V1/holdout access and benchmark changes. No additional human
feedback or checkpoint was received during implementation.

## Evaluation performed

- Dedicated semantic matrix: `64` cases, `38` multi-capture cases, `8` test
  methods, `0` failures, `0` errors; result in
  `eval/results/product-v2-semantic-truth.json`.
- Full repository suite: `163/163` passed in `24.592s` on the final run.
- Evaluator tests: `10/10`; acceptance harness: `7/7`.
- Integrated acceptance: final `50/50 PASS`; first exploratory rerun was
  `49/50` and is described above, with the final result saved in
  `eval/results/product-v2-integrated-acceptance.json`.
- Contract smoke: correct candidate schema-valid with `semantic_score=1.0`
  and `6` true positives; malformed candidate rejected; non-scored result in
  `eval/results/contract-smoke.json`.
- Compilation/syntax: `compileall` and `node --check app/web/app.js` passed.
- Frozen benchmark structure: `200` events and `4` checkpoints checked.
- Authoritative live smoke in `live-validation.json`: `10/10` captures saved,
  all processed on attempt 1, `0` retries, `8/8` Ask HTTP 200/ready responses,
  health HTTP 200, and a second Attention inspection with exactly two
  lifecycle-current items. Current/history keys, uncertainty, contradiction,
  mixed-language temporal structure, German semantic retrieval, and precise
  source references were exercised. The Polish price-history ask returned only
  the observed `9 EUR` item, and the meeting-change ask exposed operations but
  not both before/after times; those are recorded as live semantic/presentation
  limitations. The file also records that final offline-only refinements came
  after the authoritative live run, so the cap was not exceeded.

No benchmark oracle, holdout material, G01/G02/G03, baseline prompt, or
production infrastructure was accessed or changed.

## Result

Offline semantic truth, application regression, evaluator, acceptance,
contract, and structural gates pass. The authorized live run is structurally
healthy but the overall semantic live gate is `PARTIAL` because two user-facing
change/history answers were incomplete and the run could not be repeated after
offline-only fixes.

## Regressions or unresolved issues

- Live provider extraction and synthesis quality is not universal: the
  price-history and meeting-change answers need a separately authorized live
  validation if they become a release requirement.
- The live run observed a null fact-level temporal `normalized` field from the
  strict nullable schema; deterministic offline normalization was fixed and
  covered by tests after that run.
- No human usability study was performed. No scored benchmark metric was
  changed or claimed.

## Final decision

`KEEP` the implementation and evidence-led projection for the explicitly
authorized post-freeze Product V2 product scope. Record the overall live gate
as `PARTIAL`; do not reopen the frozen benchmark or infer holdout performance.

## Related git commit

To be filled with the coherent commit created for this task after final
validation.
