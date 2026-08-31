# Task prompt

Source: the user message that initiated this task, received 2026-08-31.

```text
/goal Referenced pasted text files:
- pasted text file: /Users/natan/.codex/attachments/0e46f3bf-0f2d-4ae5-9029-fcae7dc85441/pasted-text-1.txt. Read this file before continuing.
```

The referenced pasted text was read in full before implementation. It is the
direct task specification titled “BLACKHOLE — FINAL DEMO PRESENTATION POLISH”.
The specification authorizes a bounded final presentation/UX hotfix directly
on `master`, starting from `0ecd49443ef7c85367a4375b0b8dacbcccc2d0c6`, with a
clean worktree and `origin/master` at the same SHA. It limits changes to Ask,
Capture, Attention, and Memory presentation/UX, focused regression coverage,
local visual review, a maximum of 3 synthetic captures and 4 Ask messages for
live validation, the listed full gate, evidence updates, and final submission
preparation.

The specification explicitly forbids reopening Product V2 architecture,
semantic extraction, model/reasoning/batch/benchmark/evaluator/V1 behavior,
noun- or language-specific translation tables, provider configuration changes,
production infrastructure, holdout access, and any benchmark optimization.
It requires preserving raw evidence and provenance, avoiding attribution in
ordinary answers, removing redundant Ask footer and Capture “Saved.” copy,
fixing Ask scrolling and composer/navigation spacing, Capture text alignment,
Attention Done alignment, and Memory presentation without destructive
translation. It also requires focused tests, sanitized live evidence if live
validation occurs, trajectory index updates, a coherent commit, push, final
SHA checks, and a PASS/PARTIAL/FAIL gate report before stopping.
