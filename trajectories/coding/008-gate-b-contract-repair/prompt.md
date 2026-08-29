# Human instruction summary

This records the human-authorized Gate B blocker instruction supplied in the
pasted attachment `f6db3a7d-98eb-492e-8fd1-1ed2f0ebc29a`. It is a faithful
summary of the instruction, not a verbatim historical transcript.

Gate B is blocked because the recorded baseline-v0 score is not a valid measure:
the response/evaluator contract mismatch produced zero true positives, malformed
records, and confounded recall versus state-maintenance failures. Preserve the
existing run as invalid evidence and do not change benchmark facts.

Repair only the public evaluation/output contract. Diagnose raw model outputs,
the query bundle, schema, expected assertions, canonicalization, and malformed
records; replace evaluator-internal state-key guessing with an explicit public
semantic assertion representation or expose a derivable identifier grammar;
clarify ambiguous query wording; and add an independent non-scored smoke test.

Freeze response-contract-v2 without changing the substantive baseline-v1 prompt,
then run exactly one corrected official 200-event Codex baseline with the same
model, reasoning, checkpoint isolation, and no application state. Preserve the
invalid run, save a clearly versioned valid result, create a labeled 50-event
fast development slice, document evidence and semantic failure categories, do
not implement the advanced Blackhole system, and stop at `GRILL ME — GATE B
VALID`.
