# Agent guidance

## Current repository phase

This repository is in the benchmark-design phase. Benchmark contract design, development benchmark cases, synthetic inputs, and evaluator design are allowed in this phase. Do not add application code, baseline implementation, production infrastructure, executable evaluation implementation, holdout cases, holdout expected outputs, or final benchmark ground truth unless the project owner explicitly changes the scope.

The human-authorized size-calibration step is a narrow exception: non-scored synthetic histories and their visible calibration-only oracle may live under `benchmark/calibration/`. That oracle is not final benchmark ground truth, must remain separate from `benchmark/dev/` and `benchmark/holdout/`, and must not be used to tune a baseline prompt.

The remaining empty directories are represented by placeholders so Git can preserve the intended layout. A placeholder is not permission to begin implementing the corresponding subsystem. Development benchmark content must follow the approved contract; evaluator-owned holdout material remains outside the implementation-agent trust boundary.

## Non-negotiable invariants

1. **Raw sources are immutable.** Preserve the original capture, receipt, document, or observation exactly as received. Corrections and interpretations are new records with provenance; they do not rewrite the source.
2. **Derived state is rebuildable.** Any index, entity state, task, obligation, financial aggregate, or attention item must be reproducible from immutable inputs plus versioned transformation rules.
3. **Unknown is a first-class result.** Missing, unreadable, ambiguous, or not-yet-checked information must not be converted into zero, false, an empty value, or an assertion of completion.
4. **Deterministic work is executable work.** Arithmetic, date calculations, comparisons, duplicate checks, and financial aggregation must be performed by deterministic code or SQL when implementation begins. LLMs may interpret or propose; they are not the calculator of record.
5. **Consequential actions require approval.** Sending, paying, cancelling, signing, changing an account, deleting evidence, or making another consequential external change must wait for explicit user confirmation.
6. **Evidence and provenance matter.** Derived facts should be traceable to the source material and the transformation that produced them.
7. **Protect the benchmark.** Never inspect, modify, copy, summarize, infer from, or expose holdout expected outputs. Keep evaluator-owned holdout material outside implementation-agent access in real runs; the current repository contains no final or holdout ground truth. The explicit calibration-only oracle is not a holdout substitute and must not leak into final benchmark artifacts.

## Working rules

- Read the relevant document before changing its subject area.
- Keep changes narrow and coherent.
- Record durable product or architectural decisions in `docs/DECISIONS.md`.
- Record benchmarked experiments and measured improvements in `IMPROVEMENT_CHANGELOG.md`.
- Do not commit secrets, personal data, unredacted user content, model credentials, or evaluator-only artifacts.
- Preserve raw data and benchmark boundaries when renaming or reorganizing files.
- Prefer explicit status and provenance over silent fallback behavior.
- When a requirement is ambiguous, document the assumption and its risk rather than inventing hidden behavior.
- Do not claim evaluation success without a reproducible run record and clearly identified inputs.

## Before application or baseline implementation begins

Any move from benchmark design to application or baseline implementation should first establish:

- the source and derived-state boundaries;
- the representation of known, inferred, and unknown values;
- the user-approval boundary for actions;
- the evaluator-owned holdout access model; and
- a minimal reproducible evaluation protocol.

## Agent work documentation protocol

The project is being developed with coding agents and must preserve enough evidence to reconstruct the important development decisions, experiments, failures, retries, and human checkpoints.

Documentation is part of completing a task, not optional cleanup after implementation.

### What counts as a meaningful task

A task is meaningful if it does one or more of the following:

- changes architecture or persistence;
- introduces or changes agent behavior;
- changes runtime prompts or tools;
- adds or removes a feature;
- changes evaluation logic;
- introduces an experiment;
- responds to an observed benchmark failure;
- changes entity resolution, memory, reconciliation, provenance, or state handling;
- changes task, deadline, financial, or aggregation behavior;
- materially changes reproducibility, runtime cost, or reliability.

Small formatting changes, typo fixes, comments, and trivial refactors do not require a dedicated trajectory unless they are part of a meaningful task.

## Coding trajectory protocol

Before beginning a meaningful task, create:

`trajectories/coding/<NNN>-<short-task-name>/`

At minimum the directory should contain:

- `prompt.md`
- `summary.md`

If an authentic session transcript can be exported from the coding-agent environment, also preserve it as:

- `transcript.txt`
- or `transcript.json`

Never fabricate, reconstruct, or paraphrase a transcript and present it as the original transcript.

### prompt.md

Before implementation begins, record the actual human instruction that initiated the task.

Preserve the instruction as faithfully as possible.

If the task originated from a broader discussion, summarize only the instruction that directly authorized the work and identify it as a summary rather than pretending it is a verbatim prompt.

### summary.md

At the end of the task, record:

- Goal
- Agent/tool used
- Initial hypothesis, if applicable
- Important implementation decisions
- Tools/actions used
- Failures encountered
- Retries or changed approaches
- Human feedback or checkpoints
- Evaluation performed
- Result
- Regressions or unresolved issues
- Final decision
- Related git commit

Do not invent information that was not observed.

## Experiment protocol

Every meaningful experiment must have a written hypothesis before implementation.

Use this lifecycle:

1. Identify an observed problem or failure.
2. Write the hypothesis.
3. Record the current metric before making the change.
4. Implement the smallest change that can test the hypothesis.
5. Run the same evaluation protocol.
6. Compare results.
7. Record regressions, runtime, and cost where available.
8. Decide: KEEP, REVISE, or REMOVE.
9. Update `IMPROVEMENT_CHANGELOG.md`.
10. Stop before beginning the next experiment unless explicitly instructed to continue.

Do not bundle unrelated experiments into one evaluation result.

Do not continue adding complexity merely because an experiment technically works. A change should be kept because evidence shows that it improves the intended user outcome or materially improves reliability.

## Improvement changelog rules

`IMPROVEMENT_CHANGELOG.md` is an experimental history, not a general development log.

Add an entry when:

- a baseline is established;
- an experiment changes measurable behavior;
- an attempted improvement fails;
- a component is removed after evaluation;
- a significant failure changes the design direction;
- the final system combines previously validated improvements.

Each entry should contain:

- Stage / experiment identifier
- Problem observed
- Hypothesis
- What changed
- Evaluation method
- Metric before
- Metric after
- Regressions
- Runtime/cost impact when known
- Decision: KEEP / REVISE / REMOVE
- Learning

Never rewrite historical experiment results because a later implementation performs better.

Append a new experiment instead.

## Decision log rules

Use `docs/DECISIONS.md` for durable product and engineering decisions such as:

- SQLite versus another persistence mechanism;
- immutable event storage;
- derived-state rebuildability;
- known/inferred/unknown semantics;
- provenance rules;
- deterministic versus LLM responsibilities;
- user-approval boundaries;
- benchmark access boundaries.

A decision does not need to appear in `IMPROVEMENT_CHANGELOG.md` unless it was tested as an experiment with evidence.

## Evaluation evidence

Machine-readable evaluation outputs must be stored under:

`eval/results/`

Use stable identifiers such as:

- `baseline-v0.json`
- `experiment-001-memory.json`
- `experiment-002-entity-resolution.json`
- `final.json`

Reported metrics in documentation must point to an actual evaluation result.

Never manually adjust evaluation output to match an expected narrative.

Never change expected benchmark results because the implementation disagrees with them.

If the benchmark itself is discovered to be incorrect, stop and request human review before changing ground truth.

## Runtime trajectory protocol

Runtime trajectories are separate from coding trajectories.

Store representative executions of the Life Inbox agent under:

`trajectories/runtime/<NNN>-<case-name>/`

A runtime trajectory should make it possible to understand:

- input received;
- relevant state before execution;
- agent instructions;
- tools invoked;
- tool results;
- reasoning-relevant decisions that are externally observable from the trace;
- retries or verification;
- resulting state;
- final user-visible outcome.

Do not expose benchmark holdout answers in runtime trajectories.

## Git protocol

Create coherent commits corresponding to meaningful development stages.

Prefer descriptive commit messages such as:

- `docs: establish project constraints`
- `benchmark: freeze evaluation set v1`
- `baseline: implement stateless extraction`
- `experiment: add persistent entity memory`
- `experiment: add state reconciliation`
- `revert: remove verifier with no measurable gain`

Avoid vague messages such as:

- `update`
- `changes`
- `stuff`
- `final`

Do not rewrite or squash away experiment history during active development unless explicitly instructed.

## Task completion checklist

A meaningful task is not complete until the agent has checked:

- the requested design or implementation work is complete;
- relevant tests or validation checks pass when applicable;
- evaluation was run when behavior changed;
- evaluation output was saved;
- trajectory summary was updated;
- `IMPROVEMENT_CHANGELOG.md` was updated when applicable;
- `docs/DECISIONS.md` was updated when applicable;
- unresolved regressions are documented;
- no benchmark boundary was violated;
- no secrets or private user data were added;
- the change has a coherent git commit.

The final response for a meaningful task must state:

1. what changed;
2. why;
3. what was tested;
4. measured result if applicable;
5. regressions or unresolved issues;
6. whether the change should be KEEP, REVISE, or REMOVE;
7. which trajectory and evaluation files contain the evidence.
