# Reproduction protocol

The goal of this document is to make a future implementation or benchmark result repeatable without exposing protected evaluation data.

## 1. Run identity

Every run should have a stable identifier and record:

- repository commit or immutable source revision;
- implementation and configuration version;
- runtime and coding prompt revisions;
- model name, provider, and model-version identifier;
- benchmark split and input manifest identifier;
- evaluation/scoring revision;
- operating system and dependency/runtime versions;
- timezone and locale;
- random seeds and concurrency settings; and
- start and end timestamps.

## 2. Input discipline

- Use immutable source snapshots or content-addressed input manifests.
- Record hashes or stable identifiers for inputs without copying protected content into logs.
- Keep synthetic, raw, development, and holdout data clearly separated.
- Never include holdout expected outputs in implementation logs, prompts, trajectories, or debug artifacts.
- Redact secrets and unnecessary personal information before sharing a run artifact.

## 3. Processing record

A reproducible run should make it possible to identify:

1. the source snapshot;
2. the interpretation versions used;
3. the deterministic calculation and projection versions;
4. approvals or user decisions included in the run; and
5. the resulting derived-state and evaluation artifact identifiers.

Derived outputs should be disposable and rebuildable. The source snapshot and version manifest are the durable anchors.

## 4. Result record template

Future tooling can populate a record with fields equivalent to:

```text
run_id:
source_manifest:
code_revision:
runtime_prompt_revision:
coding_prompt_revision:
model_versions:
configuration:
benchmark_split:
scoring_revision:
environment:
timezone:
random_seed:
output_artifacts:
notes:
```

This is a documentation template only; no runner is implemented yet.

## 5. Determinism expectations

For deterministic transformations, repeated runs with identical versioned inputs should produce identical results. If a model or external service introduces nondeterminism, record the relevant settings and separate that variation from deterministic calculation checks.

Missing values must remain missing during reproduction. A run is not reproducible if it silently fills absent values with zero, false, or a guessed default.

## 6. Minimum handoff checklist

Before calling an evaluation result reproducible, confirm:

- the revision can be checked out;
- dependencies and runtime versions are recorded;
- the input manifest is available to the authorized evaluator;
- prompts and model versions are pinned or identified;
- deterministic projections have a versioned implementation;
- raw evidence is unchanged;
- the output artifact can be located; and
- holdout ground truth was never included in the implementation-facing artifacts.

## 7. Non-scored size calibration

The pre-freeze calibration dataset is reproducible without the application or
evaluator. From the repository root, run:

```text
python benchmark/calibration/generate_calibration.py
```

The command regenerates the four deterministic prefixes and the separate,
calibration-only oracle. Record the resulting manifest and file hashes, the
selected model/provider/version, tokenizer, documented context limit, fixed
prompt revision (`baseline-v1`), exact token counts, context utilization,
query-correctness readout, degradation observations, runtime, retries, and cost
in [`benchmark/calibration/reports/RUNTIME_CALIBRATION.md`](../benchmark/calibration/reports/RUNTIME_CALIBRATION.md).
The visible calibration oracle is not final benchmark ground truth and must not
be copied into development or holdout packages.
