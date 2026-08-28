# Product specification

**Product:** Life Inbox
**Status:** Design scaffold
**Audience:** Product, engineering, evaluation, and agent-workflow contributors

## 1. Product intent

Life Inbox is a zero-organization personal inbox. It gives a user one low-friction place to capture fragments of everyday life without requiring classification, folder selection, tagging, or a decision about what the fragment means.

The product earns its value later by turning those fragments into an understandable, persistent picture of facts, entities, obligations, deadlines, changes, and items requiring attention.

## 2. User problem

Everyday information arrives in forms that do not fit a single organizing system: a quick thought, a photographed receipt, a contract PDF, a subscription renewal, a task mentioned in a message, or a financial observation. Requiring organization at capture time causes delay, omission, and premature decisions.

The product should defer organization while preserving enough evidence to support trustworthy interpretation later.

## 3. Primary user job

> “Let me put this somewhere safe now, and help me understand what it means when I have the attention to deal with it.”

## 4. Supported capture categories

The initial concept covers:

- short text and free-form notes;
- receipts and other images;
- documents;
- tasks and reminders;
- subscriptions;
- contracts and agreements; and
- financial observations.

These are examples of source material, not a classification burden imposed on the user.

## 5. Desired system responsibilities

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

## 6. Information semantics

### Known

Information directly supported by an available source or by an explicit user confirmation. The evidence and extraction path should be visible to the system and, where useful, to the user.

### Inferred

A hypothesis or interpretation derived from one or more sources. It must remain distinguishable from a directly observed fact, carry its provenance, and be revisable when new evidence arrives.

### Unknown

Information that is missing, unreadable, ambiguous, conflicting, or not yet checked. Unknown must remain unknown. In particular, absence of a value does not imply zero, false, “none,” or completion.

## 7. User experience principles

- Capture first; organization is optional at capture time.
- Show why a derived item exists and which source supports it.
- Make uncertainty and conflicts visible without overwhelming the user.
- Surface attention-worthy items rather than producing an undifferentiated stream of notifications.
- Ask for confirmation at consequential boundaries.
- Allow the user to correct interpretations without damaging source evidence.

## 8. Safety and trust requirements

- Original source content is immutable.
- Derived state can be rebuilt when extraction, prompts, models, or rules change.
- Arithmetic and other deterministic transformations have an executable source of truth.
- The system does not autonomously send, pay, cancel, sign, delete, or otherwise cause a consequential external effect.
- Financial and contractual information is presented as extracted or inferred information, not as professional advice.
- Sensitive content is handled with least-necessary exposure and explicit retention decisions.

## 9. Non-goals for the initial product

- A fully autonomous personal assistant that acts without approval.
- A replacement for accounting, legal, tax, or financial professionals.
- A requirement that users maintain folders, tags, or a taxonomy.
- Silent cleanup or deletion of source material.
- Treating every captured item as a task or notification.
- Using an LLM as the authoritative calculator or ledger.

## 10. Open product questions

- What is the smallest useful attention unit: a fact, conflict, obligation, deadline, or proposed action?
- How should the product rank attention without equating uncertainty with urgency?
- Which corrections should be user-confirmed, and which can be safely re-derived?
- What retention and export controls are required for sensitive raw sources?
- Which slices of the benchmark best represent real capture friction and downstream trust?
