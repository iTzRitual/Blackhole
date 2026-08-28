# Architecture and product decisions

This is a lightweight decision record. Each entry captures the current design direction, why it exists, and what would justify revisiting it.

## Decision format

- **Status:** Proposed, accepted for design, or superseded
- **Context:** The problem or constraint
- **Decision:** The chosen direction
- **Consequences:** Benefits, costs, and risks
- **Revisit when:** Evidence that should trigger reconsideration

## D-001 — Zero-organization capture

- **Status:** Accepted for design
- **Context:** Classification at capture time creates cognitive friction and causes information loss.
- **Decision:** Provide a single capture path for supported source types. Classification is deferred to later processing.
- **Consequences:** The system must invest in extraction, linking, uncertainty handling, and review. Capture remains fast and inclusive.
- **Revisit when:** Evidence shows that a narrowly scoped capture choice materially improves trust or accuracy without adding meaningful friction.

## D-002 — Immutable raw sources

- **Status:** Accepted for design
- **Context:** Users and evaluators need to distinguish what was originally captured from what the system later inferred or corrected.
- **Decision:** Raw source records are append-only and immutable. Corrections and derived interpretations are separate records.
- **Consequences:** Storage and provenance are more important. Destructive cleanup cannot be the default.
- **Revisit when:** A formally versioned replacement mechanism can preserve complete evidence and auditability without mutating history.

## D-003 — Rebuildable derived state

- **Status:** Accepted for design
- **Context:** Prompts, models, extraction rules, and schemas will evolve.
- **Decision:** Derived state must be reproducible from immutable sources plus versioned transformations.
- **Consequences:** Every transformation needs identifiable inputs and versions. Ad hoc manual state changes require explicit provenance.
- **Revisit when:** A specific state category can be proven to require an irreducible manual component, while retaining a clear audit trail.

## D-004 — Explicit known, inferred, and unknown semantics

- **Status:** Accepted for design
- **Context:** Silent assumptions make personal and financial information unsafe.
- **Decision:** Represent direct evidence, inference, and unresolved absence as distinct semantic states.
- **Consequences:** Interfaces and metrics must avoid collapsing uncertainty into binary fields or numeric defaults.
- **Revisit when:** A narrower domain-specific representation improves clarity without losing the distinction.

## D-005 — Deterministic calculations outside the LLM

- **Status:** Accepted for design
- **Context:** Arithmetic, date math, comparisons, and aggregation must be repeatable and auditable.
- **Decision:** Code or SQL is the source of truth for deterministic calculations. The LLM may extract inputs, explain results, or propose classifications.
- **Consequences:** Calculation inputs need validation and provenance. Evaluation can separate extraction errors from calculation errors.
- **Revisit when:** Never for authoritative calculations; model assistance may expand only for non-authoritative explanation or hypothesis generation.

## D-006 — Explicit approval for consequential actions

- **Status:** Accepted for design
- **Context:** A wrong inference about a contract, payment, cancellation, or message can cause harm.
- **Decision:** The system may prepare a proposed action, but a user must explicitly approve a consequential external effect.
- **Consequences:** Approval state, preview, and audit records become first-class concerns.
- **Revisit when:** A narrowly scoped action has a documented safety case and an explicit product decision authorizes automation.

## D-007 — Evaluator-owned holdout ground truth

- **Status:** Accepted for design
- **Context:** An implementation agent that can read expected holdout outputs can optimize against or leak the benchmark.
- **Decision:** Holdout cases and expected outputs are evaluator-controlled. The implementation-facing repository contains placeholders only; real holdout material should be mounted or queried through an isolated evaluation boundary.
- **Consequences:** Evaluation tooling must separate candidate outputs from scoring data and must audit access.
- **Revisit when:** A different evaluation protocol provides equal or stronger protection against contamination.

## D-008 — Attention is a derived projection, not the source of truth

- **Status:** Accepted for design
- **Context:** Users need focus, but an attention list can become stale or hide its evidence.
- **Decision:** Attention items are rebuildable projections over facts, uncertainty, obligations, deadlines, conflicts, and approvals.
- **Consequences:** An item leaving the attention view does not delete the underlying evidence or state.
- **Revisit when:** User research demonstrates a durable need for a manually managed attention state, with provenance preserved.
