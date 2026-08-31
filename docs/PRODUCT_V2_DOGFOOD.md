# Product V2 dogfood acceptance gate

## Purpose

This is the independent acceptance system for Product V2. It tests whether a
normal person can capture messy ordinary-life information with almost no
organization, find it later, understand changes and uncertainty, and recover
from mistakes without losing evidence.

It is deliberately separate from the frozen V1 benchmark, V1 LQA, baseline
prompt work, and any unseen generalization claim. The 50 cases are visible
development acceptance tests. They are not a hidden oracle and must not be
presented as holdout evidence.

## Scope and boundaries

The acceptance system lives under `product_acceptance/` and uses only a public
black-box Host contract. It does not import application internals or modify
`app/**`. The current required base exposes only part of the logical V2
surface, so absent semantic endpoints are reported as `NOT TESTED` rather than
simulated as product success.

The suite preserves the project boundaries:

- captures and attachments are expected to remain immutable source evidence;
- derived state, current/history answers, and Attention are judged by what a
  user can observe;
- unknown, ambiguous, and uncertain information must stay explicit;
- consequential actions are never performed by the harness;
- CI uses a deterministic mock and does not call a live provider;
- evaluator-owned holdout material and V1 expected answers are not used.

## Corpus and coverage

The corpus contains 50 cases in five collections:

| Collection | Focus |
| --- | --- |
| `01-capture-and-attention.json` | Text capture, rapid saves, duplicate submit, relative/explicit time, false-positive Attention |
| `02-memory-and-changes.json` | Locations, preferences, people, price changes, corrections, contradictions, uncertainty |
| `03-open-world-life.json` | Recipes, Wi-Fi, gifts, shoe size, conversation, documents, pets, travel, maintenance, observations |
| `04-attachments-and-reliability.json` | Image/PDF/unsupported/duplicate attachments, provider failure, retry, restart, repeated processing |
| `05-ask-undo-and-time.json` | Current/history/list/cross-entity/no-evidence/ambiguous Ask, Undo, today/tomorrow, overdue/completed/cancelled |

Required Attention distinctions are explicit:

- should trigger: `Taxi za 10 minut.`, `Odbieram dzieci o 16:30.`, and the
  parking renewal deadline;
- should not automatically become urgent: a brother's flight next month, a
  possible bike purchase next year, a 30-day contract notice clause, and a
  past outing remembered from last Tuesday.

Open-world cases intentionally include facts that do not belong to a tiny
predefined ontology: storage locations, car noise, recipe changes, Wi-Fi
workarounds, gift ideas, shoe size, a conversation detail, a document meaning,
pet observations, travel instructions, household maintenance, and a vague
observation.

## Product-quality gates

The dashboard reports these separately, using `PASS`, `FAIL`, `PARTIAL`, or
`NOT TESTED`:

| Gate | User-visible question |
| --- | --- |
| Capture durable without provider | Did the note get a durable saved receipt even when later understanding was unavailable? |
| Capture does not wait for semantic work | Was save feedback immediate and independent of provider processing? |
| No lost captures on failure | Does a provider failure leave a recoverable raw capture and retry path? |
| Attention time correctness | Are relative, today, tomorrow, explicit, overdue, completed, cancelled, and rescheduled states correct? |
| No false urgent Attention | Are future context and past observations kept out of automatic urgent attention? |
| Ask supported by evidence | Does an answer cite or expose supporting capture evidence? |
| No fabricated answer | Does missing, conflicting, or uncertain information stay explicit? |
| Undo/forget correctness | Does explicit Undo permanently forget the selected capture and its source-linked Product V2 state without disturbing unrelated captures? |
| Attachment integrity | Are image-only, PDF-only, text-plus-file, unsupported, and duplicate files retained or clearly rejected? |
| Restart survival | Does state survive restart without duplicate active items? |
| Human-readable contract | Can a normal person understand saved, pending, failed, uncertain, current, and historical states? |
| No debug UI dependency | Can the product be used successfully without raw benchmark assertions or developer diagnostics? |

No single score can waive a failed trust gate. The report should identify the
failed capability and the exact case/step evidence.

## Manual session

Use [`product_acceptance/manual/DOGFOOD_PROTOCOL.md`](../product_acceptance/manual/DOGFOOD_PROTOCOL.md)
for the 15–25 minute session. It covers ordinary captures, attachment-only
capture, processing, Attention, Memory, natural Ask questions, a changed fact,
Undo, and restart. Use the separate
[`TROUBLESHOOTING.md`](../product_acceptance/manual/TROUBLESHOOTING.md) only
when a technical investigation is needed.

## Automated evidence

Run the deterministic validation and mock report with:

```text
python -m unittest product_acceptance.harness.test_harness -v
python -m product_acceptance.harness.run --adapter mock --report eval/results/product-v2-dogfood-mock.json
```

The report records case count, coverage, per-step results, product-quality
gates, adapter, limitations, and the fact that no live provider was called.
The HTTP adapter can later target an integrated Host explicitly, but it does
not assume a reset/restart route or a particular database schema.

The recorded mock run at
[`eval/results/product-v2-dogfood-mock.json`](../eval/results/product-v2-dogfood-mock.json)
contains 50 cases: 2 `PASS`, 48 `PARTIAL`, and 0 `FAIL`. All seven deterministic
mock quality gates are `PASS`. The `PARTIAL` cases are expected because the
mock intentionally exposes transport/reliability behavior but not semantic
Ask, Attention, or Memory behavior.

## Acceptance status at this base

The deterministic corpus/fixture/loader/harness path is the acceptance-system
foundation. The mock is expected to be `PARTIAL` for semantic surfaces because
it is a transport and reliability stub. A complete Product V2 gate requires a
separately recorded HTTP or manual run against the integrated Host, with no
unseen-evidence claim made from these visible cases.

Known limitations are intentional and must remain visible:

- no live provider calls are made by CI;
- the current base does not expose all V2 semantic/Undo/attachment routes;
- the HTTP adapter cannot isolate, reset, or restart a target process;
- the corpus is not holdout material and must not be used to tune a prompt or
  claim generalization.
