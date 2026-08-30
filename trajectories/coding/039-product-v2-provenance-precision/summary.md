# Product V2 Ask provenance precision

## Goal

Implement the authorized Product V2 Ask provenance-precision fix in an
isolated worktree based exactly on the language-invariance source HEAD. Keep
bounded retrieval candidates separate from answer-supporting evidence, make
provider evidence selection explicit and validated, preserve deterministic and
language-invariant behavior, run the bounded live validation and full
regression, document the result, and commit only the new branch.

## Agent/tool used

Codex in the shared Blackhole workspace using PowerShell commands,
`apply_patch`, Python `unittest`/validation runners, Node syntax checks, and
the local authenticated Codex CLI only through the existing Product V2
subscription-first adapter. No provider token was read, copied, exported, or
persisted. No authentic transcript export was available; none was fabricated.

## Initial hypothesis

The mixed-language live over-citation was caused by the Ask response layer
unioning provider-returned references with references derived from the bounded
retrieval selection, rather than tracking provider-selected supporting
evidence separately from candidate evidence.

## Trace result before implementation

The hypothesis was confirmed. `_retrieval_context()` deliberately broadens
unknown/mixed-language queries into bounded `facts`, `history`, `relations`,
`attention`, and `sources` candidate collections. In `ask()`, the old response
path initialized `refs` from `selected_facts`, then added every provider
`source_refs` value that matched any source metadata in that candidate context
(`app/product_v2.py` old Ask path). With no lexical winner, all fallback
candidate source IDs were therefore valid and were unioned into the final
answer even when the provider rendered an answer about one fact. The provider
contract had no explicit evidence-selection field, so its `source_refs` array
was doing double duty as both answer provenance and an unchecked
candidate-source list.

## Important implementation decisions

- Tag every provider-facing bounded fact, history item, relationship, Attention
  item, and source metadata item with a stable typed internal `evidence_id`.
  Current facts use entity/concept IDs; stored history and relations use their
  IDs; Attention uses its fingerprint; source metadata uses its event ID; and
  an immutable canonical digest is the fallback.
- Extend the strict shared provider schema with bounded `evidence_ids` and
  update the Ask prompt to require the smallest materially supporting set,
  preserve multiple IDs for history/corrections/conflicts, and never invent
  IDs. Ask ignores the provider's top-level `source_refs` list.
- Validate returned IDs against the exact context supplied to the provider,
  de-duplicate and cap them, derive public `source_refs` from selected items
  only, map source metadata back to its event ID, strip internal IDs from
  public items, and fail closed when a non-empty provider selection contains
  no valid ID. Deterministic answer paths retain their existing direct
  provenance.
- Preserve the raw/derived boundary and all frozen benchmark, baseline,
  evaluator, calibration, holdout, V1, and source-worktree boundaries.

## Tools/actions used

- Read the attached goal objective before any task work; resolved source HEAD
  `f56dd4908aced1683993e0a32a45bf5fef1c65f6` and required ancestry; created
  `product/v2-provenance-fix` at
  `C:/Users/natan/OneDrive/Dokumenty/ChatGPT/Blackhole-v2-provenance-fix`.
- Read the relevant Product V2 architecture, specification, decisions,
  integration, prompt, and changelog documents before editing them.
- Added the runtime/provider contract change, migrated provider fixtures and
  the integrated acceptance fixture, added the dedicated provenance suite,
  and updated Product V2 documentation and changelog.
- Ran the authorized live smoke in one fresh temporary Home through the
  normal Host HTTP lifecycle: the four prescribed captures were saved, the
  normal worker was allowed to finish, and the four asks were issued without
  intervening data edits.
- Preserved the pre-existing
  `eval/results/product-v2-integrated-acceptance.json` artifact and saved the
  final 50-case run as `eval/results/product-v2-provenance-fix.json`.
- Verified the source worktree remained clean and unchanged.

## Failures encountered

An initial trajectory patch used an unintended duplicated `OneDrive` path.
The two created files were removed and recreated at the correct worktree
path; no source or target task file was lost.

The live smoke's fourth provider answer conservatively reported the Marek
meeting time as unclear even though the capture contained `Donnerstag 16:00`.
It still selected only `live-004` as provenance. The disposable inline
harness also emitted Windows `WinError 10038` while its server thread was
exiting after all requests completed; no request failed.

## Retries or changed approaches

The trajectory creation was retried after the path correction. A provenance
fixture query was made less lexically specific after it took the deterministic
path, so the test explicitly exercised the provider-backed mixed-language
fallback; this was done before the authorized live run and did not alter live
wording or runtime behavior. The invalid-ID test was strengthened to require a
safe no-match result rather than an uncited provider answer.

## Human feedback or checkpoints

The attached objective authorized one fresh temporary Home, at most four
captures and four asks, normal processing wait, and no edits between live
questions. That limit was respected. No further live retry was made after the
partial fourth answer.

## Evaluation performed

- Baseline focused comparator before implementation: 26 passing tests.
- Dedicated provenance suite: 11/11 passing.
- Combined Ask/language/provider/Product V2 focused suite: 43/43 passing.
- Full application suite: 137/137 passing.
- Evaluator tests: 10/10 passing.
- Product acceptance harness tests: 7/7 passing.
- Non-scored response-contract smoke: correct score `1.0`, schema valid;
  malformed control rejected as expected.
- `compileall`: PASS; `node --check app/web/app.js`: PASS;
  `node --check app/web/sw.js`: PASS.
- Public benchmark structure check: PASS, 200 events and 4 checkpoints;
  no benchmark scoring or optimization run.
- Qualification: PASS with the four pre-existing repository warnings.
- Final visible integrated acceptance: 50/50 PASS, zero partial/fail cases;
  latency probe PASS with 9.835 ms capture return, 145.667 ms processing
  completion, and a 120 ms fixture-provider delay.
- Authorized live smoke: 4/4 captures processed on attempt 1 with zero
  retries; 4/4 asks returned relevant-only source references; semantic answer
  quality was 3/4 because the meeting-time answer remained unclear.

## Result

The provenance implementation passes all offline and visible acceptance
checks. Provider-backed Ask now uses explicit validated evidence selection, so
valid but unrelated retrieval candidates cannot become final citations, and
invalid provider IDs cannot fabricate provenance. Deterministic current,
history, correction, contradiction, and Attention paths remain covered. The
live provenance precision result was 4/4 relevant-only citations, while the
overall live semantic gate is PARTIAL at 3/4.

## Regressions or unresolved issues

No application, provider-contract, HTTP/UI, evaluator, acceptance,
benchmark-structure, source-integrity, or frozen-boundary regression remains.
The installed provider's extraction/synthesis path did not recover the
meeting time in the authorized smoke; resolving that is a separate provider
extraction validation and must not be treated as provenance evidence or
addressed by unapproved wording tuning. Qualification retains four known
pre-existing warnings.

## Final decision

KEEP the provenance-precision implementation: every final citation observed
in the authorized smoke was materially tied to the rendered support, and the
offline invalid-ID guard fails closed. REVISE the overall live semantic gate
only after a separately authorized provider-extraction validation. This work
is post-freeze product generalization evidence, not E006, a benchmark result,
or a holdout claim.

## Related git commit

Implementation commit: `c73369b` (`fix: separate Product V2 Ask evidence
from candidates`). The final branch SHA is recorded in the delivery report.
