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

## D-009 — Calibrate benchmark length before freezing Gate A

- **Status:** Proposed for Gate A review
- **Context:** A short timeline may fail to expose longitudinal state-maintenance errors in a strong long-context model, while an oversized timeline can measure context exhaustion rather than state quality.
- **Decision:** Before freezing the final benchmark length, run a separate non-scored calibration with 50-, 100-, 200-, and 400-event prefixes. Keep ten evolving storylines and prioritize state churn—updates, corrections, contradictions, supersession, cancellations, missing periods, duplicates, and ambiguity—over raw event count. Prefer the smallest approximately 150–200-event primary that shows repeatable degradation while remaining within usable context and the hackathon budget; keep a larger track secondary.
- **Consequences:** Calibration artifacts and a visible calibration-only oracle may be stored under `benchmark/calibration/`, but they are not final ground truth and cannot tune the baseline prompt. The selected model, tokenizer, context limit, correctness readout, runtime, and cost must be recorded before Gate A freeze.
- **Revisit when:** The fixed-prompt calibration shows no meaningful degradation through 400 events, the selected model/context changes, or the human owner approves a different primary/stress policy.

## D-010 — Blackhole framing and low-friction interaction

- **Status:** Accepted for design
- **Context:** Traditional productivity tools can turn capture into a second organizational task, especially for people with high executive-function friction, attention overload, forgetfulness, or low tolerance for setup.
- **Decision:** Use the product name **Blackhole** with the descriptor **“A zero-organization life inbox.”** The product principle is **CAPTURE NOW. ORGANIZE LATER.** Normal capture should be silent by default; interruption is reserved for useful attention items; observations should be factual and non-judgmental. ADHD may be referenced as an example of user need, without medical claims or treatment/diagnosis language.
- **Consequences:** The capture path should minimize classification questions and properties. Attention ranking, reminders, and advice must be evaluated for usefulness and tone rather than volume. Existing repository paths are not renamed for branding.
- **Revisit when:** User research shows that a different framing reduces capture friction without adding organizational overhead or making unsupported medical claims.

## D-011 — Isolate state maintenance from OCR in the primary benchmark

- **Status:** Proposed for Gate A review
- **Context:** The main hypothesis concerns longitudinal state maintenance, not the quality of an OCR or vision subsystem.
- **Decision:** Represent receipt, document, and image-derived modalities with synthetic text or normalized extracted content in the primary benchmark. Real uploads may be demonstrated separately; OCR/vision errors are not a primary benchmark confound.
- **Consequences:** Benchmark failures are more attributable to state changes, provenance, uncertainty, linking, temporal reconciliation, and projections. A separate modality slice can be added later without changing the primary metric.
- **Revisit when:** A validated modality pipeline becomes part of the product hypothesis and can be evaluated without masking state-maintenance behavior.

## D-012 — Use unweighted per-query LQA-0M with false-positive penalties

- **Status:** Proposed for Gate A review
- **Context:** Weighting critical assertions inside the primary average can make the headline score depend on arbitrary category weights, while unsupported assertions need an explicit penalty.
- **Decision:** For each fixed query, compute `TP`, `FP`, and `FN` over canonical assertions and use `TP / (TP + FP + FN)`. If both expected and produced assertion sets are empty, the query score is `1.0`; if only one is empty, the non-empty side creates false positives or false negatives and the score is `0.0`. LQA-0M is the unweighted arithmetic mean of all fixed query scores across primary checkpoints. Critical categories and safety violations are reported separately.
- **Consequences:** Hallucinated or unsupported claims lower the primary score. Precision, recall, and F1 remain useful diagnostics, but arbitrary 2:1 primary weights are removed.
- **Revisit when:** Human review identifies a deterministic, non-arbitrary aggregation rule that better reflects user risk without hiding false assertions.

## D-013 — Use DSCR for zero-maintenance correction burden

- **Status:** Proposed for Gate A review
- **Context:** A minimum-repair optimization such as MIR-90 is too expensive for the hackathon and can overstate repeated query failures caused by one root defect.
- **Decision:** Use **Distinct State Corrections Required (DSCR)**: after the zero-maintenance run, count distinct underlying state defects a human would need to correct. Multiple query failures caused by one defect count once. Report total DSCR, DSCR per 100 captured events, and correction categories. Do not equate DSCR with human minutes.
- **Consequences:** The secondary metric focuses on persistent state quality and is feasible to adjudicate. Exploratory wall-clock maintenance time may be reported separately but is not the contract metric.
- **Revisit when:** A later evaluation can measure actual maintenance effort reproducibly without replacing root-defect accounting.

## D-014 — Freeze a fair exact-model long-chat baseline

- **Status:** Proposed for Gate A review
- **Context:** The advanced system's structured state, deterministic tools, and retrieval are intentional experimental treatments; weakening the comparison baseline would invalidate the comparison.
- **Decision:** The baseline is one continuous general-purpose AI conversation receiving the same chronological captures and fixed checkpoint questions, with complete history whenever it fits and one frozen reasonable personal-life-admin prompt. Use the same exact semantic runtime model for baseline and advanced calls where practical, not merely the same model family. The baseline receives no hidden state, database, summary, retrieval, or specialized reconciliation tool.
- **Consequences:** Resource, token, latency, and cost differences must be reported transparently. The baseline prompt is frozen before calibration and cannot be tuned against individual calibration failures.
- **Revisit when:** The exact model is technically unavailable to both systems or a human-approved fairness protocol changes the treatment comparison.

## D-015 — Generate final benchmark state from a deterministic synthetic world

- **Status:** Proposed for Gate A review
- **Context:** Manually authoring and checking hundreds of final assertions is error-prone and burdens the human owner.
- **Decision:** Author final cases from explicit storyline/state-machine rules: canonical hidden world state → chronological user-facing events → deterministic checkpoint ground truth. Human review focuses on storyline semantics, transition rules, query definitions, subjective inference rules, critical transitions, and explicit unknown/contradiction cases. The implementation agent must not access protected holdout ground truth.
- **Consequences:** Final case generation is reproducible and easier to audit. Subjective expectations still require human adjudication, and generated development data must remain separate from evaluator-owned holdout material.
- **Revisit when:** A hand-authored case demonstrates a material behavior that cannot be represented transparently by the synthetic-world rules.
