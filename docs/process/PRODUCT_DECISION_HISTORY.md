# Blackhole product decision history

## Scope and attribution

This is a sanitized reconstruction of the project’s product and engineering
decisions, written from a complete private advisory conversation, the committed
coding trajectories, runtime traces, evaluation artifacts, and Git history.
It is a decision history, not a transcript. The human owned the product,
provided the real-world feedback, and accepted, rejected, constrained, or
redirected proposed work. ChatGPT acted as an advisory planning and
interpretation partner. Codex coding trajectories are the authoritative record
of what was implemented, tested, and committed. Where authorship is not
material, this document uses neutral language such as “the project chose” or
“the evaluation showed.”

The history is intentionally split into three kinds of evidence: the frozen V1
scientific benchmark, post-freeze Product V2 acceptance and dogfood, and the
separately authorized final frozen Product V2 head-to-head evaluation. These
are different claims and their numbers must not be combined.

## 1. The original product problem

Blackhole began with a simple observation: everyday life produces information
faster than many people can organize it. A receipt arrives while someone is
leaving a shop. A deadline is mentioned in a message. A person remembers where
something was put, notices a price change, or realizes that an ordinary task
still needs doing. Traditional productivity software often responds by asking
the person to make a series of decisions at the exact moment when they are
already trying not to forget the information: Is this a task or a note? Which
project owns it? What tag, folder, due date, or category should be selected?

That design turns capture into a second job. If the organizational work is
delayed until the person has more attention, the evidence may already be lost;
if it is required immediately, the person may abandon capture altogether. The
problem is particularly visible for people with executive-function friction,
attention overload, forgetfulness, or simply a low tolerance for maintaining a
personal taxonomy. The intended use case is not limited to any diagnosis and
does not make a medical claim. It is a general product problem: how can a
person safely put fragmented life information somewhere without first
becoming its librarian?

The core product principle became **Capture now. Understand automatically.
Find it later.** The project called this zero-organization capture. One quiet
inbox should accept a reminder, location, preference, receipt, document, task,
or observation without demanding a folder or schema. That principle was more
important than any individual interface or model choice. The product was not
intended to be another chat window that required the user to formulate a
perfect prompt. It was intended to be an external memory that reduces the
amount of life administration required from the user.

The early advisory discussion considered several narrower hackathon ideas,
including issue triage, bug reproduction, warranty analysis, and household
repair. The human feedback moved the direction toward ordinary personal
problems and toward a system that could accept receipts, contracts, tasks,
subscriptions, locations, and incomplete notes in one place. That choice gave
the project a real user motivation and also created a difficult engineering
requirement: it had to cope with state changing over time rather than merely
extracting fields from isolated inputs.

## 2. The early architecture

The first stable architecture was a loop rather than a collection of features:

```text
Capture → understand → remember → connect → plan → remind
```

Capture was deliberately cheap and durable. The initial interaction should
finish after the evidence had been saved, even if no model was available. A
provider could later interpret the source, relate it to existing information,
derive a useful state, and decide whether it deserved the user’s attention.
That made semantic understanding asynchronous by design. The user’s immediate
guarantee was persistence, not instant interpretation.

The architectural boundary was expressed in four layers. Immutable raw
sources preserve what was actually captured. An interpretation layer records
structured observations and relations with provenance. A state layer represents
entities, facts, events, tasks, obligations, documents, and other open-world
objects. Deterministic projections then build current Memory, history,
Attention, aggregates, and query evidence. This separation means a prompt,
model, schema, or projection rule can change without rewriting the source.

Several early decisions became non-negotiable. Derived state must be
rebuildable from immutable inputs plus versioned transformations. `unknown` is
not the same as false, zero, empty, or complete. Corrections are new evidence,
not edits to an old source. Arithmetic, dates, comparisons, duplicate checks,
financial aggregation, and lifecycle decisions belong to deterministic code or
SQL; an LLM may interpret text or propose structure, but it is not the
calculator of record. An external action such as paying, cancelling, signing,
sending, or changing an account would require explicit user approval.

Attention was defined as a scheduler-like projection, not the source of truth.
An open deadline, unresolved uncertainty, material change, or proposed action
could be surfaced there, but removing it from the active view could not erase
the evidence. Memory needed to preserve history and uncertainty so that a
current answer did not become a false rewrite of the past.

SQLite was chosen over a directory of Markdown files as the durable state
index. The filesystem remains appropriate for raw blobs and attachments, while
SQLite provides transactions, queryable relationships, rebuildable projections,
and lifecycle state over months of captures. The runtime was shaped as a
local-first Host with a mobile-first web/PWA client. The primary provider path
was subscription-first: an already-installed, already-authenticated Codex CLI
owns authentication, while Blackhole only observes safe readiness information
and never requests, reads, copies, exports, or persists provider tokens. The
project deliberately did not claim cloud sync, production remote security,
universal OCR, or a Claude adapter.

## 3. Why V1 needed a measurement strategy

The hackathon required more than a plausible demo. It required a baseline, an
agentic solution, measurable improvement, reproducibility, and a record of how
coding agents were directed and checked. The project therefore committed to
defining the measurement contract before building the advanced system. Coding
trajectories would record implementation work; the improvement changelog would
record hypothesis, evaluation, regressions, and disposition; and the benchmark
would remain separate from private product data.

The first benchmark draft proposed a final-state F1-style metric. Review
showed that this described an ontology more readily than it described the
user’s problem. The contract was revised around longitudinal state maintenance
and fixed checkpoint questions. A deterministic synthetic world generated
chronological captures and expected checkpoint assertions. The benchmark
tested current state, history, changes, temporal meaning, obligations,
duplicates, uncertainty, contradictions, provenance, and the approval
boundary.

The primary measure became Longitudinal Query Accuracy at Zero Maintenance
(LQA-0M). At a high level, each fixed query compares expected and produced
canonical assertions, penalizing both omissions and unsupported claims. The
mean is taken across queries and checkpoints without arbitrary category
weights. Distinct State Corrections Required (DSCR) was retained as a
secondary root-defect count: repeated symptoms of one underlying state error
count once. DSCR is not human minutes, and the project avoided presenting it as
such.

Calibration then tested 50-, 100-, 200-, and 400-event prefixes of a synthetic
longitudinal stream. The purpose was not to exhaust a context window; it was to
find a practical history length at which state churn remained meaningful. The
Codex CLI with `gpt-5.6-luna` completed the tested histories without an
observed truncation or context rejection signal, although the larger runs were
slower and had more state errors. The project froze one 200-event development
scenario with checkpoints at 50, 100, 150, and 200. The calibration oracle was
kept separate and non-scored.

The fair V1 comparator was one persistent general-purpose long-chat session,
not a set of independent one-shot prompts. It received the chronological raw
captures and fixed questions but no Blackhole database, summary, retrieval
layer, entity graph, or reconciliation tool. Checkpoint questions were issued
in isolated forks so that a query could not teach the continuing ingestion
conversation its own answer. This was a deliberately strong baseline: the
comparison asked whether structured external state added value beyond giving a
capable model the available history.

## 4. V1 measurement, contract repair, and development results

The first baseline output completed syntactically but used an assertion
vocabulary that did not cross the evaluator boundary. Its `LQA-0M = 0.0000`
was therefore not semantic zero; the run was preserved as an invalid-contract
failure. Gate B repaired the response boundary with public semantic subjects
and predicates, explicit known/inferred/unknown rules, deterministic
normalization, and validated provenance. The corrected official baseline was
then measurable:

```text
baseline-v1 LQA-0M: 0.30149145529538973
baseline-v1 DSCR:    277
```

The advanced work proceeded as bounded experiments against the unchanged
public development case. Experiment 001 added immutable raw captures,
structured observations and relationships, a rebuildable SQLite projection,
and deterministic query projections. Experiment 002 removed benchmark-specific
projector routing; its full replay was numerically identical, which was useful
repair evidence rather than a new improvement. Experiment 003 addressed a
different failure: the model could not reconcile older receipts when extraction
context exposed only metadata. Bounded raw-candidate retrieval and deterministic
relation reconciliation improved relation detail and lowered DSCR. Experiment
004 added a conservative raw-source completeness pass that recovered certain
dates, amounts, identifiers, and lifecycle cues that extraction had omitted.

Experiment 005 then found that the projection boundary was discarding useful
semantic evidence from true duplicate captures. The repair built components
only from true duplicate relation types, chose a canonical earliest event, and
consolidated equal or additional evidence without turning the duplicate into a
new occurrence. Similar captures, meaningful changes, contradictions, and task
reassignment were intentionally not collapsed. The replay used zero provider
calls because it reused recorded semantic output and changed only deterministic
projection behavior.

The final kept V1 development reference was:

```text
final E005 LQA-0M: 0.8695006212469447
final E005 DSCR:    40
```

That is an impressive development-set change from `0.30149145529538973` and
`277`, but its meaning is bounded. It shows that structured state, relation
reconciliation, selective completeness, and duplicate-aware evidence could
solve many measured failures in the frozen synthetic world. It does not prove
general personal-memory quality, production reliability, or performance on a
holdout. The final V1 experiment was explicitly E005; no E006 benchmark
optimization was authorized.

## 5. The generalization shock

After the V1 implementation was frozen, three new synthetic worlds were
generated and sealed before scoring. The candidates were produced by the
baseline and Blackhole treatments independently; the oracle was opened only
after sealing. This was a post-freeze shadow/generalization set, not an
organizer-owned holdout, and the project made no statistical-significance
claim.

The fresh result changed the story materially:

```text
baseline macro LQA:  0.2591711465
Blackhole macro LQA: 0.2712347361
absolute delta:      +0.0120635896
reported error-rate reduction: +1.6283908892%

mean successful runtime:
  baseline: 3066.475526 s
  Blackhole: 897.310841 s

operational retries: 3 → 0
hard failures:      0 → 0
schema validity:    0/3 → 3/3
```

Blackhole was ahead in two worlds and behind in the third. Its operational
execution was faster in the sealed evidence and its outputs were schema-valid
in all three worlds, but semantic transfer was weak. The large V1 development
gain did not transfer strongly to unseen synthetic worlds. The result was kept
unchanged and described plainly; the team did not tune the product, baseline,
or benchmark after looking at it.

## 6. The product lesson

The central lesson became:

> Optimizing an agent for measurable structured correctness can accidentally
> optimize the product away from the user.

The V1 contract rewarded exact public assertion shapes, fixed query families,
and benchmark-visible state. Those constraints were appropriate for a
scientific measurement, but they also encouraged a product surface that looked
like an evaluator: assertion cards, predicates, retrieval labels, and
hard-coded query routes. A system can be excellent at maintaining the state
representation a benchmark requests and still be awkward when a person asks
an open-ended question in a new language, changes topic, or wants a normal
sentence rather than a structured record.

This was not a reason to discard the V1 evidence. It was a reason to stop
using that evidence as a substitute for product validation. V1 remained a
valuable controlled experiment. Product V2 would be judged through deterministic
acceptance, authenticated live smoke, browser review, and human dogfood, with
each result labeled according to what it actually established.

## 7. Product V2 redesign: open-world memory

Product V2 stayed in the same repository so the evolution would remain visible,
but it was explicitly post-evaluation product development. The redesign
returned to the original user promise: a quiet inbox that can accept ordinary
life fragments without requiring a fixed ontology.

The V2 runtime separated a durable Capture boundary from a deferred processing
queue. A user could save text, an attachment reference, or a combined capture
and immediately receive a durable receipt. A worker later interpreted pending
items chronologically, retried failures with bounded delays, and committed
semantic rows and projections atomically. The Host owned the Home, database,
provider readiness, queue, and API; the PWA remained a thin client.

Memory became open-world and current-first. It could contain a person, object,
place, preference, task, subscription, document, payment, occurrence, or
other concept not known in advance. Current state was not allowed to erase
history. The system kept evidence, uncertainty, contradictions, attribution,
negation, corrections, supersession, and duplicate support distinct. Repeated
events such as two consumptions were modeled as occurrences rather than as two
competing values of one fact. Time was anchored to the capture timestamp and
timezone, including relative days and DST-local calendar behavior.

Language was moved to the presentation boundary. A Polish capture and an
English question should be able to meet through stable semantic keys, while
the answer follows the current question language. This was implemented as a
language-invariant semantic boundary rather than as a growing list of keyword
exceptions. Ask candidate retrieval was separated from the evidence that the
final answer actually used, so a bounded candidate set could not automatically
become a citation set.

Attention became a unique active projection of unresolved, actionable items.
An open deadline or task could be active; a completed, cancelled, or
superseded item could not remain active merely because an old row survived.
Nevertheless, terminal lifecycle history remained inspectable in Memory. New
evidence could close an existing open Attention item when a strong lifecycle
link made the relationship clear. The product goal was to answer “what needs
me?” without turning history into noise.

## 8. The real provider failure

Mocks and deterministic fixtures were useful, but actual provider integration
exposed a failure that could not be inferred from them. The installed Codex
CLI rejected the first Product V2 structured-output schema with an HTTP 400
`invalid_json_schema` error and a terminal `turn.failed` event. The schema
allowed additional properties and left arrays and nested objects insufficiently
closed. A PowerShell shell-snapshot warning appeared in the same diagnostics,
but disabling that feature did not solve the real problem. The failure was a
provider contract mismatch, not a semantic answer.

The repair generated a strict schema with typed array items, closed nested
objects, required fields, and nullable optional values. The adapter preserved
the terminal failure event and bounded sanitized diagnostics so provider
failures were retryable and understandable without exposing credentials or
raw payloads. This is why real provider integration mattered beyond mocks: it
tested the contract at the boundary where the shipped application actually
ran.

The same boundary preserved the subscription-first rule. Blackhole did not
obtain a direct API key. The local CLI handled login and provider invocation.
The product reported readiness and safe failure state, not token material.

## 9. Human dogfood as a development method

The independent 50-case Product V2 acceptance corpus was useful for visible
contracts and deterministic regression, but human dogfood found classes of
failure that a harness written from the contract did not naturally discover.
The human used the integrated application as a person would, including messy
captures, waiting for the worker, changing topics, and judging whether the
result made sense without reading internal state.

The observations included stale or duplicated Attention, completed work that
still looked active, countdown and badge inconsistencies, and a payment or
completion capture that did not close the corresponding open item. Ask could
expose retrieval-shaped language, raw objects, `self: 1`, timestamps, or
irrelevant evidence. A follow-up question could inherit the previous thread
topic even when the new question was fully specified. Ordinary occurrences
could be mislabeled as conflicting state, while genuine uncertainty could be
presented as a useless clarification. Mixed-language inputs exposed the need
for language-neutral semantics and question-language rendering. Attribution
metadata and internal payloads leaked into ordinary answers. Chat scrolling,
composer alignment, disclosure state, and mobile spacing were also part of
whether the product felt trustworthy.

These were not private dogfood facts to publish. They were failure classes
that redirected implementation. The coding trajectories show the sequence:
runtime foundation, UI redesign, independent acceptance, Host/PWA integration,
provider-schema repair, Ask routing, language invariance, provenance precision,
semantic truth, permanent Undo, final dogfood repairs, cross-platform repair,
relative-day repair, and final coherence. The human feedback repeatedly
stopped the team from treating a deterministic PASS as permission to ignore a
bad live experience.

The resulting product contract became more conservative. Capture could say it
was saved even when understanding was pending. The UI could say that memory was
still being understood rather than claim “no data.” Ask could fail closed or
state uncertainty rather than produce a confident unsupported answer. Normal
presentation had to be human-readable, while evidence and provenance remained
available behind the appropriate disclosure.

## 10. The cross-platform release failure

Fresh-machine reproduction on macOS then found a portability defect that the
original Windows-centered checks had missed. Local timezone discovery could
return a fixed-offset `datetime.timezone`, while the code called
`tzinfo.utcoffset()` without the required datetime argument. Product V2 Capture
failed before saving, even though the evaluator and acceptance harness were
green. The observed pre-fix application report was `184` tests with `5`
failures and `120` errors; the evaluator still reported `10/10` and the
acceptance harness `7/7`.

The fix retained aware local datetimes, used IANA names and safe environment or
POSIX metadata where available, preserved known Windows aliases, and used the
aware offset only as a last resort. The fresh-Mac run then passed the full
deterministic gates. The important decision was procedural as much as
technical: a release is not portable because a test suite passes on the
author’s original machine. Reproduction on a fresh operating system matters.

## 11. Ask evolution

Ask went through three distinct product phases. First it was close to a
retrieval/debug view: keyword routes selected an internal projection and the
UI exposed the structure directly. That was quick and easy to test, but it
made open-world use brittle. A short word such as the Polish preposition `do`
could route a location question to an unrelated task path.

The next phase introduced deterministic fast paths. Date normalization,
arithmetic, occurrence totals, lifecycle, high-confidence Attention, and
provenance remained code-owned because they are the operations where exactness
and auditability matter. This improved speed and made important calculations
reproducible, but deterministic paths sometimes emitted ugly internal prose.

The final Product V2 boundary is deliberately split. Deterministic code owns
truth selection, current/history semantics, date and timezone normalization,
arithmetic, lifecycle reconciliation, and validation of source evidence. When
the provider is ready, it receives a bounded, selected evidence context and
returns a constrained answer with evidence IDs. AI owns the normal
human-facing synthesis. Invalid, unsafe, empty, or ungrounded provider output
falls back to an explicitly marked deterministic/degraded result.

Thread continuity is now a temporary referent hint, not a truth source. A new
fully specified question takes priority over the previous topic. The latest
turns can help answer “what does that mean?” or “what about earlier?”, but a
new thread clears that context. This preserves conversational usefulness
without letting an old assistant answer contaminate retrieval.

## 12. Attention and Memory coherence

The final lifecycle semantics are intentionally simple to explain. An open
task or obligation is active Attention. Completion or cancellation removes it
from the active set and badge, but the terminal event remains inspectable in
Memory/history. A later capture can reconcile an open item when it strongly
identifies the same lifecycle or document; unrelated completion language must
not close an arbitrary item.

This distinction fixed a subtle conceptual error. “Not currently asking for
attention” is not the same as “never happened.” Active Attention is a focused
projection. Memory is the durable account of what was observed, what changed,
what remains uncertain, and what was completed. The product can therefore be
quiet without becoming forgetful.

## 13. Document understanding without an OCR claim

Human dogfood also showed why a role extracted from a document is a poor
primary identity. For an invoice-like document, “Buyer” describes a party’s
role; it does not tell the user which document they are looking at or what
needs attention. It is too generic to reconcile a later payment reliably.

The final Product V2 document projection therefore prefers a useful identity
assembled from evidence: document type, reference, issuer or provider,
service or subject, amount and currency, due date, payment status, and related
account or reference where supported. A later payment can then close only the
matching document Attention. Raw attachment bytes and source provenance stay
intact, and unsupported fields remain unknown. The project does not claim that
the provider can OCR or understand every PDF or image; document and image
handling is bounded by actual provider support.

## 14. Undo as permanent forget

Ordinary correction, supersession, and lifecycle history preserve evidence.
Undo is different because it is an explicit user request to forget. The final
Product V2 decision narrowed the concept to one understandable operation:
**Undo means permanent delete inside the selected Product V2 Home.**

The implementation removes the source event, processing state, source-linked
derived facts and relations, provenance, and unreferenced attachment blobs. A
minimal event-ID tombstone can prevent reuse and protect a worker race, but it
does not retain text, files, or semantic content. Shared blobs survive while
another capture references them. Late provider results and mixed batches are
checked against the surviving rows so a deleted capture cannot be resurrected.
The operation is idempotent and explicit; it is not automatic history cleanup.

## 15. Latency tradeoff

The redesign made an intentional latency tradeoff instead of pretending it had
solved latency. Capture durability is immediate: the user should be able to
leave the interaction after the raw evidence is written. Understanding is
asynchronous and depends on the local provider, prompt, queue, and batch.

During the bounded Product V2 effort comparison, ordinary five-case extraction
calls measured approximately `48.859 s` at high reasoning, `43.391 s` at
medium, and `31.640 s` at low. Low was selected because the same semantic
checks passed at each effort, not because low was claimed universally better.
The final product used conservative batches of two. In the final live dogfood,
the first useful state appeared around `23.031 s`, while the remaining burst
took about `129.562 s`. These are real provider-backed observations, not
deterministic fixture timings, and they do not demonstrate that latency was
solved.

Final provider-backed Ask samples were about `11.5–11.7 s`. Earlier
deterministic Ask paths could answer in roughly 15–16 ms, but that speed came
from returning internal-style deterministic prose and was not sufficient as
the final human-facing contract. The shipped Product V2 therefore favors a
natural, grounded AI answer over claiming that every Ask is instant. The demo
uses a prepared synthetic Home so the video can show the product without
misrepresenting the asynchronous wait.

## 16. Final evidence state

The project ends with three evidence layers.

**V1 scientific evidence** is the frozen 200-event development benchmark,
with its valid official baseline (`LQA-0M 0.30149145529538973`, `DSCR 277`),
the kept E005 development reference (`LQA-0M 0.8695006212469447`, `DSCR 40`),
and the post-freeze V1R1 shadow/generalization result (`0.2591711465` versus
`0.2712347361`, a `+0.0120635896` macro delta). These numbers belong to the
V1 contract and are not Product V2 scores.

**Product V2 development acceptance and human dogfood** establish a different
kind of evidence: the final implementation’s deterministic tests, visible
50-case acceptance, cross-platform checks, browser review, and bounded live
smokes. They show that the product boundaries and the human-facing lifecycle
were repaired through observed use. They do not establish holdout accuracy or
statistical significance. Their limitations—especially provider latency and
the absence of production security, sync, pairing, and universal document
understanding—remain part of the result.

**The final frozen Product V2 head-to-head** is a separately authorized,
post-freeze comparison of the immutable `hackathon-submission-demo-ready`
snapshot against the same model family receiving raw chronological captures at
query time. Its cases, scoring contract, operational measurements, and
interpretation are maintained outside the product repository until sealed, and
its sanitized result is documented separately. It must not be merged into V1
LQA, used to tune the product after sealing, or described as official holdout
evidence.

The durable process conclusion is therefore not “the benchmark proved the
product.” It is that measurement, implementation trajectories, real provider
integration, cross-platform reproduction, and human dogfood each exposed a
different part of the truth. Keeping those boundaries visible made it possible
to preserve the strong V1 evidence, acknowledge its weak transfer, and still
build a more coherent product for people.

## Evidence map

- V1 contract and results: [`docs/EVALUATION.md`](../EVALUATION.md),
  [`docs/GATE_B_VALID_REPORT.md`](../GATE_B_VALID_REPORT.md), and
  [`trajectories/coding/008-gate-b-contract-repair/summary.md`](../../trajectories/coding/008-gate-b-contract-repair/summary.md).
- E003–E005 experiments: [`IMPROVEMENT_CHANGELOG.md`](../../IMPROVEMENT_CHANGELOG.md),
  [`trajectories/coding/014-experiment-003-relations/summary.md`](../../trajectories/coding/014-experiment-003-relations/summary.md),
  [`trajectories/coding/015-experiment-004-selective-verification/summary.md`](../../trajectories/coding/015-experiment-004-selective-verification/summary.md),
  and [`trajectories/coding/016-experiment-005-duplicate-evidence/summary.md`](../../trajectories/coding/016-experiment-005-duplicate-evidence/summary.md).
- Product V2 implementation history: [`TRAJECTORY_INDEX.md`](../../TRAJECTORY_INDEX.md),
  [`docs/PRODUCT_V2_HUMAN_DOGFOOD.md`](../PRODUCT_V2_HUMAN_DOGFOOD.md), and
  the coding trajectories `031` through `049`.
- Generalization evidence: [`docs/GENERALIZATION_V1R1_REPORT.md`](../GENERALIZATION_V1R1_REPORT.md)
  and [`trajectories/coding/030-generalization-v1r1-scoring/summary.md`](../../trajectories/coding/030-generalization-v1r1-scoring/summary.md).
- Advisory/process framing: [`CHATGPT_DECISION_LOG.md`](CHATGPT_DECISION_LOG.md)
  and [`CHATGPT_TRANSCRIPT_NOTE.md`](CHATGPT_TRANSCRIPT_NOTE.md).
