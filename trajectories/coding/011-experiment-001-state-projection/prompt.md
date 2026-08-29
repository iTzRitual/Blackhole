# Experiment 001 prompt summary

This is a faithful retrospective summary of the human-authorized advanced-
system instruction, not a verbatim historical transcript.

The repository is already frozen at Gate A and valid Gate B. Do not reopen the
benchmark, change expected outputs, change `response-contract-v2`, or modify
the official `baseline-v1` result. Build the smallest evidence-backed Blackhole
architecture that can materially improve longitudinal state maintenance over
the valid long-chat baseline, using Codex CLI with `gpt-5.6-luna` and
reasoning `max` where practical.

Run up to three evidence-driven experiments, each with a written hypothesis,
the smallest meaningful change, tests, the 50-event FAST DEV slice first,
before/after comparison, regression documentation, a KEEP/REVISE/REMOVE
decision, and coding/runtime trajectories. Do not bundle unrelated changes or
hardcode benchmark answers.

Experiment 001 targets poor current-state and temporal reconciliation. Its
hypothesis is that an append-only event store plus a deterministic,
rebuildable current-state projection can reduce stale and superseded-state
errors without making the LLM reread the entire history. The first version
should use SQLite, immutable captures, structured derived facts, current/effective
state, provenance, supersession/history semantics, a scoped semantic Codex
boundary for new captures, and deterministic projection. Do not build the full
UI, solve every entity type, or add unnecessary multi-agent orchestration.

The official 200-event benchmark remains the final milestone only after a
candidate demonstrates improvement on FAST DEV and passes major tests. Preserve
the subscription-first runtime boundary and never read or store provider
credentials. After the measured milestone, report the requested GATE C PREVIEW
and stop.
