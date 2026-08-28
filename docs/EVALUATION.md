# Evaluation plan

**Status:** Proposed benchmark contract, pending human review

This document defines what a trustworthy Life Inbox system should demonstrate and proposes a concrete benchmark contract. It is design-only: no benchmark cases, expected outputs, scorer, or evaluator implementation is included.

## 1. Evaluation goals

Measure whether the system can turn low-friction captures into useful, evidence-backed derived state while preserving uncertainty and safety. Evaluation must distinguish failures of capture preservation, interpretation, deterministic computation, attention ranking, and action control.

## 2. Evaluation dimensions

| Dimension | Example question |
| --- | --- |
| Source fidelity | Was the original input preserved without mutation or loss? |
| Extraction | Were facts, dates, amounts, parties, and terms extracted correctly? |
| Classification | Was the input assigned useful categories without requiring user pre-classification? |
| Entity linking | Were references linked to the correct existing entity, or left unresolved when ambiguous? |
| Temporal state | Were deadlines, renewals, changes, and historical observations represented correctly? |
| Obligations | Were tasks and obligations identified without inventing commitments? |
| Duplicate/change detection | Were repeated observations distinguished from meaningful changes? |
| Financial computation | Are totals, comparisons, and aggregates deterministic and correct? |
| Uncertainty | Are known, inferred, and unknown states kept distinct and calibrated? |
| Attention quality | Does the system surface items requiring attention without noisy over-alerting? |
| Safety | Are consequential actions blocked until explicit approval? |
| Rebuildability | Can derived state be regenerated and explained from versioned inputs? |

## 3. Dataset split and access

The development set may be used for iteration and debugging. The holdout set is evaluator-owned and must not expose expected outputs to the implementation agent. The current repository contains no benchmark cases or ground truth in either split.

Scoring should happen outside the implementation agent's trust boundary. Candidate outputs may be submitted to an evaluator, but scoring data and expected outputs must not be returned as debugging content.

## 4. Suggested metric families

- Exact or normalized accuracy for directly extractable fields.
- Precision, recall, and F-score for classifications, links, obligations, and duplicate/change findings.
- Calibration or selective-accuracy measures for known versus inferred versus unknown.
- Error in deterministic aggregates, with explicit handling for missing values and units.
- Deadline and temporal relation accuracy, including timezone and ambiguity cases.
- Attention precision, coverage of high-priority items, and unnecessary-alert rate.
- Safety violation count, with any unapproved consequential action treated as a critical failure.
- Rebuild consistency across repeated runs with the same versioned inputs.

The final metric definitions, tolerances, and weighting should be frozen before holdout evaluation.

## 5. Important test slices

Include cases with:

- incomplete receipts and documents;
- conflicting observations;
- ambiguous entity names;
- recurring subscriptions and changed prices;
- contracts with multiple dates or conditional obligations;
- currency, tax, units, and rounding variation;
- duplicate-looking captures that contain a meaningful change;
- genuinely unknown values;
- distractors that should not create attention items; and
- proposals that must not become actions without approval.

## 6. Failure classification

Every failed case should be assigned a primary cause where possible:

1. source preservation failure;
2. extraction or parsing failure;
3. classification failure;
4. entity-linking failure;
5. temporal or obligation reasoning failure;
6. deterministic calculation failure;
7. uncertainty or calibration failure;
8. attention ranking failure;
9. provenance or rebuild failure; or
10. safety boundary failure.

This taxonomy supports the improvement changelog and prevents a single aggregate score from hiding serious safety regressions.

## 7. Evaluation record requirements

Each run should record the code revision, prompt revisions, model identifiers, dataset split and manifest, configuration, environment, random seeds, timezone, scoring version, and artifact locations. See [REPRODUCTION.md](REPRODUCTION.md).

## 8. Proposed benchmark contract

The following contract is a proposal for human review. It is not frozen, and this task creates no benchmark cases.

### 8.1 Exact unit of evaluation

The benchmark unit is one **scenario**: an isolated, ordered inbox history for one synthetic person, together with the public context available to the system and a fixed cutoff time. A scenario is processed independently; state must not leak between scenarios.

The scenario is scored through **typed atomic state assertions**. An assertion is the smallest claim that can be independently correct or incorrect, such as one entity link, one field value, one task lifecycle state, one duplicate relation, or one explicit unknown. The reported primary score is a macro-average of scenario scores so a long scenario cannot dominate the benchmark merely by containing more assertions.

### 8.2 Primary metric

The primary metric is **Macro Evidence-State F1 (MES-F1)**.

For each scenario, the evaluator compares the candidate and expected sets of canonical assertions. A match requires the same assertion kind, subject or record key, field or relation, normalized value (or explicit unknown), and `knowledge_status`. For `known` and `inferred` assertions, the candidate must include the required supporting source references or confirmation reference. Unknown assertions must include the expected reason category.

For scenario `s`:

```text
precision_s = TP_s / (TP_s + FP_s)
recall_s    = TP_s / (TP_s + FN_s)
F1_s        = 2 * TP_s / (2 * TP_s + FP_s + FN_s)
MES-F1      = mean(F1_s for all scored scenarios)
```

All expected assertions, including required unknowns, count toward recall. Unsupported candidate assertions count as false positives. A run with an unapproved consequential side effect fails the safety gate regardless of its MES-F1 score.

### 8.3 Secondary metrics

The evaluator should report, without replacing MES-F1:

- micro Evidence-State F1 across all assertions;
- per-type F1 for facts, classifications, entity links, tasks, obligations, deadlines, financial observations, financial aggregates, duplicate/change relations, corrections, contradictions, and attention items;
- value-only extraction accuracy versus full value-plus-status accuracy;
- known/inferred/unknown precision, recall, and calibration;
- provenance and required-source-reference precision/recall;
- source-fidelity and raw-payload integrity failures;
- entity-linking accuracy, including correct unresolved decisions;
- task, obligation, and deadline precision/recall with temporal accuracy;
- exact financial-observation accuracy and deterministic aggregate error;
- duplicate, meaningful-change, and correction precision/recall;
- contradiction detection and contradiction-preservation scores;
- attention precision, attention coverage, and unnecessary-alert rate;
- rebuild consistency for identical versioned inputs;
- schema-validity and malformed-output rate;
- safety violation count; and
- runtime, token/call count, and cost when available.

### 8.4 Structure of one benchmark scenario

The implementation-facing scenario package has this conceptual shape:

```json
{
  "contract_version": "0.1-proposed",
  "scenario_id": "<scenario identifier>",
  "cutoff_at": "<ISO-8601 timestamp>",
  "timezone": "<IANA timezone>",
  "initial_context": {
    "entities": [],
    "accepted_state": []
  },
  "raw_events": [
    {
      "event_id": "<event identifier>",
      "sequence": 1,
      "captured_at": "<ISO-8601 timestamp>",
      "observed_at": "<optional ISO-8601 timestamp>",
      "source_type": "text|image|document|record",
      "payload": "<inline content or content reference>",
      "payload_sha256": "<hash of immutable payload>",
      "metadata": {}
    }
  ],
  "allowed_side_effects": []
}
```

The private evaluator package adds the frozen expected final state, scorable-slot manifest, and scoring metadata. Those fields are never supplied to the implementation agent. The candidate response uses the same scenario identifier and contains a `final_state` plus any proposed actions; it must not claim an external action was executed without an explicit approval record.

A scenario should contain enough ordered evidence to test state over time, such as a first observation, a repeated or changed observation, a missing field, an ambiguity, or an explicit correction. It should not require cross-scenario memory.

### 8.5 Representation contract

#### Common assertion envelope

Every scorable value uses a common semantic envelope:

```json
{
  "knowledge_status": "known|inferred|unknown",
  "value": "<structured value; omitted when unknown>",
  "source_refs": ["<event or state reference>"],
  "confirmation_ref": "<optional explicit user confirmation>",
  "unknown_reason": "missing|unreadable|ambiguous|conflicting|not_checked"
}
```

`value` is required for `known` and `inferred` assertions and must be omitted for `unknown`. `source_refs` are required for derived assertions; an explicit confirmation may additionally or alternatively be cited where the contract allows it. `unknown_reason` is required only for `unknown`. Confidence may be recorded for analysis, but it does not turn an inference into a known fact.

#### Raw events

Raw events are append-only source records. They contain a stable `event_id`, sequence position, capture time, optional observed time, source type, original payload or content reference, immutable payload hash, and minimal metadata. Missing source metadata remains missing; it is not filled with a semantic default. A correction or replacement is a new event or derived correction record and never mutates the original payload.

#### Expected final state

The expected state is a private, normalized collection of typed records evaluated as atomic assertions. It includes all scorable slots for the scenario, including slots whose correct result is explicit `unknown`. It may contain `entities`, `facts`, `entity_links`, `tasks`, `obligations`, `deadlines`, `financial_observations`, `financial_aggregates`, `duplicate_relations`, `corrections`, `contradictions`, and `attention_items`.

Existing entity identifiers supplied in `initial_context` are public and may be used for links. Newly introduced entities are matched by their scenario-local identity signature rather than by an opaque evaluator-only identifier.

#### Entity links

An entity link contains a source mention reference, a target existing entity reference or new-entity identity signature, a link state such as `linked` or `unresolved`, the common `knowledge_status`, and supporting references. An ambiguous mention is correctly represented as `unknown`/`unresolved`, not as a forced link.

#### Tasks

A task contains a stable task key, action or description, optional owner reference, lifecycle value such as `open`, `completed`, `cancelled`, or `blocked`, optional deadline reference, the common knowledge envelope for each uncertain field, and supporting references. A missing task state is not equivalent to completed.

#### Obligations

An obligation contains an obligation key, obligor, obligee, required action or condition, lifecycle state, trigger or recurrence when known, and supporting references. The benchmark distinguishes an obligation from a casual note or a proposed task.

#### Deadlines

A deadline contains a deadline key, target task/obligation/contract reference, due date or interval, declared date precision, timezone when applicable, and knowledge envelope. Date arithmetic and comparisons use the canonicalized timestamp or interval, not model prose.

#### Financial observations

A financial observation contains an observation key, subject or entity reference, exact decimal amount when available, ISO currency code, direction, occurrence time or period, category when supported, and provenance. Amounts are represented as decimal strings rather than binary floating-point values. A missing amount is an explicit unknown amount, never zero.

Deterministic financial aggregates, when included in a scenario, contain an aggregate key, a versioned expression identifier, exact decimal result or explicit unknown, currency, and coverage references. The evaluator computes the expected result with deterministic code or SQL.

#### Duplicates and meaningful changes

A duplicate relation contains two event references and a relation of `exact_duplicate`, `normalized_duplicate`, `meaningful_change`, `not_duplicate`, or `unknown`, plus changed fields when applicable, knowledge status, and evidence references. Duplicate detection must not erase either raw event.

#### Corrections

A correction contains a correction key, target assertion or record, changed fields, prior and replacement values when known, origin such as `user_confirmed` or `system_proposed`, effective time, knowledge status, and evidence references. The original source remains in the raw event set. A user-confirmed correction can make the replacement known; a system proposal remains inferred until confirmed.

#### Contradictions and attention items

A contradiction record identifies its member assertions, the conflicting field or relation, and a resolution state of `unresolved` or `resolved` with the relevant correction or confirmation reference. An attention item identifies the state or evidence needing review, its reason, and any urgency value supported by the contract. Attention is a projection and never replaces the underlying state.

### 8.6 Scoring algorithm

The deterministic scorer performs these steps:

1. Validate the scenario identifier, contract version, output envelope, and allowed field ontology.
2. Verify the input payload hashes before and after processing to detect raw-source mutation.
3. Canonicalize Unicode and whitespace for text keys, normalize timestamps to the scenario timezone while retaining declared precision, compare decimal values exactly, and treat set-like reference lists as order-independent.
4. Flatten expected and candidate final states into typed assertion sets. An assertion key includes its type, subject/record key, field or relation, and normalized value/status.
5. Match assertions one-to-one. Known and inferred assertions must satisfy required evidence-reference rules; unknown assertions must satisfy the reason rule.
6. Count unmatched candidate assertions as `FP` and unmatched expected assertions as `FN`. A malformed complete response scores zero for the scenario; malformed individual records are false positives and are also reported by the schema metric.
7. Compute scenario F1 and then the macro-average MES-F1. Produce the secondary metrics by the same canonicalized comparison.
8. Apply the safety gate: any unapproved send, payment, cancellation, signing, account change, deletion of evidence, or other consequential side effect marks the run as failed even if the state score is high.

No credit is given for persuasive prose outside the contract fields. The scorer is deterministic and must not use an LLM.

### 8.7 Missing information

The private expected state explicitly includes every required unknown slot. A candidate receives credit only for emitting `knowledge_status: "unknown"` with the correct reason category and no fabricated value.

- Omitting a required unknown is a false negative.
- Emitting zero, false, an empty string, `none`, or a guessed value for an unknown slot is a false positive and fails the missing-data safety check.
- A numeric zero receives credit only when it is explicitly supported or deterministically derived from supported inputs.
- A field outside the scenario’s published ontology is not an implicit unknown; unsupported candidate claims are false positives, while the evaluator’s scorable-slot manifest prevents hidden scoring requirements.

### 8.8 Contradictions

When two observations address the same canonical subject and field but disagree, the expected state records both evidence references and an explicit contradiction status. If the conflict is unresolved at the cutoff, the final field is expected to be `unknown` with reason `conflicting`, alongside the contradiction record.

If an explicit user correction resolves the conflict, the expected state contains the correction record and the corrected final value. The earlier raw observation remains present and is not scored as deleted.

Contradictions are scored through both the ordinary assertion F1 and the secondary contradiction-preservation metric. Collapsing an unresolved conflict into the newest value leaves the expected conflict/unknown assertions unmatched and the asserted value unsupported, producing both recall and precision loss. Reporting two incompatible values without a contradiction record is likewise unsupported output.

### 8.9 Holdout ground-truth protection

Development cases may eventually be committed after this contract is approved. Holdout cases and expected outputs must remain evaluator-owned:

- store holdout inputs and ground truth outside the implementation checkout, or in a separately permissioned evaluator repository;
- provide the implementation only the holdout input at evaluation time, never the expected state, slot manifest, labels, or scoring diagnostics;
- run the candidate and scorer as separate principals or sandboxes, with the scorer privately mounting expected outputs;
- expose only aggregate pass/fail and approved metrics to the implementation environment;
- prevent logs, exceptions, trajectories, prompts, cache files, and artifacts from echoing expected content;
- audit access and fail closed if implementation credentials can read the expected store; and
- never place holdout material, hashes that reveal labels, or derivative hints in development prompts or fixtures.

The current repository contains no benchmark cases or ground truth. The tracked holdout placeholders are directory markers only.

### 8.10 Reproduction by judges

Judges should be able to reproduce a run from:

- a frozen `contract_version` and scorer/normalization revision;
- a content-addressed public scenario manifest and, for authorized judges, the private holdout package;
- the candidate code revision, runtime and coding prompt revisions, model/provider versions, configuration, and tool versions;
- operating system, dependency/runtime versions, locale, timezone, random seed, and concurrency settings; and
- the candidate output artifact and evaluator result manifest.

The judge runner should provision a clean sandbox, provide one scenario at a time, capture the candidate output, verify raw-event hashes, and invoke the deterministic scorer with the private expected state. Re-running a deterministic transformation with the same versioned inputs must produce the same result. Any model nondeterminism must be recorded separately from deterministic scoring and financial calculations.

The reproduction record must contain identifiers and hashes rather than protected expected content. Future judge tooling may write authorized results under `eval/results/`, but no runner or evaluator implementation is part of this design task.

### 8.11 Review gate

After human approval, the contract should be assigned a frozen version, its normalization rules and weights should be locked, and only then should development scenarios and synthetic inputs be created. Holdout construction remains evaluator-owned. Until that approval, this section is a proposal only.
