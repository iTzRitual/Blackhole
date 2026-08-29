# Runtime trajectory summary: baseline-v0

## Run identity

- Treatment: fair Codex CLI baseline-v0
- Scenario: `blackhole-long-chat-baseline-v1`
- Contract: `1.0-gate-a-dev`
- Model: `gpt-5.6-luna`
- Reasoning effort: `max`
- CLI: `0.150.0-alpha.12.2`
- Sandbox: read-only, fresh temporary workspace, no Blackhole application state
- Authentication: existing local Codex subscription; no credential value was read or persisted

## Input and state before execution

The runner supplied the public normalized raw captures in chronological order. The
canonical session began with captures 1–50, then received batches 51–100,
101–150, and 151–200. Each batch contained immutable event JSON lines and an
acknowledgement instruction. The canonical session received no expected output,
defect catalog, benchmark generator metadata, evaluator internals, database,
retrieval layer, or special memory tool.

## Instructions and tools

The canonical session received the frozen `baseline-v1` prompt and the versioned
runner protocol. At each approved checkpoint, the runner used the native atomic
Codex CLI `exec fork <canonical-thread-id> ... -` operation, supplying the fixed
12-query bundle and requiring one JSON response. Each query fork was read-only,
captured, scored after the run, discarded, and never resumed into canonical
ingestion. The runner accepted a query-list formatting slip by reshaping only the
outer query container; it did not semantically remap state keys or assertions.

## Checkpoint trace files

- `checkpoint-050.json`
- `checkpoint-100.json`
- `checkpoint-150.json`
- `checkpoint-200.json`

These files contain the captured model responses from isolated checkpoint forks.
No holdout material is present.

## Resulting state and user-visible outcome

All four checkpoint forks returned successfully and produced JSON containers with
all 12 query IDs. The baseline used a different state-key and assertion vocabulary
than the frozen exact contract, so the deterministic scorer recorded no exact true
positive matches. The saved evaluator result is
`eval/results/baseline-v0.json`; the raw candidate envelope and safe run metadata
are in `eval/results/baseline-v0-candidate.json`.

- LQA-0M: `0.0000`
- Checkpoints 50/100/150/200: `0.0000 / 0.0000 / 0.0000 / 0.0000`
- Totals: `TP=0`, `FP=266`, `FN=375`
- Schema validity: `false` with six malformed query records
- Attention false-positive rate: `1.0`
- DSCR: `336` (`168.0` per 100 events)
- Safety violations: none
- Source-integrity failure: none
- Provider/context rejection: none observed

Canonical capture turns took approximately 20 seconds total. Query forks took
approximately 2,513 seconds total. Provider-reported query input/output tokens
were 24,582/35,031, 30,662/32,201, 38,463/37,523, and 44,556/34,037 at the four
checkpoints. Subscription dollar cost was not exposed and was not inferred.

## Retries and unresolved issue

An earlier runner attempt failed because Windows console encoding produced invalid
UTF-8 input. The runner was corrected to send explicit UTF-8 bytes. A strict
provider-side output schema was then removed from invocation after the provider
rejected schema features needed for mixed JSON values; the response shape remains
documented and evaluator-validated. A two-step fork/resume diagnostic timed out,
so the official run used the successful atomic fork-with-prompt form.

The zero score is a recorded baseline observation. The state-key/assertion
vocabulary mismatch is a Gate B investigation item; expected outputs were not
changed to accommodate it.

## Reproduction references

- Runner: `baseline/run_baseline.py`
- Frozen prompt: `prompts/runtime/baseline-v1.md`
- Runner protocol: `prompts/runtime/baseline-runner-v1.md`
- Public scenario: `benchmark/dev/cases/scenario-001.json`
- Scorer: `eval/score.py`
