# Product V2 dogfood / acceptance suite

This directory contains the visible development acceptance system for Product
V2. It is intentionally independent of the frozen V1 benchmark and is designed
to answer a product question:

> Would a normal person trust Blackhole as an external memory after capturing
> messy ordinary-life information with almost no organization?

These cases are development acceptance tests. They are visible to the team and
must not be described as unseen generalization evidence. They are not V1 LQA,
not a replacement for the frozen benchmark, and not hidden ground truth.

## Contents

| Path | Purpose |
| --- | --- |
| `cases/*.json` | Five JSON collections containing 50 realistic single- and multi-step cases |
| `schemas/case.schema.json` | Public case format |
| `schemas/report.schema.json` | Machine-readable acceptance report shape |
| `fixtures/` | Small safe image, PDF, and unsupported-format fixtures |
| `harness/case_loader.py` | JSON parsing plus semantic validation, duplicate and fixture checks |
| `harness/adapters.py` | HTTP black-box adapter and deterministic transport/reliability mock |
| `harness/run.py` | Case runner, quality gates, coverage dashboard, and report writer |
| `harness/test_harness.py` | Provider-free validation and harness tests |
| `manual/` | Human dogfood protocol and technical troubleshooting appendix |

## Run it

The default path is deterministic and provider-free:

```text
python -m unittest product_acceptance.harness.test_harness -v
python -m product_acceptance.harness.run --adapter mock --report eval/results/product-v2-dogfood-mock.json
```

The mock checks durable-save receipts, attachment fingerprints, duplicate
submission, provider-failure/retry plumbing, restart preservation, and repeated
processing. It deliberately does not pretend to understand natural language;
Ask, Attention, and semantic Memory steps are reported as `NOT TESTED`.

To point the black-box adapter at an explicitly chosen local Host:

```text
python -m product_acceptance.harness.run --adapter http --base-url http://127.0.0.1:8080 --case-id CAP-001
```

The HTTP command is an integration/manual path. The harness itself never calls
Codex or another provider. A target Host may use its own provider while running
`/api/process`; that is why the deterministic mock is the CI path.

## Case format

Each JSON file is an array of cases. A case contains a timezone-aware
`initial_time`, an IANA `timezone`, natural-language `capture` steps, optional
attachment fixture references, and user-visible expectations. Other steps can
advance the test clock, ask a question, inspect Attention or Memory, process,
retry, restart, change the provider fixture, or undo a capture.

Expectations describe what a person can observe: saved confirmation, current
versus historical wording, evidence, uncertainty, actionable timing, absence of
false urgency, or preservation after Undo. The harness does not require a
particular database table, ontology ID, prompt, model, or internal state shape.

Example:

```json
{
  "case_id": "CAP-001",
  "title": "A taxi in ten minutes is actionable",
  "locale": "pl-PL",
  "tags": ["capture", "attention", "relative-time"],
  "initial_time": "2026-01-05T09:00:00+01:00",
  "timezone": "Europe/Warsaw",
  "user_outcome": "The taxi is visible as a near-term actionable item.",
  "steps": [
    {
      "id": "capture-taxi",
      "type": "capture",
      "at": "2026-01-05T09:00:00+01:00",
      "text": "Taxi za 10 minut.",
      "idempotency_key": "cap-001-taxi",
      "expect": {"saved": true, "processing": "pending"}
    },
    {
      "id": "check-attention",
      "type": "attention",
      "at": "2026-01-05T09:01:00+01:00",
      "expect": {"include": ["taxi"], "actionable": true, "evidence": "required"}
    }
  ]
}
```

## Logical black-box contract

The harness uses logical operations so a future Host can change transport
details in one adapter. The default HTTP mapping is:

| Operation | Default route | Minimum observable obligation |
| --- | --- | --- |
| Health | `GET /api/health` | A safe liveness/ready response |
| Capture | `POST /api/capture` | Accept text, attachment-only, or both; return a durable receipt and processing state |
| Process | `POST /api/process` | Report success or a retryable failure without losing raw capture |
| Retry | `POST /api/retry` | Reattempt failed work without duplicating active state |
| Ask | `POST /api/query` | Return a human-readable answer with supporting evidence or an explicit no-evidence/uncertainty response |
| Attention | `GET /api/attention` | Return actionable items with correct time/lifecycle status |
| Memory | `GET /api/memory` | Return useful current/history facts with evidence |
| Undo | `POST /api/undo` | Remove a selected capture from active state while retaining source history |

Capture requests use JSON with `text` (optional when an attachment is present),
`captured_at`, `idempotency_key`, `source_type`, and an optional attachment
object containing `filename`, `mime_type`, and small-fixture `content_base64`.
The response should expose a stable capture receipt and a processing status;
internal schema is intentionally unspecified.

The required base predates these full Product V2 surfaces. Its existing
`/api/capture`, `/api/process`, `/api/retry`, and `/api/query` routes can be
probed by the adapter; missing routes are reported as `NOT TESTED`, while a
reachable route that violates an expectation is reported as `FAIL`. The harness
does not edit `app/**` to make compatibility tests pass.

## Result meanings

- `PASS`: every automated check for the case passed.
- `FAIL`: at least one automated check contradicted the user-visible expectation.
- `PARTIAL`: executable checks passed, but one or more required surfaces were not exposed by the selected adapter.
- `NOT TESTED`: no executable check was available.

The report also contains separate product-quality gates. Do not collapse those
gates or the case statuses into one opaque score. A later integrated run should
publish the matrix, evidence, adapter/Host revision, and limitations.
