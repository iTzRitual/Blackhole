# Frozen runtime audit prompt

## Initiating instruction

Summary of the human-authored instruction supplied through the referenced pasted-text attachment (this is a summary, not a verbatim transcript):

Perform a rigorous, read-only pre-submission adversarial engineering review of the frozen Blackhole implementation from `implementation-freeze-v1` in a separate `audit/frozen-runtime-v1` worktree. Do not change runtime behavior, inspect any generalization oracle or sibling generalization worktree, run real provider calls, rerun the official baseline, optimize metrics, or score new data. Review durable memory, capture-now/understand-later behavior, ask-time freshness, benchmark coupling, query routing, provider and credential boundaries, Host/PWA security and privacy, attachment semantics, consequential-action safety, evaluation fairness, reproducibility, and deterministic failure modes. Create only the requested audit report and this trajectory's `prompt.md` and `summary.md`, commit them on the audit branch, and return the specified frozen-runtime audit gate with severity counts and verdicts.

The full initiating instruction remains in the user-provided attachment at:

`C:\Users\natan\.codex\attachments\ec323424-5b57-409a-ae90-b74c87c6e5e9\pasted-text-1.txt`

## Explicit constraints retained from the instruction

- Base commit: the commit peeled from annotated tag `implementation-freeze-v1`.
- Prohibited access: `benchmark/generalization/**`, `../Blackhole-generalization-oracle/**`, `../Blackhole-generalization-public/**`, and any sibling worktree containing generalization material.
- Allowed execution: deterministic tests and temporary-data probes only; no Codex inference, provider calls, baseline run, or new scoring.
- Allowed tracked outputs: `docs/audits/FROZEN_RUNTIME_AUDIT.md` and the two files in `trajectories/coding/024-frozen-runtime-audit/`.
- No fixes.
