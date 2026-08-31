# Blackhole submission narrative

Blackhole is a zero-organization external memory: **Capture now. Understand
automatically. Find it later.** This document is the judge-facing narrative
for the frozen Product V2 submission. It keeps Product V2 product evidence
separate from the scientifically evaluated V1 evidence.

## Problem / User Value

Life information arrives as fragments: a receipt, a deadline, a location, a
preference, a contract, or a half-formed task. Most productivity tools ask the
person to classify, file, tag, or schedule the fragment before it is safely
stored. That organizational decision is often the hardest part of capture.

Blackhole gives the user one quiet inbox. A capture is saved immediately, even
when the semantic provider is unavailable. Later, asynchronous understanding
turns the evidence into current Memory, a short Attention view, and natural
questions with source grounding. The user does not need to maintain a folder
system or a predefined ontology.

The product loop is:

```text
Capture → background understanding → Attention / Memory → Ask
```

- **Capture** is a zero-friction inbox. `Saved.` means the raw capture is
  durable; it does not wait for a model.
- **Attention** contains things that still need the user: open deadlines,
  unresolved uncertainty, meaningful changes, and proposed actions.
- **Memory** is the current useful state, with history, uncertainty,
  contradictions, and provenance kept visible where they matter.
- **Ask** is natural, bounded retrieval over personal memory. Deterministic
  date, time, and arithmetic paths stay deterministic; bounded semantic
  questions can use the local Codex CLI.
- **Undo** permanently forgets the selected Product V2 capture and its
  source-linked state inside the Product V2 Home. It is an explicit user
  action, not automatic cleanup.

## Agent Solution / Engineering

Product V2 uses an already-installed, already-authenticated local Codex CLI
through a narrow provider boundary. The CLI owns authentication; Blackhole
never requests, reads, copies, exports, or persists provider tokens. Capture is
provider-independent and returns a durable `Saved.` receipt before semantic
work.

The application then combines:

- a durable asynchronous queue with chronological ownership, lease recovery,
  retry, and restart-safe processing;
- open-world Memory for entities, facts, events, tasks, deadlines, relations,
  documents, transactions, observations, and proposed actions;
- semantic truth that distinguishes current, historical, uncertain,
  conflicting, attributed, negated, corrected, superseded, and duplicate
  evidence;
- deterministic date/time normalization, lifecycle handling, comparisons,
  and financial/occurrence aggregation;
- Attention as a unique projection of unresolved, actionable items, with
  capture-time due dates, human explanations, and approval-gated proposed
  actions;
- bounded natural Ask retrieval with temporary thread context, narrow
  evidence selection, and provenance derived from the evidence actually used;
- language-invariant semantic keys that keep Polish, English, mixed-language,
  and other source labels from becoming separate memories; and
- permanent, idempotent Undo/forget that removes the selected source-linked
  Product V2 state and unreferenced attachment data while preserving unrelated
  state.

Raw sources remain immutable during normal operation. Derived state is
rebuildable from evidence and versioned transformations. Missing information
stays unknown. No consequential external action is executed without explicit
approval.

## End-to-End Quality

The final Product V2 path is exercised through the real local Host/PWA seam:

```text
browser Capture
  → POST /api/v2/capture
  → raw source + durable pending row
  → background worker / explicit process
  → normalized semantic state + rebuildable projections
  → Attention, Memory, and bounded POST /api/v2/ask
```

The final development/dogfood evidence reports:

- application tests: `216/216 PASS` (including the macOS timezone, live-UX, and relative-day regressions);
- root discovery suite: `233/233 PASS`;
- evaluator tests: `10/10 PASS`;
- Product V2 acceptance harness: `7/7 PASS`;
- integrated Product V2 acceptance: `50/50 PASS`;
- quality gates: `7/7 PASS`; and
- benchmark structure: `200` events with checkpoints at `50`, `100`, `150`,
  and `200`.

The integrated acceptance uses a deterministic in-process provider and fresh
temporary Homes. It is useful product acceptance evidence, but it is not an
unseen generalization benchmark. The real authenticated Codex path was also
validated in bounded dogfood runs; its latency and incomplete semantic cases
remain disclosed below.

### macOS portability hotfix

The fresh-Mac reproduction supplied for this task exposed a local timezone
portability failure: before the fix, the application report was `184` tests
with `5` failures and `120` errors, while the evaluator was `10/10 PASS` and
the acceptance harness was `7/7 PASS`.

On macOS, `datetime.now().astimezone().tzinfo` can be a fixed-offset
`datetime.timezone`. The broken implementation called `current.utcoffset()`
without the required datetime argument, so default Product V2 Capture raised
`TypeError: timezone.utcoffset() takes exactly one argument (0 given)`.

Hotfix commit `8eb8158c9177114ff66122f98c5bfef1ccd0aeb4` retains the aware
local datetime, validates IANA names from `tzinfo.key`, `TZ`, and safe POSIX
metadata, preserves the existing Windows aliases, and uses the actual
aware-datetime offset only as a last resort. Explicit timezone precedence and
capture-time-relative normalization remain unchanged. On this Mac,
`local_timezone_name()` resolved `Europe/Warsaw`, default capture succeeded,
and `resolve_timezone(None)` returned a usable `ZoneInfo`.

The post-fix deterministic evidence is `192/192` application tests,
`209/209` root discovery tests, `10/10` evaluator tests, `7/7` acceptance
harness tests, and `50/50` integrated acceptance cases with no live provider
call. The machine-readable acceptance result is
[`eval/results/product-v2-integrated-acceptance.json`](../eval/results/product-v2-integrated-acceptance.json).

### Final live Ask + Memory + UI hotfix

The explicitly authorized final live UX hotfix preserves the frozen benchmark
and Product V2 provider configuration while making Ask current-question-first,
keeping previous assistant text out of evidence, rendering provenance as
secondary support, and treating generic event captures as coexisting known
occurrences. Genuine clarification now navigates to Ask with a prefilled
question without auto-submitting or persisting a fact. Memory is current-first
with closed `History · N` and `Occurrences · N` disclosures; Capture and
Attention use the reviewed mobile-safe geometry.

The bounded live smoke used a fresh temporary Home, four synthetic captures,
and three Ask requests. All seven HTTP requests returned 200; processing ended
at four processed, zero failed, one attempt per capture, and zero retries. The
topic-switch Ask did not reuse the museum-pass fact for the X aggregate, and
the real X occurrence Memory remained known occurrence state without false
clarification, conflict, or history duplication. Exact state and answers are
preserved in
[`trajectories/runtime/046-final-live-ask-memory-ui-hotfix/trace.json`](../trajectories/runtime/046-final-live-ask-memory-ui-hotfix/trace.json).
The machine-readable hotfix gate is
[`eval/results/product-v2-final-live-ux-hotfix.json`](../eval/results/product-v2-final-live-ux-hotfix.json).

## Measured Improvement

### Frozen V1 development benchmark

V1 is the scientifically evaluated system. Its official public development
baseline and final kept development reference are:

| V1 evidence | Result |
| --- | --- |
| Stateless `baseline-v1` | `LQA-0M 0.30149145529538973`, `DSCR 277` |
| Final kept V1 development reference, Experiment 005 | `LQA-0M 0.8695006212469447`, `DSCR 40` |
| Recorded replay provider calls | `0` |

The frozen case is one public 200-event scenario with four isolated
checkpoints. These scores are V1 benchmark measurements, not Product V2
semantic scores.

### Post-freeze V1R1 shadow/generalization set

The later result uses **three fresh synthetic worlds**. It is a post-freeze
shadow/generalization set, not an organizer-provided official holdout and not
a significance claim:

- baseline macro LQA: `0.2591711465`;
- Blackhole macro LQA: `0.2712347361`;
- absolute LQA delta: `+0.0120635896`;
- reported error-rate reduction: `+1.6283908892%`;
- mean successful runtime: `3066.475526 s` baseline vs `897.310841 s`
  Blackhole;
- operational retries: `3` baseline vs `0` Blackhole;
- hard failures: `0 / 0`; and
- schema validity: `0/3` baseline vs `3/3` Blackhole.

The public report is [`docs/GENERALIZATION_V1R1_REPORT.md`](GENERALIZATION_V1R1_REPORT.md).

### Final Product V2 head-to-head

After the implementation freeze, a separate sealed comparison tested the
frozen Product V2 path against a fresh stateless raw-memory Codex comparator.
It used four newly authored synthetic worlds, 80 captures, checkpoints at
7/14/20, and 13 queries. Both systems used `gpt-5.6-luna` with low reasoning.
This is a descriptive post-freeze generalization result, not a new V1 score,
official holdout, or E006 optimization.

| Result | Raw-memory Codex | Product V2 |
| --- | ---: | ---: |
| PTS (macro F1 across 10 families) | `0.8575` | `0.7928` |
| Attention precision / recall / F1 | `0.5385 / 0.6154 / 0.5641` | `0.6410 / 0.7692 / 0.6795` |
| Query schema validity | `13/13` | `13/13` |
| Operational wall time | `130.878 s` | `1217.334 s` |

The raw-memory comparator recalled more of this small authored assertion set,
while Product V2 produced the stronger active Attention set and exercised
durable processing, provenance, and permanent Undo through the normal product
boundary. The result is intentionally mixed and is not used to tune frozen
Product V2 or V1 behavior. The complete sanitized report is
[`docs/FINAL_H2H_REPORT.md`](FINAL_H2H_REPORT.md), with the machine-readable
summary at
[`eval/results/final-h2h-001-summary.json`](../eval/results/final-h2h-001-summary.json).

### The engineering lesson

The measured story is intentionally not a victory lap:

> Optimizing an agent for measurable structured correctness can accidentally
> optimize the product away from the user.

The large DEV improvement transferred weakly to fresh worlds. Human dogfooding
then found that the product still had lifecycle, provider-schema, Ask-routing,
language, provenance, semantic-truth, Undo, and presentation problems. The
Product V2 redesign and final repairs are the response to those observed user
failures, not an attempt to rewrite the V1 score.

## Reproducibility

Start with [`README.md`](../README.md) for the local Product V2 quickstart and
[`docs/REPRODUCTION.md`](REPRODUCTION.md) for the split between V1 benchmark
reproduction and the Product V2 local application.

The repository preserves:

- the public V1 scenario, response contract, evaluator, baseline result, and
  Experiment 005 result;
- deterministic application, evaluator, acceptance, compile, JavaScript,
  benchmark-structure, contract-smoke, and qualification checks;
- safe synthetic Product V2 demo preparation through
  `scripts/prepare_product_v2_demo.py`;
- coding and runtime evidence in [`TRAJECTORY_INDEX.md`](../TRAJECTORY_INDEX.md);
- the final Product V2 integration, dogfood, and acceptance records; and
- the authoritative final `product-v2-submission-release` tag and remote SHA,
  recorded in
  [`docs/SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md) after finalization.
  The historical `product-v2-submission` and `product-v2-submission-final` tags
  remain prior snapshots and are not moved.

The deterministic gate does not require provider credentials and does not run
new semantic-provider performance experiments:

```text
python -m unittest discover -s . -p "test_*.py" -v
python -m unittest discover -s eval/tests -v
python -m unittest product_acceptance.harness.test_harness -v
python scripts/run_product_v2_integrated_acceptance.py
python -m compileall -q app eval product_acceptance scripts
node --check app/web/app.js
python benchmark/dev/generate_benchmark.py --check
python eval/contract_smoke.py
python scripts/qualification_check.py --inventory
git diff --check
```

## Hot Take / Insights

The benchmark rewarded structured correctness, but the user needed something
quieter and more trustworthy: a capture that never gets lost, a current answer
that does not erase history, an unknown that is not a guess, and an Attention
list that does not become noise. The important design shift was to treat
benchmark evidence, product semantics, and human dogfood as different sources
of truth with different gates.

The resulting product is deliberately inspectable. A judge can follow a
capture from immediate receipt through queue state, semantic interpretation,
current/history projection, Attention, Ask evidence, and explicit Undo.

## Known Limitations

- Capture is immediate, but live background semantic processing remains slower
  than desired. Prior final dogfood measured a first useful state around
  `23.031 s` and a remaining burst around `129.562 s`.
- Those measurements are real provider evidence; deterministic fixture timing
  does not replace them. The demo uses prepared state rather than waiting for a
  four-item live burst on camera.
- PDFs and other attachments are persisted with truthful read/unread/
  unsupported status, but semantic understanding remains limited where the
  provider cannot interpret them. No blanket OCR/vision guarantee is made.
- This is a local single-user application. Pairing, cloud sync, hosted
  deployment, and production remote security are deferred.
- Graceful Windows terminal stop logging may remain imperfect in a live
  launcher, although deterministic clean-stop logging is covered.

## Claim and privacy boundaries

Product V2 acceptance and dogfood results are labeled development acceptance
evidence. They are not unseen generalization results. V1 benchmark scores are
not Product V2 scores. The V1R1 set is described as three fresh synthetic
worlds, not an official holdout. No private human dogfood data, credentials,
V1 oracle, evaluator-owned holdout expected outputs, or new G01/G02/G03 tuning
is part of this submission package.
