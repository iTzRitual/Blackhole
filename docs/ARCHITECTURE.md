# Conceptual architecture

This document describes boundaries and invariants, not an implementation stack. The architecture is intentionally specific about trust boundaries and intentionally open about frameworks, storage engines, and model providers.

## 1. Conceptual flow

```text
capture inputs
      |
      v
immutable source records  --->  source evidence / provenance
      |
      v
versioned interpretation and linking
      |
      v
canonical facts, entities, relationships, and state
      |
      +--> tasks and obligations
      +--> deadlines and changes
      +--> duplicate findings
      +--> deterministic financial projections
      +--> attention projection
      |
      v
user review, correction, and explicit approval
```

The arrows describe derivation, not destructive movement. A later stage must be able to point back to the source and the transformation that produced it.

## 2. Logical layers

### Source layer

Stores the original capture and minimal capture metadata. Source content is immutable. A new upload, replacement, correction, or user clarification is a new source or event rather than an in-place rewrite.

### Interpretation layer

Extracts candidate facts, classifications, entity links, dates, amounts, and obligations. Model outputs are proposals or derived records, never replacements for the source. Each output needs transformation and provenance metadata.

### State layer

Maintains the current derived view of entities, relationships, obligations, deadlines, subscriptions, contracts, and financial observations. State is rebuildable and should retain enough history to explain changes over time.

### Deterministic projection layer

Computes arithmetic, date relationships, duplicate comparisons, totals, changes, and other rule-governed results. Code or SQL is authoritative for these calculations. An LLM can help identify inputs or explain a result but cannot be the calculation authority.

### Attention and interaction layer

Projects the derived state into items requiring review, clarification, confirmation, or action. Attention is not a second source of truth. Hiding or resolving an attention item must not erase its evidence.

## 3. State semantics

Every important field or conclusion should be able to distinguish at least:

| State | Meaning | Required behavior |
| --- | --- | --- |
| Known | Directly supported by source evidence or explicit confirmation | Preserve evidence and provenance |
| Inferred | Proposed from interpretation, linking, or rules | Keep uncertainty visible and make it revisable |
| Unknown | Missing, unreadable, ambiguous, conflicting, or unchecked | Do not coerce to zero, false, empty, or complete |

Conflicting known observations should remain conflict-bearing until resolved; the newest observation is not automatically the correct one.

## 4. Rebuild model

A rebuild should be able to:

1. select an immutable source snapshot;
2. identify the versions of prompts, models, parsers, rules, and schemas;
3. rerun interpretation and deterministic projections;
4. compare the resulting derived state with a prior run; and
5. explain any changed fact, obligation, aggregate, or attention item.

Manual user decisions may influence a later rebuild, but those decisions need their own immutable audit record and must not rewrite the original source.

## 5. Safety boundaries

- Source records are read-only after capture.
- Derived records are replaceable only through a traceable, versioned rebuild or an explicit user decision.
- Consequential actions are separate from interpretation and require explicit approval.
- External side effects must be auditable and attributable to a user approval event.
- Sensitive source content should be exposed only to components that need it.
- Evaluation ground truth is outside the implementation-agent trust boundary.

## 6. Failure modes to design for

- OCR or parsing produces a plausible but wrong value.
- Two sources refer to the same entity but use different names.
- A source is missing a field that looks numerically complete.
- A contract or subscription changes between observations.
- A duplicate is mistaken for a change, or a change for a duplicate.
- A stale derived item remains visible after its evidence changes.
- An agent emits a confident answer where the correct state is unknown.
- A proposed action is mistaken for an approved action.

## 7. Deliberately open implementation choices

- event log versus relational source tables;
- object storage and document extraction approach;
- entity-linking strategy;
- model and prompt versioning format;
- materialized versus on-demand projections; and
- user-interface representation of evidence and uncertainty.

These choices should be evaluated against the invariants above rather than treated as defaults.
