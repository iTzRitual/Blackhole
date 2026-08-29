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

## 2. Provider and runtime boundary

The MVP runtime is subscription-first. Blackhole controls an already-installed,
already-authenticated local agent CLI through a provider adapter; the CLI owns
authentication. Blackhole never requests, reads, copies, exports, or persists
provider auth tokens. A missing or unauthenticated provider is a setup/status
condition, not a login flow that Blackhole proxies.

The smallest useful provider-agnostic interface is conceptual rather than an
implementation commitment:

| Capability | Provider boundary responsibility |
| --- | --- |
| Detection/discovery | Report whether a provider is supported and locate its executable |
| Auth/status | Return safe status metadata without exposing credentials |
| Capabilities | Report supported modes, models, reasoning controls, structured output, sessions, and usage fields |
| One-shot execution | Run one non-interactive request with timeout and cancellation handles |
| Persistent execution | Start a provider-owned session and send an ordered request |
| Resume | Continue a known session by provider session/thread identifier |
| Configuration | Select only provider-advertised model and reasoning values; reject unsupported combinations explicitly |
| Results | Return structured output, usage metadata when exposed, and a raw trajectory reference |

Codex CLI is the MVP provider and Claude Code is a minimal adapter target. The
interface must not grow a provider-neutral abstraction for capabilities that no
provider exposes. Runtime detection is authoritative, and a configuration
failure must not silently fall back to another model or provider.

### Runtime roles

The fair long-chat baseline uses one real persistent provider session for
chronological ingestion. At each approved checkpoint, the harness forks that
canonical session, asks the fixed read-only query bundle in the fork, records the
answer, and never resumes the fork. The canonical parent receives only later
capture batches. This prevents query answers from becoming unapproved memory for
later checkpoints while preserving the long-chat treatment. It receives no
Blackhole database, hidden summary, retrieval layer, or specialized
state-maintenance tool.

The future advanced system must not use one long provider session as its primary
memory. Blackhole owns durable memory and derived state. It should retrieve a
narrow relevant slice, make a fresh or deliberately scoped semantic provider
call, validate and reconcile the candidate deterministically, and persist the
result in rebuildable state. This keeps provider reasoning separate from
longitudinal truth maintenance.

## 3. Logical layers

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

## 4. State semantics

Every important field or conclusion should be able to distinguish at least:

| State | Meaning | Required behavior |
| --- | --- | --- |
| Known | Directly supported by source evidence or explicit confirmation | Preserve evidence and provenance |
| Inferred | Proposed from interpretation, linking, or rules | Keep uncertainty visible and make it revisable |
| Unknown | Missing, unreadable, ambiguous, conflicting, or unchecked | Do not coerce to zero, false, empty, or complete |

Conflicting known observations should remain conflict-bearing until resolved; the newest observation is not automatically the correct one.

## 5. Rebuild model

A rebuild should be able to:

1. select an immutable source snapshot;
2. identify the versions of prompts, models, parsers, rules, and schemas;
3. rerun interpretation and deterministic projections;
4. compare the resulting derived state with a prior run; and
5. explain any changed fact, obligation, aggregate, or attention item.

Manual user decisions may influence a later rebuild, but those decisions need their own immutable audit record and must not rewrite the original source.

## 6. Safety boundaries

- Source records are read-only after capture.
- Derived records are replaceable only through a traceable, versioned rebuild or an explicit user decision.
- Consequential actions are separate from interpretation and require explicit approval.
- External side effects must be auditable and attributable to a user approval event.
- Sensitive source content should be exposed only to components that need it.
- Evaluation ground truth is outside the implementation-agent trust boundary.

## 7. Failure modes to design for

- OCR or parsing produces a plausible but wrong value.
- Two sources refer to the same entity but use different names.
- A source is missing a field that looks numerically complete.
- A contract or subscription changes between observations.
- A duplicate is mistaken for a change, or a change for a duplicate.
- A stale derived item remains visible after its evidence changes.
- An agent emits a confident answer where the correct state is unknown.
- A proposed action is mistaken for an approved action.

## 8. Deliberately open implementation choices

- event log versus relational source tables;
- object storage and document extraction approach;
- entity-linking strategy;
- model and prompt versioning format;
- materialized versus on-demand projections; and
- user-interface representation of evidence and uncertainty.

These choices should be evaluated against the invariants above rather than treated as defaults.

## 9. Benchmark-only execution boundary

The current benchmark harness is not the product architecture. It creates an
empty temporary provider workspace, sends only the frozen runtime prompt and
public chronological captures, and records provider usage and model responses.
The deterministic development evaluator separately reads the public expected
output; the provider baseline never receives it. The harness has no durable
Blackhole state and performs no external action.

The prior execution used a 200-event, ten-storyline synthetic timeline with
checkpoints at 50, 100, 150, and 200. That package is historical draft evidence
while Gate A is reopened. The active design proposal recommends a 100-event,
ten-storyline primary with checkpoints at 20, 40, 60, 80, and 100, plus an
optional separate stress track. See [`docs/GATE_A_PROPOSAL.md`](GATE_A_PROPOSAL.md)
before changing benchmark artifacts. This separation lets future application
work demonstrate rebuildable state maintenance without changing the fair
baseline treatment.
