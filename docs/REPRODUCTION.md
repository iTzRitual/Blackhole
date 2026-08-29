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

The current public development runner and evaluator are implemented in
[`baseline/run_baseline.py`](../baseline/run_baseline.py) and
[`eval/score.py`](../eval/score.py). The scoped advanced experiment runner is
[`app/advanced_runner.py`](../app/advanced_runner.py); the checklist remains the
handoff template for future holdout and advanced-system runs.

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

## 9. Gate B corrected public development run (valid)

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

The 50-event representative run, when present, is a labeled `DEV FAST / NOT
OFFICIAL SCORE` diagnostic and cannot replace the official four-checkpoint run.
Record the corrected run's actual checkpoint scores, totals, schema validity,
DSCR, provider input/output tokens, wall time, retries, and observed semantic
failure categories in its result and trajectory summary. Do not invent dollar
cost when the subscription runtime does not expose it.

## 10. Experiment 001 state-projection replay

Experiment 001 is an advanced application experiment, not a replacement for
the fair baseline. It uses only the public development scenario and the frozen
public response contract. A fresh semantic run requires an already-installed,
already-authenticated Codex CLI and never receives expected output or holdout
material:

```text
python -m app.advanced_runner --scenario benchmark/dev/cases/scenario-001.json --query-bundle benchmark/dev/query-bundle-v2.json --response-contract benchmark/dev/response-contract-v2.json --max-events 200 --batch-size 50 --semantic-reasoning high --output eval/results/experiment-001-full-v1-candidate.json --trajectory trajectories/runtime/experiment-001-full-v1 --run-id experiment-001-full-v1 --label "EXPERIMENT 001 / FROZEN 200-EVENT MILESTONE / HIGH EXTRACTION"
python eval/score.py --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/experiment-001-full-v1-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/experiment-001-full-v1.json
```

Projection revisions can be reproduced without provider calls from the
recorded public extraction outputs:

```text
python -m app.advanced_runner --scenario benchmark/dev/cases/scenario-001.json --query-bundle benchmark/dev/query-bundle-v2.json --response-contract benchmark/dev/response-contract-v2.json --max-events 200 --batch-size 50 --replay-extraction-dir trajectories/runtime/experiment-001-full-v1 --output eval/results/experiment-001-full-v4-candidate.json --trajectory trajectories/runtime/experiment-001-full-v4 --run-id experiment-001-full-v4 --label "EXPERIMENT 001 / FROZEN 200-EVENT MILESTONE / PROJECTOR V4 GROUP REPLAY"
python eval/score.py --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/experiment-001-full-v4-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/experiment-001-full-v4.json
```

The replay uses the public development expected output only because this is a
local diagnostic. A judge must mount holdout expected output privately and must
not place it in the implementation checkout, prompt, trajectory, or result
artifact. The final Experiment 001 replay is recorded at
`eval/results/experiment-001-full-v4.json` and its runtime evidence is under
`trajectories/runtime/experiment-001-full-v4/`; the fresh semantic provider
usage is recorded under `experiment-001-full-v1`.

## 11. Experiment 002 genericity replay

Experiment 002 is a deterministic projector repair. It reuses the recorded
public extraction outputs above, so it requires no provider configuration and
makes no model calls:

```text
python -m app.advanced_runner --scenario benchmark/dev/cases/scenario-001.json --query-bundle benchmark/dev/query-bundle-v2.json --response-contract benchmark/dev/response-contract-v2.json --max-events 200 --batch-size 50 --replay-extraction-dir trajectories/runtime/experiment-001-full-v1 --output eval/results/experiment-002-generic-full-candidate.json --trajectory trajectories/runtime/experiment-002-generic-full --run-id experiment-002-generic-full --label "EXPERIMENT 002 / GENERIC PROJECTOR / FROZEN 200-EVENT PUBLIC REPLAY" --semantic-reasoning high
python eval/score.py --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/experiment-002-generic-full-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/experiment-002-generic-full.json
```

The FAST diagnostic uses the same replay mode with `--max-events 50` and the
four selected public query IDs, followed by `eval.score_slice`; it is not an
official score. The final full artifact is
`eval/results/experiment-002-generic-full.json`, with runtime evidence under
`trajectories/runtime/experiment-002-generic-full/`. Holdout expected output
must remain privately mounted by the judge and must never be copied into an
implementation checkout or trajectory.

## 12. Local demo reproduction

The demo uses only the Python standard library and a committed synthetic seed.
It is independent of the public benchmark and does not require provider
authentication:

```text
python scripts/seed_demo.py --reset
python -m app.web_app --host 127.0.0.1 --port 8080
```

Then open `http://127.0.0.1:8080`. The seed command replaces only the selected
demo SQLite file under `data/demo/`; it does not touch benchmark, baseline, or
evaluation artifacts. The server auto-seeds a missing demo database, serves the
four static UI views, and exposes these local routes:

| Route | Purpose |
| --- | --- |
| `GET /api/state` | Current deterministic attention, memory, counts, and recent raw captures |
| `GET /api/query?q=...` | One of the fixed structured demo query families |
| `POST /api/capture` | Append one raw text capture with pending semantic status |
| `POST /api/reset` | Rebuild the demo database from `data/synthetic/demo-seed.json` |

The capture endpoint stores text and optional filename metadata as a new raw
event; it creates no semantic observation and performs no external action. The
web demo checks only whether the `codex` executable is discoverable and does not
read authentication files or tokens. For a semantic extraction run, use the
separate `app.advanced_runner` commands above after authenticating the local
provider outside Blackhole.

The browser-facing smoke checks used during this phase verified that the page
loads, the Attention and Memory views render seeded projections, a suggested Ask
question returns a structured change section, and a capture returns `Saved.`.
The automated equivalent is `app/tests/test_demo.py`; the browser smoke test is
not a benchmark score.

## 13. Experiment 003 relation-reconciliation replay

Experiment 003 reuses the recorded public Experiment 001 semantic extraction,
then applies the generic deterministic fallback and bounded raw-capture
candidate retrieval. It makes no provider calls and does not change the frozen
benchmark or official baseline:

```text
python -m app.advanced_runner --scenario benchmark/dev/cases/scenario-001.json --query-bundle benchmark/dev/query-bundle-v2.json --response-contract benchmark/dev/response-contract-v2.json --max-events 200 --batch-size 50 --replay-extraction-dir trajectories/runtime/experiment-001-full-v1 --output eval/results/experiment-003-retrieval-full-v3-candidate.json --trajectory trajectories/runtime/experiment-003-retrieval-full-v3 --run-id experiment-003-retrieval-full-v3 --label "EXPERIMENT 003 / RETRIEVAL RELATION RECONCILIATION / FROZEN 200-EVENT PUBLIC REPLAY" --semantic-reasoning high --relation-recovery retrieval
python eval/score.py --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/experiment-003-retrieval-full-v3-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/experiment-003-retrieval-full-v3.json
```

The resulting development evidence is
`eval/results/experiment-003-retrieval-full-v3.json`, with runtime records
under `trajectories/runtime/experiment-003-retrieval-full-v3/`. Candidate
retrieval is capped at four earlier raw captures per considered relation. A
judge must mount holdout expected output privately and must not copy it into an
implementation checkout or trajectory.

## 14. Final submission evidence

The product-phase deterministic comparison snapshot is recorded in
`eval/results/final-comparison-v1.json`; it references the unchanged official
`baseline-v1` artifact and the preceding kept advanced replay. The current
Experiment 005 result is recorded below, with Experiment 004 and Experiment
003 preserved as preceding kept replays. Each provides checkpoint values,
category metrics, and runtime caveats for their respective phase. The
representative product/runtime behavior is described in
`trajectories/runtime/013-demo-simple-capture/` through
`trajectories/runtime/016-demo-correction-reassignment/`. The final validation
checklist and exact presentation claims are in `docs/VIDEO_SCRIPT.md` and
`docs/VIDEO_SHOT_LIST.md`.

## 15. Experiment 004 selective completeness replay

Experiment 004 reuses the recorded public Experiment 001 semantic extraction
and the unchanged Experiment 003 retrieval treatment. It then scans each raw
capture for structural evidence and applies only deterministic, unambiguous
derived completions. This replay makes no provider calls:

```text
python -m app.advanced_runner --scenario benchmark/dev/cases/scenario-001.json --query-bundle benchmark/dev/query-bundle-v2.json --response-contract benchmark/dev/response-contract-v2.json --max-events 200 --batch-size 50 --replay-extraction-dir trajectories/runtime/experiment-001-full-v1 --output eval/results/experiment-004-deterministic-full-candidate.json --trajectory trajectories/runtime/experiment-004-deterministic-full --run-id experiment-004-deterministic-full --label "EXPERIMENT 004 / DETERMINISTIC COMPLETENESS / FROZEN 200-EVENT PUBLIC REPLAY" --semantic-reasoning high --relation-recovery retrieval --completeness deterministic
python eval/score.py --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/experiment-004-deterministic-full-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/experiment-004-deterministic-full.json
```

The kept result is
[`eval/results/experiment-004-deterministic-full.json`](../eval/results/experiment-004-deterministic-full.json).
The runner records scanner versions, evidence digests, flagged captures,
completion counts, projection runs, and provider usage in the candidate and
under
[`trajectories/runtime/experiment-004-deterministic-full/`](../trajectories/runtime/experiment-004-deterministic-full/).
The optional `--completeness verifier` mode is implemented for future
human-authorized runs, but was not used for this result because deterministic
FAST and full replay already met the keep threshold. A verifier run must use a
fresh scoped local CLI call and must not receive expected output or evaluator
internals.

## 16. Experiment 005 duplicate-evidence replay

Experiment 005 reuses the recorded public Experiment 001 extraction, the
Experiment 003 retrieval treatment, and the Experiment 004 deterministic
completeness treatment. It enables only the new generic duplicate-evidence
projection mode; it makes no provider calls:

```text
python -m app.advanced_runner --scenario benchmark/dev/cases/scenario-001.json --query-bundle benchmark/dev/query-bundle-v2.json --response-contract benchmark/dev/response-contract-v2.json --max-events 50 --batch-size 50 --replay-extraction-dir trajectories/runtime/experiment-001-full-v1 --output eval/results/experiment-005-duplicate-evidence-fast-candidate.json --trajectory trajectories/runtime/experiment-005-duplicate-evidence-fast --run-id experiment-005-duplicate-evidence-fast --label "EXPERIMENT 005 / DUPLICATE-AWARE EVIDENCE / DEV FAST / NOT OFFICIAL SCORE" --semantic-reasoning high --relation-recovery retrieval --completeness deterministic --duplicate-evidence consolidate
python -m eval.score_slice --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/experiment-005-duplicate-evidence-fast-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/experiment-005-duplicate-evidence-fast.json --checkpoint 50 --query-ids q-subscriptions-current,q-subscriptions-history,q-attention-14d,q-recent-changes
```

The standard FAST result is diagnostic only. The justified frozen public replay
uses all four approved checkpoints:

```text
python -m app.advanced_runner --scenario benchmark/dev/cases/scenario-001.json --query-bundle benchmark/dev/query-bundle-v2.json --response-contract benchmark/dev/response-contract-v2.json --max-events 200 --batch-size 50 --replay-extraction-dir trajectories/runtime/experiment-001-full-v1 --output eval/results/experiment-005-duplicate-evidence-full-candidate.json --trajectory trajectories/runtime/experiment-005-duplicate-evidence-full --run-id experiment-005-duplicate-evidence-full --label "EXPERIMENT 005 / DUPLICATE-AWARE EVIDENCE / FROZEN 200-EVENT PUBLIC REPLAY" --semantic-reasoning high --relation-recovery retrieval --completeness deterministic --duplicate-evidence consolidate
python eval/score.py --scenario benchmark/dev/cases/scenario-001.json --expected benchmark/dev/expected/scenario-001.json --candidate eval/results/experiment-005-duplicate-evidence-full-candidate.json --response-contract benchmark/dev/response-contract-v2.json --output eval/results/experiment-005-duplicate-evidence-full.json
```

The replay records duplicate-component metadata, consolidation counts, and the
derived SQLite state under
`trajectories/runtime/experiment-005-duplicate-evidence-full/`. The public
expected output is used only by the local development scorer. A judge must
mount holdout expected output privately and must never copy it into an
implementation checkout, prompt, trajectory, or result artifact. The official
`baseline-v1` result and all frozen benchmark artifacts remain unchanged.
