# Benchmark boundary

This directory defines the intended boundary between development cases and evaluator-controlled holdout material. The proposed benchmark contract is documented in [docs/EVALUATION.md](../docs/EVALUATION.md#8-proposed-benchmark-contract) and is pending human review. This directory contains no benchmark cases or expected outputs yet.

## Layout

```text
benchmark/
├── README.md
├── dev/
│   ├── cases/
│   └── expected/
└── holdout/
    ├── cases/
    └── expected/
```

- `dev/cases/`: development inputs that may eventually be used for local iteration.
- `dev/expected/`: development references that may eventually support local debugging.
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
## Contract status

The proposed contract defines source modalities, stable scenario identifiers, permitted metadata, expected-output granularity, uncertainty labels, and scoring rules. It also specifies how conflicts, missing data, units, dates, provenance, and user-approval boundaries are represented.

After human approval, the contract should be versioned and frozen before development cases or synthetic inputs are added. Holdout construction remains evaluator-owned.

Do not expose or derive holdout expected outputs through prompts, fixtures, trajectories, documentation, logs, or debug artifacts.
