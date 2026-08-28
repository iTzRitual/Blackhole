# Product specification

**Product:** Blackhole
**Descriptor:** A zero-organization life inbox.
**Status:** Design scaffold; Gate A pre-freeze
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

## 10. Non-goals for the initial product

- A fully autonomous personal assistant that acts without approval.
- A replacement for accounting, legal, tax, medical, or financial professionals.
- A requirement that users maintain folders, tags, or a taxonomy.
- Silent cleanup or deletion of source material.
- Treating every captured item as a task or notification.
- Using an LLM as the authoritative calculator or ledger.
- Diagnosing, treating, or improving ADHD or another medical condition.

## 11. Open product questions

- What is the smallest useful attention unit: a fact, conflict, obligation,
  deadline, or proposed action?
- How should the product rank attention without equating uncertainty with
  urgency?
- Which corrections should be user-confirmed, and which can be safely
  re-derived?
- What retention and export controls are required for sensitive raw sources?
- Which slices of the benchmark best represent real capture friction and
  downstream trust?
