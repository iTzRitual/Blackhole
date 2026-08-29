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

The approved primary is a 200-event, ten-storyline synthetic timeline with
checkpoints at 50, 100, 150, and 200. A 400-event run is optional and secondary.
This separation lets future application work demonstrate rebuildable state
maintenance without changing the fair baseline treatment.

## 10. Experiment 001 implementation slice

The first advanced experiment instantiates the smallest useful part of the
conceptual flow in `app/`:

```text
public captures
      |
      v
SQLite raw_events (immutable, hashed)
      |
      v
scoped semantic observations + relationships
      |
      v
deterministic rebuild_projection()
      |
      v
query-scoped public response projection
```

`app/state_store.py` keeps raw event JSON, payload hashes, observations,
relationships, projection runs, and current facts. SQLite triggers reject raw
updates and deletes. Rebuilds retain history and produce an input digest and
projection version; a contradiction remains `unknown` until a later explicit
correction or supersession relation resolves it.

`app/provider.py` uses the subscription-first local Codex CLI boundary and
does not access provider tokens. `app/advanced_runner.py` makes one fresh
semantic call per chronological batch and stores the raw provider output in a
runtime trajectory. `app/response_projector.py` performs query-specific
deterministic projections, including date windows, history traversal, duplicate
components, and Decimal-based financial aggregation. It selects subjects by
public ontology kind and routes query families without embedding benchmark
entity identifiers. A replay mode allows projection changes to be evaluated
from identical recorded extraction outputs.

The benchmark-facing experiment slice has no production infrastructure,
external-action executor, Claude adapter, or holdout access. The repository now
also includes the separate minimal local demo described in section 12; that UI
is a deterministic presentation of synthetic state, not a production service
or a replacement for the benchmark treatment. Its measured result is recorded
in `IMPROVEMENT_CHANGELOG.md` and the Experiment 001/002 coding and runtime
trajectories; the frozen benchmark and official baseline remain separate from
product memory.

## 11. Experiment 002 genericity repair

The follow-up audit removed named-subject coupling from the response projector.
Service and merchant calculations are grouped by each subject's public kind,
insurance and contract replacement detection is based on state transitions,
and duplicate/change capture filtering uses event observation semantics. An
entity-link-only event is not treated as receipt-like duplicate evidence merely
because it has a relationship edge.

The repair was replayed against the same recorded E001 semantic extraction and
the unchanged public evaluator. It preserved the full 200-event result exactly
(`LQA-0M=0.7492295899`, `DSCR=72`) and is recorded as experiment evidence, not
as a new benchmark or baseline treatment.

## 12. Minimal local demo

The repository now includes a deliberately small local demonstration of the
state boundary. It is a product slice, not production infrastructure:

```text
committed synthetic seed
        |
        v
SQLite raw_events (immutable, hashed)
        |
        v
seeded semantic observations + relationships
        |
        v
rebuild_projection()
        |
        v
structured attention, memory, and ask views
```

`app/demo.py` seeds 14 synthetic captures covering current and historical
subscription price, task reassignment and cancellation, an open deadline,
observed and missing service periods, a purchase, a duplicate, an explicit
unknown amount, and an unexecuted approval-gated action. `app/web_app.py` is a
stdlib HTTP server with fixed static routes and JSON endpoints for state,
queries, raw capture, and demo reset. The UI does not classify the capture or
invoke a provider in the request path; it reports that the capture was saved and
leaves its semantic status pending.

The `codex` status pill is discovery-only. The separate advanced runner remains
the subscription-first semantic runtime: an installed local CLI owns login and
authentication, while Blackhole never requests, reads, copies, exports, or
persists provider credentials. No endpoint performs a consequential external
action. The local demo database is ignored by Git and can be rebuilt with
`python scripts/seed_demo.py --reset`.

## 13. Experiment 003 relation reconciliation

Experiment 003 added a narrow reconciliation layer after each semantic
extraction batch:

```text
structured observations + model relations
                    |
                    v
       deterministic fallback recovery
                    |
                    v
 bounded raw candidates by primary identifier
                    |
                    v
      versioned derived relationship replacement
                    |
                    v
             rebuildable projection
```

`app/relation_recovery.py` first recovers only missing explicit
supersession/correction edges and duplicate-marked identical payload edges.
The retrieval treatment then considers only receipt-like relation sources with
one existing relation, extracts the first stable identifier, and returns no
more than four earlier raw candidates. Meaningful changes prefer the newest
non-duplicate candidate; duplicate and similarity edges prefer the newest
candidate. Relation type, changed fields, and duplicate-group details are
derived conservatively from the source wording and candidate content. A
provider resolver was not needed for the kept treatment.

`StateStore.replace_relationships_for_sources()` changes derived relationship
rows only; immutable raw events and structured observations remain intact. The
relationship replacement and projection versions are recorded in the runtime
trajectory, and each checkpoint has a retrieval record containing the bounded
candidate IDs, raw text, metadata, selected target, and replacement digest.
This preserves rebuildability because the runner can replay the same semantic
outputs and deterministic recovery rules without evaluator data.

The final public Experiment 003 replay improved from the kept Experiment 002
result of `LQA-0M=0.7492295899` / `DSCR=72` to
`LQA-0M=0.8157180034` / `DSCR=45`, while all other reported category metrics
remained unchanged, source integrity and safety passed, and provider usage was
zero. The result is development evidence only; Gate A, `response-contract-v2`,
the official baseline, calibration evidence, and holdout boundaries remain
unchanged.

## 14. Experiment 004 selective completeness treatment

Experiment 004 adds a narrow raw-source completeness pass after the existing
Experiment 003 relation-reconciliation pass and before the deterministic
projection is queried:

```text
immutable raw capture
          |
          v
generic structural anchors
          |
          v
same-event coverage gaps
          |
          v
deterministic derived completions
          |
          v
rebuildable projection
```

`app/completeness.py` scans raw text for structural dates, amounts/currencies,
conservative identifiers, and temporal/lifecycle/action cues. The scanner emits
evidence anchors only; it does not turn every number or date into a semantic
fact. The gap detector compares those anchors with observations from the same
capture and the current subject state. A completion is admitted only for a
generic, unambiguous mapping such as a contract identifier, an explicit signed
date, a monthly billing-period field, or a clearly stated lifecycle status.

Completions are derived observations with the original event as provenance and
are passed through the existing public-contract normalization. They never mutate
the raw event and do not alter Experiment 003 relationship reconciliation. The
optional verifier prompt is versioned and restricted to one raw capture, its
existing observations, structural anchors, public ontology/value shapes, and
relevant current subject facts. It was covered by neutral fixtures but was not
invoked in the kept replay because the deterministic treatment already met the
experiment threshold.

The full public replay scanned 200 captures, flagged 10, repaired 6 captures
deterministically, added 8 observations including 1 correction, and made zero
provider calls. It improved LQA-0M from `0.8157180034` to `0.8630770101` and
reduced DSCR from `45` to `41`. Raw sources, the frozen benchmark, evaluator,
official baseline, and holdout boundary remain unchanged.
