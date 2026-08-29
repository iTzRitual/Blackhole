# Human instruction summary

This file records the human-authorized instruction from the pasted request
"RUNTIME PROVIDER ARCHITECTURE CORRECTION". It is a faithful task summary,
not a verbatim historical prompt and not an exported session transcript.

The human corrected the runtime assumption: Blackhole must be subscription-first
and must not require direct OpenAI or Anthropic API credentials for the MVP. It
should control an already-installed, already-authenticated local agent CLI,
with the CLI owning authentication. Codex CLI is preferred and Claude Code is
the minimal secondary provider. Blackhole must never read, copy, export, or
persist provider auth tokens.

The authorized work is to:

- design the smallest provider-agnostic `AgentProvider` boundary covering
  detection, binary discovery, auth/status checks, capabilities, one-shot and
  persistent sessions, resume, structured output, model/reasoning selection,
  timeout, cancellation, usage metadata, and raw trajectory capture;
- inspect actual local Codex CLI and Claude Code behavior with harmless help,
  status, version, and capability commands, without exposing credentials;
- verify whether Codex accepts the preferred, not-yet-frozen configuration
  `gpt-5.6-luna` with `max` reasoning, and report alternatives without silently
  changing configuration;
- use a persistent Codex session for the fair long-chat baseline when reliable,
  with complete chronological history and no Blackhole database, hidden summary,
  retrieval, or advanced state supplied;
- isolate baseline sessions in a temporary workspace that cannot read benchmark
  expected outputs, calibration oracles, Blackhole state, or evaluation internals;
- keep Blackhole durable memory in its own future SQLite/state layer, using fresh
  or deliberately scoped semantic provider calls rather than one long provider
  session as primary memory;
- document subscription-first setup and reproduction requirements;
- run the existing 50/100/200/400 calibration through the local CLI path only if
  the actual capability and authentication checks succeed, using frozen
  `baseline-v1`, identical provider/model/reasoning settings, persistent session
  behavior where reliable, and deterministic calibration correctness;
- consider the previously defined 800-event extension only under its existing
  conditions;
- update architecture, reproduction, evaluation, product, and decision
  documentation; and
- do not implement the advanced Blackhole system yet.

The return must report detected CLIs and versions, safely determinable auth
status, Codex non-interactive capabilities, acceptance of `gpt-5.6-luna` and
`max`, the final proposed provider interface, baseline session and isolation
strategies, advanced-call strategy, reproduction implications, calibration
results if possible, and blockers. If calibration completes, return
`GRILL ME — GATE A FINAL` and stop.
