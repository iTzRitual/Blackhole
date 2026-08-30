# Product V2 integration record

Status: integrated Product V2 Host/PWA and dogfood acceptance evidence on the
isolated `product/v2-integration` branch. This is post-evaluation product work;
it does not reopen the frozen V1 benchmark or runtime.

Final coherent integration commit: `43426e8`.

## Scope and sources

The integration worktree was created from the frozen base
`68b7b15d353b12cffb65a770f8583aa0ebb849dd}` and merged the three authorized
source branches with normal merge commits:

| Source | Commit | Integration merge |
| --- | --- | --- |
| `product/v2-runtime` | `cbf706b6497ae22e1c964b991a6ca1ec6a4307c9` | `5e2dfda` |
| `product/v2-ui` | `35854aad409a964057572ffcfa8667e1af287325` | `0326600` |
| `product/v2-dogfood` | `ef63200854b1480a0c102c14f5f3a6aec9f09ab2` | `2ff1156` |

The source worktrees and the frozen base remained clean and unchanged. No
benchmark holdout material or evaluator-owned expected output was inspected.

## Reconciled product contract

The PWA now uses the real V2 Host routes through `app/web_app.py` and
`app/web/app.js`:

- `POST /api/v2/capture` accepts text-only, attachment-only, and combined
  captures. Browser attachments are sent as bounded `data_base64` bytes with
  filename and MIME metadata, preserving the exact source bytes.
- `GET /api/v2/state` and `GET /api/v2/processing` are read-only; they expose
  current Memory/Attention and processing status without starting provider
  work.
- `POST /api/v2/process` and `POST /api/v2/retry` make deferred work explicit
  and retryable. The normal Host worker can process asynchronously after the
  immediate save response.
- `POST /api/v2/ask` provides deterministic retrieval and bounded synthesis;
  `POST /api/v2/retract` implements auditable semantic Undo; and
  `GET /api/v2/attachments/<sha256>` serves verified immutable blobs.

The integration also reconciles duplicate/idempotent capture behavior, pending
and failed processing feedback, chronological retry, restart recovery,
Attention lifecycle status, relative due-time computation, open-world Memory,
deterministic arithmetic and change answers, explicit uncertainty, and source
references. V1-compatible routes remain available on the server for historical
compatibility, but the current PWA does not use them.

## Acceptance evidence

The reproducible visible acceptance run is recorded in
[product-v2-integrated-acceptance.json](../eval/results/product-v2-integrated-acceptance.json).
It covers 50 public English/Polish product cases and reports:

- `50/50 PASS`, with zero `PARTIAL`, `FAIL`, or `NOT TESTED` cases;
- all durable-save, duplicate-submit, provider-failure/retry, restart, and
  attachment-integrity quality gates passing;
- the normal-worker latency probe returning capture in `110.706 ms` while
  processing completed in `239.226 ms` with a `120 ms` provider delay; and
- provider work already visible at capture return in the latency probe, while
  the response still returned before processing finished.

The runner uses a deterministic in-process fixture provider and a fresh
temporary V2 Home per case. It is product acceptance evidence, not benchmark
ground truth and not a generalization claim. No live provider credentials or
provider tokens were used.

## Language-invariant memory and Ask

Product V2 treats language as presentation rather than as the identity of a
memory. Semantic extraction should emit a stable entity key and a
language-neutral concept, while retaining the source-language label and raw
evidence for display and provenance. A capture in one language must remain
retrievable from an Ask question in another language; dates, money, names,
Unicode, and uncertainty remain structured evidence rather than translated
substitutes.

The deterministic Ask planner is only an optional fast path. Unknown or
mixed-language questions are kept on the generic path and receive a bounded
structured candidate set for provider-directed semantic selection. The answer
provider is told to use the language of the current question and to select
explicit IDs for only the bounded evidence items that support the answer. The
runtime validates those IDs and derives the public source references from the
selected items. The language matrix and live smoke are separate post-freeze
product evidence; they do not modify the frozen V1 benchmark, baseline,
evaluator, or holdout boundary.

## Ask provenance precision follow-up

The separately authorized provenance follow-up starts from source commit
`f56dd4908aced1683993e0a32a45bf5fef1c65f6` on the isolated
`product/v2-provenance-fix` branch. The observed failure was at the Ask
projection boundary: unknown or mixed-language retrieval correctly produced a
bounded candidate pool, but the old path unioned provider `source_refs` with
all source references present in that pool. A semantically correct answer
could therefore expose unrelated, valid candidate citations.

The repaired flow is `retrieve broadly -> tag candidates -> provider selects
evidence_ids -> validate exact context -> derive source_refs narrowly -> strip
internal IDs`. The strict shared provider schema requires `evidence_ids` and
the answer prompt forbids invented IDs and broad source lists. Deterministic
cost/date/Attention/history/change paths remain authoritative and derive
provenance from what they render. Selected history/correction/conflict items
can preserve multiple material sources; invalid-only provider selections fail
closed without fabricated provenance. Raw captures and derived store schemas
are unchanged.

The dedicated provenance suite contains 11 regression cases covering bounded
candidate separation, cross-language and mixed-language over-citation,
current/history and correction semantics, contradiction uncertainty,
unsupported/entity/Attention retrieval, and invalid provider IDs. Focused
coverage increased from 26 passing tests before the change to 43 after it; the
full application suite passes 137/137. The visible integrated acceptance run
passes 50/50 and is preserved as
[product-v2-provenance-fix.json](../eval/results/product-v2-provenance-fix.json);
the prior integrated result file was not overwritten.

The authorized live smoke processed all four prescribed captures on attempt 1
with zero retries. All four Ask responses returned only the relevant capture
reference and no unrelated references. Three answers were semantically
correct; the meeting answer cited only its material capture but conservatively
reported the time as unclear, so live semantic correctness is `3/4` and the
overall live gate remains `PARTIAL` pending a separately authorized provider
extraction validation. No live retry or wording change was made.

## Validation and visual review

The final validation commands and results are:

```text
python -m unittest discover -s app/tests -v       # 137 passed
python -m unittest discover -s eval/tests -v      # 10 passed
python -m unittest product_acceptance.harness.test_harness -v  # 7 passed
node --check app/web/app.js
python -m compileall -q app eval product_acceptance scripts
python scripts/run_product_v2_integrated_acceptance.py  # 50/50 passed
```

The PWA was inspected in the local Host at `390x844` and `1280x900`, including
Capture, Attention, Memory, Ask, the attachment affordance, Enter submission,
feedback/retry, and the `+1 off your mind` plus Undo affordance. The fixture
mode used for the view checks is UI-only and contains no benchmark or holdout
data. This was a technical visual review, not a human usability study.

## Boundary review and decision

The implementation preserves immutable raw `source_events`, content-addressed
attachment bytes, rebuildable derived projections, known/inferred/unknown
semantics, deterministic date/arithmetic paths, provenance, and approval-gated
consequential actions. It does not add production infrastructure, remote
access, a Claude adapter, OCR, token handling, holdout material, or a new
benchmark-optimization experiment. Existing V1 artifacts and official results
remain unchanged.

Known limitations are deliberate: the acceptance runner explicitly drains the
processing endpoint to make semantic cases deterministic, while asynchronous
behavior is separately measured; the fixture provider is not a live-provider
smoke test; and no human usability study was performed.

Decision: **KEEP** the integrated Product V2 contract and implementation for
the explicitly authorized post-freeze product scope.

## Product V2 semantic-truth follow-up

The authorized `product/v2-semantic-truth` follow-up extends the integrated
contract without reopening the frozen V1 benchmark. Raw evidence remains
immutable; derived truth may change and is rebuildable. A correction is not a
deletion, and an ordinary change is not automatically a correction. The
projector keeps current and historical evidence separate, applies only
targeted semantic supersession, preserves duplicate support, and leaves
unresolved contradictions as unknown/conflicting rather than choosing the
last capture.

Facts now preserve first-class uncertainty, confidence, claim type,
attribution, negation, semantic relation, and structured temporal meaning.
Reported claims retain who made the claim. A newer uncertain statement does
not automatically replace a confirmed value; a later known observation may
resolve earlier uncertainty. Effective/valid time selects the appropriate
state version without treating a future meeting occurrence as an inactive
fact. Relative dates are normalized from the capture's timestamp and timezone,
not from a later retry wall clock. Coarse expressions remain coarse.

Attention uses a stable lifecycle key and related-event links so reschedules,
corrections, cancellations, and completions remove stale active occurrences.
Historical events, document clauses, possibilities, and non-actionable
mentions do not become urgent items. Ask renders current, historical,
uncertain, conflicting, attributed, and negated states distinctly while
retaining the existing candidate-versus-supporting-evidence boundary.

The semantic provider remains the language-neutral interpretation boundary.
Structured weekday/time output is normalized deterministically, and no
language-specific correction rule or exact mixed-language phrase rule is used.
The dedicated sequence suite and live-validation record are the evidence for
this follow-up; they are product generalization evidence, not benchmark,
holdout, baseline, or E006 optimization evidence.
