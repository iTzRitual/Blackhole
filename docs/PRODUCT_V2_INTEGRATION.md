# Product V2 integration record

Status: integrated Product V2 Host/PWA and dogfood acceptance evidence on the
isolated `product/v2-integration` branch. This is post-evaluation product work;
it does not reopen the frozen V1 benchmark or runtime.

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
[product-v2-integrated-acceptance.json](/C:/Users/natan/OneDrive/Dokumenty/ChatGPT/Blackhole-v2-integration/eval/results/product-v2-integrated-acceptance.json).
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

## Validation and visual review

The final validation commands and results are:

```text
python -m unittest discover -s app/tests -v       # 104 passed
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
