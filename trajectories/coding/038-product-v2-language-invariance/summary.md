# Product V2 language invariance — coding trajectory

## Goal

Implement and validate language-invariant Product V2 memory and Ask behavior
from the exact authorized base in the isolated worktree, while preserving raw
evidence, existing deterministic behavior, and all benchmark boundaries.

## Agent/tool used

Codex in the shared workspace, using PowerShell, `apply_patch`, Python's
standard-library unittest/compile checks, and the repository's existing
validation scripts. No provider credentials are requested, read, copied, or
persisted.

## Initial hypothesis

The observed failure is structural rather than a missing translation: the
planner's finite lexical routing vocabulary prevents an unfamiliar-language
question from reaching a general semantic path, and language-specific answer
branches make presentation inconsistent. A bounded structured-memory fallback
plus provider-directed response-language behavior should preserve existing
high-confidence deterministic paths while allowing unlisted languages to be
handled semantically.

## Architecture audit before implementation

| Area | Existing dependency | Classification | Planned treatment |
| --- | --- | --- | --- |
| Raw capture storage | Stores original text/payload JSON and immutable source rows | A — presentation/provenance | Preserve exactly |
| Semantic extraction | Provider prompt is open-world and receives UTF-8 capture text | A — provider interpretation | Make language-neutral meaning fields explicit |
| Derived entities/facts | Entity keys are slugs of provider-selected labels; concepts and values are structured | B — deterministic normalization | Preserve labels and add bounded semantic retrieval metadata |
| Ask tokenization | Unicode whole-word tokenization and accent folding | B — fast-path optimization | Keep as optional lexical ranking |
| Ask aliases/stop words | Finite English/Polish stop words, aliases, and phrase patterns | C — capability-critical coupling when used as the only route | Remove capability dependence; keep only bounded fast paths where safe |
| Ask language detection | Existing Polish signal or English default | C — presentation coupling | Replace with provider-directed response language metadata/fallback |
| Retrieval | Token overlap over current facts/history/relations; empty overlap becomes `no_match` | C — capability-critical coupling | Add bounded structured candidate context for general semantic fallback |
| Deterministic answer text | Mostly English, one Polish ambiguity string | C — presentation coupling | Route wording through language-aware renderer with safe fallback |
| Dates/money/numbers | Deterministic normalization and Decimal aggregation | A — invariant calculation | Preserve and regression-test |
| Evidence | Source refs are attached to normalized facts and returned Ask items | A — provenance | Preserve original source and refs |

## Baseline observation

At the authorized base, the existing 37-case Product V2 Ask routing corpus and
the prior Product V2 test suite are the regression comparators. The new
cross-language matrix and live smoke are not present at baseline. The concrete
repro is that an unfamiliar-language question with no lexical overlap can
produce `no_match` without invoking the semantic provider, even when bounded
structured memory exists.

## Important implementation decisions

- Kept the finite Ask vocabulary as an optional fast path rather than a
  capability gate. Added a conservative `unknown` presentation hint and a
  `lexical_gap` marker; unknown and mixed-language plans stay generic and
  require the semantic path.
- Made Unicode identifier separators searchable as word boundaries so a
  provider key such as `basement_keys` can match ordinary words without
  adding a language-specific translation table.
- Added bounded semantic fallback candidates from structured current facts,
  history, relations, and Attention. The fallback is capped at 40 facts and
  20 entries for each other collection and never includes raw capture
  payloads.
- Updated the Product V2 prompt to request reusable language-neutral entity
  keys and concepts while preserving source labels and evidence. Updated the
  answer prompt to use the current Ask language and the smallest directly
  supporting source-reference set.
- Preserved deterministic arithmetic/date/Attention/cost/change behavior and
  added localized English/Polish fast-path copy. Unknown-language rendering is
  provider-directed rather than guessed locally.
- Allowed a unique one-term entity winner only when the question has a real
  lexical gap. Fully recognized queries retain strict ambiguity and
  retraction/no-match behavior after an initial over-broad relaxation exposed
  a garage-key false positive.
- Versioned the Product V2 prompt and extractor contract (`v3` prompt,
  `v2` extractor) so the semantic representation change is auditable.

## Tools/actions used

- Read the user-referenced pasted task file before any other task work.
- Audited the target-base Product V2 specification, architecture, decision
  log, runtime prompt, Ask planner, runtime/store, existing tests, and
  acceptance contract without opening protected V1 oracle/scoring material.
- Created the exact isolated worktree and branch from the requested commit.
- Used `apply_patch` for the implementation, tests, prompt, documentation,
  trajectory, and machine-readable evidence files.
- Used Git boundary/status/diff checks and Python unittest, compile, benchmark
  structure, contract smoke, qualification, JavaScript syntax, and Product V2
  acceptance commands.
- Ran one authorized fresh-temporary-home live smoke with the normal worker,
  six captures, and eight Ask queries. The CLI owned authentication; no
  credential value was read, copied, exported, or persisted.

## Failures encountered

- The initial dedicated matrix exposed cross-language one-term retrieval
  gaps, missing fixture answers for owner/document cases, and a mixed-language
  temporal case that needed the general semantic path. These were corrected
  in the general planner/retrieval/test fixture contract, not with live
  phrase-specific branches.
- The first unique-entity relaxation regressed an existing retraction test by
  returning a remaining garage-key fact for a withdrawn basement-key query.
  The relaxation was guarded by `lexical_gap`; the retraction/no-match test
  then passed.
- One combined focused run hit the existing 0.5-second capture-return test
  threshold at 1.125 seconds under local Windows/OneDrive load and left its
  intentionally blocked test provider holding a temporary SQLite file during
  cleanup. The complete application suite subsequently passed 126/126,
  including that test; no source workaround was added.
- The integrated acceptance runner regenerated its historical result file.
  That accidental overwrite was discarded and the tracked historical report
  was preserved; this task's result is separate.
- The live smoke's mixed-language answer was correct about the missing exact
  date and returned valid event IDs, but cited all six bounded candidate
  sources. The answer instruction and result seeding were tightened after
  the smoke. No further live Ask was issued, so the live gate remains
  `PARTIAL`.

## Retries or changed approaches

- Replaced the first unrestricted unique-best retrieval relaxation with the
  `lexical_gap`-guarded version after the retraction regression.
- Kept the final fallback provider-directed for unknown/mixed questions and
  made provider failure safe (`no_match`) when no selected evidence exists,
  rather than rendering the entire candidate set as an answer.
- Preserved the historical integrated acceptance JSON after its validation
  rerun and recorded the fresh language-invariance evidence in a new result.

## Human feedback or checkpoints

The user-authorized task specification is the governing checkpoint. No further
human checkpoint has been supplied.

## Evaluation performed

- Pre-change focused Product V2 comparator: 27 tests passed. The concrete
  Spanish basement-key reproduction was `no_match` with zero Ask-provider
  calls despite matching structured memory.
- Dedicated language-invariance matrix: 54/54 cases passed; 30 used the
  provider-directed semantic fixture and 24 used deterministic fast paths.
  All 54 preserved expected source references and answer-language metadata.
  Unknown-language candidate context measured 12 facts, 14 history entries,
  0 relations, and 3 Attention entries, within the declared limits, with no
  raw payload or raw capture text.
- Full application suite: 126 passed. Evaluator suite: 10 passed. Product
  acceptance harness: 7 passed. Integrated visible acceptance: 50/50 PASS.
  Benchmark structure: 200 events and 4 checkpoints. Non-scored contract
  smoke: semantic score 1.0 for the correct fixture and malformed fixture
  detected. Compileall, JavaScript syntax, and qualification passed;
  qualification reported the repository's four existing warnings.
- Authorized live smoke: 6/6 captures saved and processed on attempt 1; 8/8
  Ask calls returned ready results; 5 Ask provider calls and 2 capture
  provider calls were observed. Polish, English, Spanish, German, French,
  mixed-language, and Japanese requests returned language-appropriate output
  metadata and valid evidence. One mixed-language result over-cited the
  bounded candidate set, so the live gate is `PARTIAL`.
- Machine-readable evidence: `eval/results/product-v2-language-invariance.json`.
  Live evidence: `live-validation.json` in this trajectory.

## Result

The requested language-invariant Product V2 implementation is complete in the
isolated worktree. The runtime no longer treats the existing lexical vocabulary
as the language capability boundary: unrecognized or difficult questions can
reach a bounded semantic provider context, stable semantic keys survive
capture/Ask language changes, raw evidence remains immutable, and provider
answers are instructed to follow the current question language. Offline product
and regression gates pass. The authorized live gate is useful but partial due
to the mixed-answer provenance over-citation described above.

## Regressions or unresolved issues

- No final application, evaluator, acceptance-harness, visible integrated
  acceptance, benchmark-structure, contract-smoke, or JavaScript regression
  remains.
- The live provider should be rechecked in a separately authorized,
  provenance-focused smoke after the minimal-reference prompt change. The
  current task does not authorize more live questions.
- The fallback still depends on provider semantic quality for languages outside
  the local deterministic fast paths; the implementation makes that boundary
  explicit and bounded but does not claim universal language identification or
  equal quality for every language.
- No benchmark score, baseline result, holdout material, G01/G02/G03 run, V1
  oracle/scoring worktree access, production infrastructure, or Claude adapter
  was added.

## Final decision

**KEEP** the language-neutral semantic boundary, bounded fallback, prompt
contract, and offline-tested implementation. **REVISE** the live-validation
gate only after separately authorized provenance-focused validation; do not
start a benchmark-optimization experiment or alter frozen V1 evidence.

## Related git commit

Implementation commit: `16aad12` (`generalization: make product v2 ask
language invariant`).
