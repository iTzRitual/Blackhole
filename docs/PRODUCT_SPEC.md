# Product specification

**Product:** Blackhole
**Descriptor:** A zero-organization life inbox.
**Status:** Product design retained; Gate A benchmark frozen, Gate B response contract valid; V1 implementation frozen; Product V2 runtime foundation authorized post-evaluation
**Audience:** Product, engineering, evaluation, and agent-workflow contributors

## 1. Product intent

Blackhole is a zero-organization personal inbox. It gives a person one low-
friction place to capture fragments of everyday life without requiring a folder,
tag, project, category, due date, or decision about what the fragment means.

The product earns its value later by turning those fragments into an
understandable, persistent picture of facts, entities, obligations, deadlines,
changes, and items requiring attention.

## 2. Problem framing

Traditional productivity systems often make capture itself into a second task. A
person wants to get something out of their head quickly, but the tool may require
choosing a database, folder, project, category, due date, priority, tags, or
properties before the thought is safely stored.

This friction is especially relevant for people who experience executive-function
friction, attention overload, forgetfulness, or low tolerance for organizational
overhead. ADHD is a strong example of this user need, but Blackhole makes no
medical claims: it does not diagnose, treat, or improve ADHD or any other medical
condition and does not provide medical assistance.

## 3. Core principle

> **CAPTURE NOW. ORGANIZE LATER.**

The primary capture interaction should be:

```text
input
  → saved
```

Classification and organization are deferred. A user should not need to decide
what an item is before preserving it.

Operationally, Blackhole also follows **CAPTURE NOW. UNDERSTAND LATER.** The
synchronous capture path validates the input, appends one immutable raw event,
records a separate derived `pending` processing row, and returns `Saved.`. It
does not call a semantic provider, classify the input, resolve entities, or
rebuild semantic state during the capture interaction. A later processing run
can make the capture useful to queries, attention, and memory.

## 4. Primary user job

> “Let me put this somewhere safe now, and help me understand what it means when I have the attention to deal with it.”

## 5. Supported capture categories

The initial concept covers:

- short text and free-form notes;
- receipts and other images;
- documents;
- tasks and reminders;
- subscriptions;
- contracts and agreements; and
- financial observations.

These are examples of source material, not a classification burden imposed on
the user.

## 6. Desired system responsibilities

After capture, the system may propose or maintain:

1. extracted facts and supporting evidence;
2. classifications and candidate entity links;
3. persistent state for entities and relationships over time;
4. an explicit distinction between known, inferred, and unknown information;
5. tasks, obligations, and relevant deadlines;
6. duplicate and change findings;
7. deterministic financial aggregates; and
8. a focused attention view containing items that need review or action.

These are derived capabilities. They must never overwrite the original source.

## 7. UX principles

### Silent by default

Normal capture should ideally be `input → saved`. The user should not have to
maintain a conversation, answer classification questions, or fill properties in
order to capture information.

### Interrupt only when useful

Proactive interruption is reserved for information that may materially help the
user, such as:

- deadlines and reminders;
- unresolved conflicts that matter;
- required decisions;
- important changes; and
- other attention-worthy obligations.

Routine capture and routine organization should not produce unnecessary
interruptions.

### Observe, do not judge

Blackhole should surface factual observations without moralizing about behavior.
For example, it should prefer:

> “18 confirmed energy-drink observations in August; observed spend: X; data coverage: 22/28 days.”

over an unsolicited judgment such as:

> “You are drinking too many energy drinks.”

Interpretation, advice, or behavioral recommendations may be provided when the
user explicitly requests them.

## 8. Information semantics

### Known

Information directly supported by an available source or by explicit user
confirmation. The evidence and extraction path should be visible to the system
and, where useful, to the user.

### Inferred

A hypothesis or interpretation derived from one or more sources. It must remain
distinguishable from a directly observed fact, carry its provenance, and be
revisable when new evidence arrives.

### Unknown

Information that is missing, unreadable, ambiguous, conflicting, or not yet
checked. Unknown must remain unknown. In particular, absence of a value does not
imply zero, false, “none,” or completion.

## 9. Safety and trust requirements

- Original source content is immutable.
- Derived state can be rebuilt when extraction, prompts, models, or rules change.
- Arithmetic and other deterministic transformations have an executable source
  of truth.
- The system does not autonomously send, pay, cancel, sign, delete, or otherwise
  cause a consequential external effect.
- Financial and contractual information is presented as extracted or inferred
  information, not as professional advice.
- Sensitive content is handled with least-necessary exposure and explicit
  retention decisions.
- The benchmark's primary hypothesis is longitudinal state maintenance; OCR and
  vision quality should not be the main source of benchmark error.

## 10. Runtime and provider boundary

The MVP is subscription-first. Blackhole should control an already-installed,
already-authenticated local agent CLI through a small provider adapter rather
than requiring a direct OpenAI or Anthropic API credential. The provider CLI owns
authentication; Blackhole must never request, read, copy, export, or persist
provider auth tokens.

At setup, Blackhole may detect supported local providers and show their safe
status. If a provider is missing or unauthenticated, it may show the external
login command (for example, `codex login` or `claude auth login`), but Blackhole
does not proxy that login flow. Codex CLI is the MVP evaluation provider; Claude
Code support may be a minimal adapter behind the same boundary.

The provider boundary may expose one-shot calls, persistent sessions, resume,
structured output, supported model/reasoning selection, cancellation and
timeouts, usage metadata, and raw trajectory capture. Runtime capability
detection is authoritative: unsupported model or reasoning combinations must be
reported rather than silently replaced.

### Deferred ingestion and freshness

The product-facing backend exposes a deferred ingestion service. `capture()` is
cheap and provider-independent. `process_pending()` claims pending captures in
sequence order, uses bounded batches, and runs the existing semantic extraction
and deterministic state pipeline. Processing status is derived operational
state, separate from raw source JSON, and records attempts, versions, success,
and retryable errors.

An Ask-like caller may call `ensure_state_fresh()` before reading structured
state. For the MVP this processes all pending captures when any exist; it does
not add a scheduler or require every future query to process everything. A
failed batch stops later chronological work, preserves the previously valid
projection, and leaves failed captures available to `retry_failed()`.

Semantic detection of a payment, cancellation, signing, sending, or account
change creates only a proposed derived action. The runtime never executes the
consequential action without explicit user approval.

## 11. Non-goals for the initial product

- A fully autonomous personal assistant that acts without approval.
- A replacement for accounting, legal, tax, medical, or financial professionals.
- A requirement that users maintain folders, tags, or a taxonomy.
- Silent cleanup or deletion of source material.
- Treating every captured item as a task or notification.
- Using an LLM as the authoritative calculator or ledger.
- Diagnosing, treating, or improving ADHD or another medical condition.

## 12. Open product questions

- What is the smallest useful attention unit: a fact, conflict, obligation,
  deadline, or proposed action?
- How should the product rank attention without equating uncertainty with
  urgency?
- Which corrections should be user-confirmed, and which can be safely
  re-derived?
- What retention and export controls are required for sensitive raw sources?
- Which slices of the benchmark best represent real capture friction and
  downstream trust?

## 13. Post-evaluation Product V2 runtime foundation

Product V2 is the open-world product runtime built after the evaluated V1
boundary. It is isolated in its own worktree and branch and must not be used
to tune, rewrite, or replace the frozen V1R1 benchmark, baseline, evaluator,
calibration evidence, or reported results.

### Capture and processing

Capture is nonblocking and provider-independent. Text-only, attachment-only,
and combined captures append one immutable source event and return `Saved.`
before semantic work. A durable pending row records processing separately from
raw evidence. A background worker or explicit process command claims events in
chronological order with a lease, recovers stale owners, retries failures with
bounded backoff, and commits normalized semantics and rebuilt projections in a
single transaction. A failure never discards the source or silently skips an
earlier event.

### Open-world memory

The V2 contract accepts generic entities, facts, events, tasks, deadlines,
relations, documents, transactions, observations, and proposed actions. It
does not require a predefined benchmark ontology. Every value is explicitly
`known`, `inferred`, or `unknown`; corrections, contradictions, supersession,
duplicates, and provenance references remain visible. Derived state is
rebuildable and raw evidence is never rewritten.

### Attention and Ask

Attention is a deterministic projection of tasks, obligations, deadlines,
unknowns, changes, conflicts, and proposed actions. Relative dates are
interpreted with capture timezone/context, and upcoming/overdue status is
recomputed from the current clock. It does not make medical or ADHD claims.
Ask uses `POST /api/v2/ask` and bounded retrieval over processed state rather
than replaying the complete history. Cost totals, date comparisons, upcoming
work, recent changes, and last-mention lookups use deterministic code. Only
bounded synthesis questions may invoke the local Codex CLI, and references
must point to known stored evidence.

#### Language invariance

Language is presentation, not memory structure. The language of a capture must
not determine whether that memory can be represented or retrieved later. A
semantic provider may preserve the source label for display while assigning a
stable, language-neutral entity key and semantic concept; the runtime keeps the
raw capture, names, Unicode, numbers, currencies, dates, times, units, and
filenames intact as evidence. Derived state remains rebuildable and provenance
remains attached to the source.

Captures and Ask questions may use different languages. The runtime may use
small lexical rules as bounded fast paths, but those rules are not the product's
language capability boundary. If a question is mixed, unfamiliar, or cannot be
resolved safely by the fast path, Ask passes a bounded candidate set of
structured current facts and related state to the general semantic provider
instead of returning `no_match` solely because surface languages differ. The
provider is instructed to answer in the current question's language and to
return explicit IDs for only the supplied evidence items that materially
support the rendered answer; the runtime maps those IDs back to source
references. This is a bounded generalization mechanism, not a claim of
universal language identification or equal answer quality for every language.

For provider-backed Ask, retrieval candidates and answer-supporting evidence
are separate contracts. Each bounded candidate receives a typed internal
`evidence_id`; the provider must select those IDs, and the runtime validates
them against the exact context before deriving public `source_refs`. Provider
source-reference lists cannot broaden the answer, and invalid-only selections
fail closed without fabricated provenance. Deterministic current, history,
correction, contradiction, and Attention answers continue to derive
provenance from the items they render.

### Attachments and retraction

Attachment bytes are stored as verified content-addressed blobs inside
Blackhole Home. The event records filename, MIME type, length, SHA-256, and
the blob link. Text content, attachment-only content, and combined content are
valid inputs. The local Python boundary accepts a file path; the HTTP boundary
requires bounded base64 bytes so a request cannot make the host read an
arbitrary server path. The runtime reports whether an attachment was unread, read,
unsupported, or unreadable; it makes no blanket OCR or vision-quality claim.
Retraction is an append-only semantic operation. It excludes the selected
source from active derived state while retaining the raw bytes, source event,
history, and provenance for rebuild and audit.

The initial V2 implementation is backend/API and deterministic-test focused.
It does not claim completion of a redesigned PWA surface, production hosting,
remote access, multi-user isolation, OCR, a Claude adapter, or consequential
action execution.
