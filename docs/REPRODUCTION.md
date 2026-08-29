# Reproduction protocol

The goal of this document is to make a future implementation or benchmark result repeatable without exposing protected evaluation data. The current
Gate A proposal is still under human review; the existing execution commands
below describe historical artifacts and must not be treated as a new freeze.

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

The current public development runner and evaluator are implemented in
[`baseline/run_baseline.py`](../baseline/run_baseline.py) and
[`eval/score.py`](../eval/score.py). The checklist remains the handoff template
for future holdout and advanced-system runs.

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
calibration-only oracle. Record the resulting manifest and file hashes, the selected model/provider/version,
tokenizer, documented context limit, fixed prompt revision (`baseline-v1`), exact
token counts, context utilization, query-correctness readout, degradation
observations, runtime, retries, and cost in
[`benchmark/calibration/reports/RUNTIME_CALIBRATION.md`](../benchmark/calibration/reports/RUNTIME_CALIBRATION.md).
The visible calibration oracle is not final benchmark ground truth and must not
be copied into development or holdout packages.

## 8. Subscription-first CLI runtime

The MVP does not require a direct OpenAI or Anthropic API key. The runtime
controls a locally installed and authenticated agent CLI, while the CLI owns
authentication. Blackhole must not request, read, copy, export, or persist
provider tokens. A reproducer authenticates outside Blackhole and records only
safe status and version metadata.

The verified local runtime for the Gate A calibration was:

| Field | Recorded value |
| --- | --- |
| Provider | Codex CLI |
| CLI version | `codex-cli 0.150.0-alpha.12.2` |
| Authentication check | `codex login status`; authenticated status reported, with no credential value recorded |
| Model | `gpt-5.6-luna` |
| Reasoning effort | `max` |
| Claude Code | No local `claude` binary detected; adapter remains documented but unverified |
| Context limit | Not exposed by the local CLI help/doctor output; all 50/100/200/400 histories completed without a context-warning or truncation signal |

The harmless inspection commands used to establish that record were:

```text
codex --version
codex exec --help
codex exec resume --help
codex login status
codex features list
codex doctor --summary --json
```

Only safe status, version, feature, and top-level diagnostic metadata were
recorded; command output was not used to retrieve credentials.

The harmless capability probe that accepted the exact model/reasoning pair was:

```text
codex exec --ephemeral --skip-git-repo-check --json --model gpt-5.6-luna -c model_reasoning_effort=max -s read-only "Reply exactly with CAPABILITY_PROBE_OK and do not use tools."
```

The persistent baseline shape was:

```text
codex exec --json --model gpt-5.6-luna -c model_reasoning_effort=max -s read-only --ignore-rules --skip-git-repo-check -C <isolated-empty-workspace> -o <initial-output> -
codex exec fork <canonical-thread-id> --json --model gpt-5.6-luna -c model_reasoning_effort=max --ignore-rules --skip-git-repo-check -o <query-output> -
```

The Gate A baseline supplied chronological captures in four ordered batches:
1–50, 51–100, 101–150, and 151–200. This batching kept the run practical while
preserving the full chronological history and provider session boundary; it was
not a Blackhole summary or retrieval layer. At each checkpoint the harness used
the native atomic fork-with-prompt form, captured the read-only query response,
and never resumed that fork. The canonical session therefore received no query
or answer. The provider workspace was fresh and empty, and contained no
repository files, calibration oracle, expected outputs, database, or evaluator
internals.

Codex `--json` exposed thread identifiers and per-turn input, cached-input,
output, and reasoning-output usage fields. Provider subscription pricing was not
exposed, so the report records token usage and wall time rather than inventing a
dollar cost. A result produced with another provider, model, reasoning setting,
or CLI version is a different runtime configuration and must not be silently
compared with this record.

## 9. Historical Gate B corrected public development run

From the repository root, after authenticating Codex outside this repository:

```text
python benchmark/dev/generate_benchmark.py --check
python eval/contract_smoke.py
python baseline/run_baseline.py --timeout 1200 --output eval/results/baseline-v1-candidate.json --trajectory trajectories/runtime/003-baseline-v1
python eval/score.py --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/baseline-v1-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/baseline-v1.json
python -m unittest discover -s eval/tests -v
```

The runner reads only the public scenario, `prompts/runtime/baseline-v1.md`, the
v2 runner protocol, `benchmark/dev/query-bundle-v2.json`, and the public
`response-contract-v2.json`. It uses the existing authenticated CLI subscription
and does not read or persist provider tokens. The substantive `baseline-v1.md`
prompt is unchanged by the contract repair.
The evaluator reads the visible development expected output only for local
development. A holdout run must provision its expected output outside the
implementation checkout and must not reuse the public development command's
paths or artifacts.

The corrected-run artifacts are:

- `eval/results/baseline-v1-candidate.json` — candidate envelope and safe provider
  run metadata;
- `eval/results/baseline-v1.json` — the single official corrected deterministic
  score;
- `trajectories/runtime/003-baseline-v1/checkpoint-050.json` through
  `checkpoint-200.json` — model responses at isolated checkpoints;
- `eval/results/contract-smoke.json` — non-scored parser/canonicalizer/evaluator
  smoke evidence; and
- `benchmark/dev/response-contract-v2.json` — frozen public response boundary.

The earlier v0 artifacts remain preserved under the unmistakable names
`eval/results/baseline-v0-invalid-contract-candidate.json` and
`eval/results/baseline-v0-invalid-contract.json`, with the reason recorded in
`eval/results/baseline-v0-invalid-contract.md`. Their `LQA-0M=0.0000` is not an
official semantic baseline and must not be overwritten or reported as one.

The commands and artifacts in this section reproduce the prior Gate B execution
for auditability; they do not freeze or authorize the revised Gate A proposal.
The 50-event representative run, when present, is a labeled `DEV FAST / NOT
OFFICIAL SCORE` diagnostic and cannot replace the official four-checkpoint run.
Record the corrected run's actual checkpoint scores, totals, schema validity,
DSCR, provider input/output tokens, wall time, retries, and observed semantic
failure categories in its result and trajectory summary. Do not invent dollar
cost when the subscription runtime does not expose it.
