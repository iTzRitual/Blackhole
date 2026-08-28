# Benchmark boundary

This directory defines the intended boundary between development cases and evaluator-controlled holdout material. The Gate A benchmark contract proposal is documented in [docs/EVALUATION.md](../docs/EVALUATION.md#19-gate-a-pre-freeze-status) and is pending human review. The final event count is not frozen: the separate non-scored [size calibration](calibration/README.md) compares 50, 100, 200, and 400-event histories with high state churn. The intended primary remains approximately 150–200 events if calibration supports it; 400 is a secondary stress candidate. Runtime correctness calibration is still pending provider/API configuration. This directory contains no final benchmark cases or final expected outputs.

## Layout

```text
benchmark/
├── README.md
├── calibration/
│   ├── README.md
│   ├── histories/
│   ├── oracle/
│   └── reports/
├── dev/
│   ├── cases/
│   └── expected/
└── holdout/
    ├── cases/
    └── expected/
```

- `dev/cases/`: development inputs that may eventually be used for local iteration.
- `dev/expected/`: development references that may eventually support local debugging.
- `calibration/`: non-scored, calibration-only synthetic histories and visible calibration oracle data. It is not the final benchmark and must not be used to tune a baseline prompt.
- `holdout/cases/`: evaluator-owned holdout inputs. They are placeholders in this scaffold.
- `holdout/expected/`: evaluator-owned ground truth. It must remain unavailable to implementation agents.

## Protection policy

The holdout split is not a second development directory. In an actual benchmark run:

- the evaluator owns and provisions holdout cases and expected outputs;
- implementation agents receive neither holdout expected outputs nor derivative hints about them;
- scoring occurs in an isolated evaluator boundary;
- candidate outputs may leave the implementation environment only through the defined submission interface;
- evaluator logs and error messages must not echo protected expected content; and
- holdout data should not be committed to the implementation repository.

The tracked placeholders in this scaffold contain no cases, labels, or ground truth. A `.gitkeep` file is only a directory marker.

The calibration directory is intentionally different: its oracle is visible because
it is non-scored and exists only to calibrate length. It must remain separate from
final development and holdout material.

## Contract status

The proposed contract defines source modalities, stable scenario identifiers, permitted metadata, expected-output granularity, uncertainty labels, fixed checkpoint queries, longitudinal scoring, maintenance interventions, evaluator boundaries, and the required size-calibration step. It also specifies how conflicts, missing data, units, dates, provenance, and user-approval boundaries are represented.

After human approval of the calibration evidence and final length, the contract should be versioned and frozen before final development cases or synthetic inputs are added. Holdout construction remains evaluator-owned.

Do not expose or derive holdout expected outputs through prompts, fixtures, trajectories, documentation, logs, or debug artifacts.
