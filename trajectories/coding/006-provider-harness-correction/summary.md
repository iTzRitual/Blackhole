# Coding trajectory summary: provider harness correction

## Goal

Correct the runtime architecture to be subscription-first through installed,
authenticated local agent CLIs; design the smallest provider-agnostic boundary;
verify the locally available Codex CLI safely; run the existing non-scored
50/100/200/400 size calibration with the frozen prompt; and document the Gate A
implications without implementing Blackhole, the baseline, or evaluation
infrastructure.

## Agent/tool used

Codex working in the repository with PowerShell and the locally installed Codex
CLI. No direct provider API key was requested or used. No credential value was
read, copied, exported, or persisted.

## Initial hypothesis

The installed authenticated Codex CLI could provide a usable, reproducible
subscription-first runtime path, including non-interactive execution, a
persistent session, resume, exact model/reasoning selection, and usage metadata.
If it did, the fair long-chat baseline could be calibrated through one isolated
persistent CLI session without giving it Blackhole-owned state.

## Important decisions

- Keep direct OpenAI/Anthropic API credentials out of the MVP runtime path.
  Authentication belongs to the provider CLI.
- Define a small `AgentProvider` boundary around detection, discovery,
  safe auth/status, capabilities, one-shot and persistent execution, resume,
  structured output, supported model/reasoning selection, timeout/cancellation,
  usage metadata, and raw trajectory references.
- Use Codex CLI as the verified MVP provider and document a minimal Claude Code
  adapter target. Do not claim Claude runtime support because no local `claude`
  binary was available.
- Use a real persistent Codex session for the calibration baseline, with each
  size in a fresh temporary workspace and no repository, database, expected
  output, calibration oracle, or evaluator files copied into that workspace.
- Supply the events as one ordered JSONL capture block and resume once for the
  fixed query bundle. This preserves complete chronological content and the
  provider session boundary without adding a Blackhole summary or retrieval
  layer.
- Keep the frozen `baseline-v1` prompt and query bundle unchanged after the
  official runs began. An earlier 50-event pilot exposed an unobservable query
  field; the query contract was corrected before the clean official 50-event
  run, and the baseline prompt was not tuned from the pilot's model errors.
- Treat the calibration as non-scored evidence. The provisional recommendation
  is 200 events for the realistic primary and 400 events for a secondary stress
  track. Do not run the optional 800-event extension because the 400-event run
  was not comfortably practical and showed additional state defects.

## Tools and actions used

- Read the pasted runtime-provider correction and the relevant repository
  guidance and design documents.
- Scanned provider/API-shaped environment variable names without printing
  values; no such variables were used.
- Inspected local command availability, Codex version/help, feature status,
  safe login status, and sanitized doctor output. The local Codex version was
  `codex-cli 0.150.0-alpha.12.2`; no local Claude Code binary was found.
- Verified the exact `gpt-5.6-luna` plus `max` configuration with an ephemeral
  read-only capability probe.
- Verified a persistent Codex session and successful resume.
- Ran fresh isolated persistent sessions at 50, 100, 200, and 400 events using
  `baseline-v1` and the fixed calibration query bundle.
- Compared the returned JSON deterministically against the calibration-only
  oracle with a one-off in-memory calculation. No evaluator implementation or
  `eval/results` score artifact was created.
- Updated the product, architecture, decision, evaluation, reproduction,
  calibration, and repository guidance documents.

## Failures encountered

- An initial probe used an unsupported `-a` option. The CLI help was checked and
  the probe was rerun with the accepted `-c model_reasoning_effort=max` setting.
- The first 50-event pilot query asked the model to name a field that was not
  observable in the prompt. That pilot was retained only as a diagnostic, not
  scored. The fixed query bundle was corrected to require the observable
  `secondary_field` label, then the 50-event run was repeated cleanly.
- The local CLI did not expose a documented context limit or tokenizer, and the
  subscription path did not expose a per-call dollar price.
- Each run emitted non-fatal Windows shell-snapshot/plugin-icon/legacy-notify
  warnings. All initial and resumed turns completed; no context-warning,
  truncation, or rejection signal was observed.

## Retries or changed approaches

The only substantive protocol change was the query-contract correction before
the official run set. The official 50-event run was a fresh-session rerun. No
baseline prompt, model, reasoning setting, or scoring rule was changed after
seeing official calibration failures. The initial ordered-block approach was
kept for all four sizes to control runtime while preserving the full history.

## Human feedback or checkpoints

The human explicitly corrected the assumed API-key architecture, required
subscription-first local CLI providers, preferred Codex `gpt-5.6-luna` with
`max` reasoning subject to verification, required isolation and persistent
resume where reliable, and authorized the existing calibration sweep. Gate A
was not approved or frozen; the final recommendation is returned for human
review.

## Evaluation performed

The verified runtime configuration and non-scored results are recorded in
[`benchmark/calibration/reports/RUNTIME_CALIBRATION.md`](../../../benchmark/calibration/reports/RUNTIME_CALIBRATION.md).
All four sizes completed. The LQA-style calibration readouts were 0.8167,
0.9000, 0.8545, and 0.8091 for 50, 100, 200, and 400 events. State-only means
were 0.8889, 1.0000, 0.9394, and 0.8788. Missing/unknown handling was exact at
all sizes; the systematic relation error was duplicate-count overestimation.
The 400-event run took 575.956 seconds and showed one current and one previous
state defect, while the 200-event run took 277.032 seconds and showed one
previous-state defect.

No application code, baseline implementation, benchmark cases, final ground
truth, executable evaluator, or production infrastructure was added.

## Result

The subscription-first provider architecture is locally viable for the Codex
MVP configuration tested. Persistent resume was reliable for the probes and all
four calibration runs. The full histories were empirically accepted without a
context warning, but the context ceiling is not known from the CLI. The 400
event size is a useful stress condition, not the realistic primary under the
observed runtime envelope.

## Regressions or unresolved issues

- The calibration has one run per size, so the state-quality decline is not yet
  a repeatability claim.
- Initial histories were batched as ordered JSONL rather than sent as one CLI
  turn per capture; per-capture turn overhead remains unmeasured.
- No Claude adapter was runtime-tested.
- Full provider JSONL stdout was withheld from the user-facing logs; final
  provider messages, thread IDs, usage summaries, and runtime observations are
  preserved in the runtime trajectory directory.

## Final decision

**KEEP** the subscription-first CLI provider boundary and the isolated persistent
baseline calibration protocol. **REVISE/hold** the final benchmark length until
human Gate A review; provisionally use 200 events as primary and 400 as stress.
Do not proceed to application or baseline implementation in this phase.

## Related git commit

Single coherent commit: `benchmark: calibrate Codex CLI runtime for Gate A`.
