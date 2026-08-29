# Gate A runtime calibration report

**Status:** completed as non-scored calibration evidence; Gate A remains open
for human review.

The run used the frozen
[`baseline-v1`](../../../prompts/runtime/baseline-v1.md) instruction and the
fixed [`query-bundle.md`](../query-bundle.md). The calibration oracle was used
only by the controller after each run; it was never supplied to the provider
session. The full results are also summarized in the coding and runtime
trajectories under
[`trajectories/runtime/001-codex-calibration/`](../../../trajectories/runtime/001-codex-calibration/).

## Runtime configuration

| Field | Recorded value |
| --- | --- |
| Provider | Codex CLI |
| CLI version | `codex-cli 0.150.0-alpha.12.2` |
| Authentication | `codex login status` reported authenticated status; no credential value was recorded |
| Exact model | `gpt-5.6-luna` |
| Reasoning effort | `max` |
| Temperature | Default; not overridden |
| Prompt | `prompts/runtime/baseline-v1.md` (`baseline-v1`) |
| Query bundle | `benchmark/calibration/query-bundle.md` |
| Context limit | Not exposed by the local CLI help or `codex doctor --summary --json` output |
| Token counting | Codex `turn.completed` usage fields; planning estimates remain character-based (`ceil(chars / 4)`) because the tokenizer was not exposed |
| Concurrency/retries | One run per size, serial; no retry after a completed run |
| Pricing | Subscription path; no per-call dollar price exposed |
| Claude Code | No local `claude` binary detected; adapter not runtime-tested |

The exact preferred model/reasoning pair was accepted by a harmless ephemeral
probe. A persistent session probe also completed and resumed successfully. The
calibration runs used a fresh session and a fresh temporary workspace for each
size. The ordered JSONL history was supplied as one initial capture block, then
the same session was resumed for the fixed query; this preserved the full
chronological history and session boundary without adding a Blackhole summary or
retrieval layer.

## Verified Codex CLI capabilities

- `codex exec` accepts a non-interactive prompt from stdin or an argument.
- `--json` emits machine-readable JSONL events, including a thread identifier
  and `turn.completed` usage metadata.
- `codex exec resume <thread-id>` resumes a persistent session; the probe and
  all four calibration sessions resumed successfully.
- `--model` selects the model, and `-c model_reasoning_effort=max` selected the
  requested reasoning setting for the verified model.
- `-s read-only`, `-C`, `--skip-git-repo-check`, `--ignore-rules`, and
  `--ephemeral` are available for controlled execution; `-o` captures the last
  provider message and `--output-schema` is available for structured output.
- The help output exposed no dedicated timeout or cancellation flag. A future
  provider adapter must therefore implement an outer process/session deadline
  and termination path, and report cancellation as controller metadata; this
  behavior was not needed or exercised in the completed runs.

The provider process ran with a read-only policy, an isolated temporary working
directory, `--skip-git-repo-check`, and no repository, oracle, expected-output,
database, or evaluator files copied into the workspace. The baseline invoked no
tools. Codex emitted non-fatal Windows shell-snapshot, plugin-icon, and
`legacy_notify` hook warnings; each run still completed. These warnings are
environment observations, not model answers or context failures.

## Artifact hashes

The calibration manifest records the regenerated oracle hashes. The input and
final-message hashes for the runtime trajectory are:

| Events | History SHA-256 | Initial output SHA-256 | Query output SHA-256 |
| ---: | --- | --- | --- |
| 50 | `7e1c209b6276a5512cf4affa85cd7e179cfe2d80d9c5169dc09eb734ebba4a1f` | `f4cdb75e14004ec1f26a9f347bfafe2d7c732cb31a80749cbd9bfe837e1c7612` | `03e4e9b679502b128e0a9e05e03a2ca9ddee26f36bd828b40e1d8925f3ce79ce` |
| 100 | `3ff9705ae0580aca0e5948f2db5d40926222a15d0e5cb810556903f7a920f58e` | `f4cdb75e14004ec1f26a9f347bfafe2d7c732cb31a80749cbd9bfe837e1c7612` | `ddf87043f9594e2f7cb072ef684257178f645e8b567790a101bf14701f6fcf4d` |
| 200 | `e87f0a567c12185c681beb31ddab220c4c1e0dd7b3d12d20c6b0da49762425af` | `f4cdb75e14004ec1f26a9f347bfafe2d7c732cb31a80749cbd9bfe837e1c7612` | `8730b36fee7e062767f7b46cf2476a1b497ecbe87e953aa87c877878844cfc8d` |
| 400 | `a16ed6edc9f0f0ac2ce01726fc96c9a7f4a24747ec7b4aba661a3f0b8cca90c6` | `f4cdb75e14004ec1f26a9f347bfafe2d7c732cb31a80749cbd9bfe837e1c7612` | `39b3b10ea8aebe75ced974a5f3a6d272f90961930c1844510d33be1166156bc2` |

## Measured run matrix

`input`, `cached input`, `output`, and `reasoning output` are the provider's
reported token fields for the initial capture turn and the resumed query turn,
respectively. The output files contain the final provider messages; raw JSONL
process stdout was intentionally withheld from the user-facing run summary.

| Events | History chars / planning tokens | Input tokens (initial / query) | Cached input (initial / query) | Output tokens (initial / query) | Reasoning output (initial / query) | Full history accepted | Runtime |
| ---: | ---: | ---: | ---: | ---: | ---: | :---: | ---: |
| 50 | 20,636 / 5,159 | 21,490 / 24,696 | 9,984 / 21,248 | 33 / 9,803 | 22 / 9,305 | yes; no warning | ~179 s* |
| 100 | 41,292 / 10,323 | 28,138 / 31,347 | 9,984 / 27,392 | 36 / 9,997 | 25 / 9,500 | yes; no warning | 186.975 s |
| 200 | 82,727 / 20,682 | 41,438 / 44,653 | 9,984 / 40,704 | 42 / 15,003 | 31 / 14,502 | yes; no warning | 277.032 s |
| 400 | 165,580 / 41,395 | 68,121 / 71,334 | 9,984 / 67,328 | 40 / 31,579 | 29 / 31,078 | yes; no warning | 575.956 s |

\* The first clean 50-event run's end-to-end time is approximate, based on the
official trajectory output timestamps; its token fields were retained from the
completed wrapper result. No run was rejected or reported truncation or
compaction. Because the context ceiling was not exposed, “fits” here means
empirically accepted with the complete ordered input and no observed context
warning, not a claim about the model's maximum context percentage.

## Deterministic correctness readout

The calibration query has four fixed assertion groups: current state (10
storylines), immediately previous state (10), intentionally missing secondary
fields (10), and relation counts (4). The controller canonicalized the JSON
answers and applied the pre-specified rule:

```text
TP = exact supported assertions
FP = unsupported or incorrect produced assertions
FN = expected assertions omitted
query_score = TP / (TP + FP + FN)
LQA-style calibration score = mean of the four query-group scores
```

This is a calibration readout, not a final benchmark score.

| Events | Current score | Previous score | Missing/unknown score | Relation score | State-only mean | LQA-style score | Current defects | Previous defects | Relation defects |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 50 | 1.0000 | 0.6667 | 1.0000 | 0.6000 | 0.8889 | 0.8167 | 0 | 2 | 1 |
| 100 | 1.0000 | 1.0000 | 1.0000 | 0.6000 | 1.0000 | 0.9000 | 0 | 0 | 1 |
| 200 | 1.0000 | 0.8182 | 1.0000 | 0.6000 | 0.9394 | 0.8545 | 0 | 1 | 1 |
| 400 | 0.8182 | 0.8182 | 1.0000 | 0.6000 | 0.8788 | 0.8091 | 1 | 1 | 1 |

The relation defect at every size was an overestimated `duplicate_count`; the
correction, contradiction, and ambiguous-link counts matched. The missing-field
behavior was correct at every size: all ten answers remained explicit
`unknown`/`missing`. At 400 events, the model returned an unknown current state
for the unresolved storyline but used `conflict` rather than the expected
`conflicting` reason, and it returned the wrong immediately previous value for
that storyline. The 50-event previous-state defects were two different
storyline answers; the 200-event defect was one. The fixed relation-count error
is therefore a systematic query weakness, while the 400-event state defects are
the relevant evidence for long-history degradation.

## Interpretation and length recommendation

The observed state-only results are non-monotonic: 50 and 100 events produced
two and zero current/previous defects, 200 produced one, and 400 produced two.
The 400-event state-only mean was 0.8788 versus 1.0000 at 100, while the full
LQA-style score was 0.8091 versus 0.9000. This supports a cautious conclusion
that state quality can degrade by 400 events while the complete history is still
accepted, but one run per size is not enough to claim a repeatable curve. The
synthetic endpoint state also changes by prefix, so the result is evidence for
selection—not a model leaderboard result.

The 400-event run took about 9.6 minutes and consumed substantially more
reasoning output than the 200-event run. It therefore does not meet the
“comfortably practical with little or no degradation” condition for an optional
800-event extension. No 800-event run was started.

**Provisional Gate A recommendation:** use approximately **200 events** for the
realistic primary benchmark, with **400 events** as a secondary stress track if
the hackathon budget and execution time permit. This preserves the requested
150–200-event focus while retaining a larger state-churn stress condition. Human
review is required before freezing the final benchmark length.

## Limitations and unresolved items

- The local CLI did not expose a documented context limit or tokenizer, so fit is
  empirical rather than a percentage of a known usable window.
- The calibration used one initial ordered JSONL block per size followed by a
  resumed query, rather than 50–400 separate provider turns. This preserves
  chronological content and persistent-session behavior but does not measure
  per-capture turn overhead.
- One early 50-event pilot used an earlier query wording that asked for an
  unobservable field name. It was discarded from the readout; the query bundle
  was corrected to require only the observable `secondary_field` label, and the
  clean 50-event run was repeated with a fresh session. The baseline prompt was
  not tuned from the pilot's model errors.
- No repeated runs were made, so variance and “repeatable degradation” remain
  open for human review.
- Subscription pricing was not available from the CLI; token usage and wall time
  are the reproducible cost proxies.
