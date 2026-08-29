# Experiment 003 task instruction

This is a faithful summary of the human-provided Experiment 003 instruction
from `C:\Users\natan\.codex\attachments\98d0d0c8-75e4-42e6-8b3b-a507c035a60e\pasted-text-1.txt`, not a fabricated transcript.

Run a scoped retrieval-assisted relation-reconciliation experiment while
preserving the frozen benchmark, expected outputs, query bundle,
`response-contract-v2`, evaluator behavior, `baseline-v1`, and current kept
advanced result. Do not implement UI.

First perform a read-only failure audit of the recorded semantic extraction,
SQLite state, raw events, candidate output, and evaluator diagnostics. Classify
representative relation failures by missing relation, wrong target/type/fields,
unnecessary relation, duplicate-group/detail mismatch, deterministic
recoverability, and need for prior raw content. Do not alter expected output.

Then, only if justified, test the cheapest generic deterministic recovery first:
explicit supersession, exact or conservative normalized raw duplicates,
observation deltas, and task lifecycle relations. Run unit tests and the FAST
replay before considering one full replay.

Only if the audit shows that prior raw capture content is required, add small
generic candidate retrieval with actual raw candidate content and metadata. If
ambiguity remains, one selective Codex CLI `gpt-5.6-luna` relation-resolution
step at reasoning `high` may output only supported relationships whose targets
are supplied earlier candidates. Do not retrieve full history or evaluator
data, replace observations, or use benchmark-specific identifiers.

Add neutral generic fixtures, record provider calls/tokens/runtime, document
the hypothesis, failures, results, regressions, and KEEP/REVISE/REMOVE decision,
and stop after the best justified variant. Return `GATE D — RELATION
EXPERIMENT` with the requested old/new metric, checkpoint, runtime, genericity,
and decision comparison. Do not begin Experiment 004 automatically.
