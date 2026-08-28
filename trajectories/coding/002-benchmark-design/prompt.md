# Human instruction

This file preserves the authentic human instruction that initiated this task. It is not a retrospective reconstruction.

```text
Human approval: move the repository from documentation-scaffolding
to benchmark-design phase.

This task is DESIGN ONLY.

Do not implement the application or baseline yet.

Create a coding trajectory for this task according to AGENTS.md.

Update the repository phase in AGENTS.md so that benchmark contract design,
development benchmark cases, synthetic inputs, and evaluator design are
allowed, but application and baseline implementation remain prohibited.

Then design the benchmark contract.

Before creating benchmark cases, propose:

1. The exact unit of evaluation.
2. The primary metric.
3. Secondary metrics.
4. The structure of one benchmark scenario.
5. The representation of:
   - raw events
   - expected final state
   - known / inferred / unknown
   - entity links
   - tasks
   - obligations
   - deadlines
   - financial observations
   - duplicates
   - corrections
6. The scoring algorithm.
7. How missing information is scored.
8. How contradictions are scored.
9. How we prevent implementation agents from accessing holdout ground truth.
10. How the benchmark can later be reproduced by judges.

Do not create actual cases yet.

Present the benchmark contract for human review and STOP.
```
