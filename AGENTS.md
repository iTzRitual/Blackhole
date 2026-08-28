# Agent guidance

## Current repository phase

This repository is in the documentation and design-scaffolding phase. Do not add application code, production infrastructure, benchmark cases, benchmark expected outputs, or evaluation implementation unless the project owner explicitly changes the scope.

The empty directories are represented by placeholders so Git can preserve the intended layout. A placeholder is not permission to begin implementing the corresponding subsystem.

## Non-negotiable invariants

1. **Raw sources are immutable.** Preserve the original capture, receipt, document, or observation exactly as received. Corrections and interpretations are new records with provenance; they do not rewrite the source.
2. **Derived state is rebuildable.** Any index, entity state, task, obligation, financial aggregate, or attention item must be reproducible from immutable inputs plus versioned transformation rules.
3. **Unknown is a first-class result.** Missing, unreadable, ambiguous, or not-yet-checked information must not be converted into zero, false, an empty value, or an assertion of completion.
4. **Deterministic work is executable work.** Arithmetic, date calculations, comparisons, duplicate checks, and financial aggregation must be performed by deterministic code or SQL when implementation begins. LLMs may interpret or propose; they are not the calculator of record.
5. **Consequential actions require approval.** Sending, paying, cancelling, signing, changing an account, deleting evidence, or making another consequential external change must wait for explicit user confirmation.
6. **Evidence and provenance matter.** Derived facts should be traceable to the source material and the transformation that produced them.
7. **Protect the benchmark.** Never inspect, modify, copy, summarize, infer from, or expose holdout expected outputs. Keep evaluator-owned holdout material outside implementation-agent access in real runs; the current repository contains no ground truth.

## Working rules

- Read the relevant document before changing its subject area.
- Keep changes narrow and coherent. Record material design changes in `docs/DECISIONS.md` and `IMPROVEMENT_CHANGELOG.md`.
- Do not commit secrets, personal data, unredacted user content, model credentials, or evaluator-only artifacts.
- Preserve raw data and benchmark boundaries when renaming or reorganizing files.
- Prefer explicit status and provenance over silent fallback behavior.
- When a requirement is ambiguous, document the assumption and its risk rather than inventing hidden behavior.
- Do not claim evaluation success without a reproducible run record and clearly identified inputs.

## Before implementation begins

Any move from scaffolding to implementation should first establish:

- the source and derived-state boundaries;
- the representation of known, inferred, and unknown values;
- the user-approval boundary for actions;
- the evaluator-owned holdout access model; and
- a minimal reproducible evaluation protocol.
