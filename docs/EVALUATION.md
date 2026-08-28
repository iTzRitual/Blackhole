# Evaluation plan

This document defines what a trustworthy Life Inbox system should demonstrate. It is a protocol scaffold, not an evaluation implementation.

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
