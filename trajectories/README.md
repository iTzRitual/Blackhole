# Trajectories

Trajectories are audit and evaluation artifacts showing how an agent or workflow processed a task. They are not the source of truth for user data or derived state.

## Layout

- `coding/`: trajectories from repository and implementation work.
- `runtime/`: trajectories from future product or benchmark runs.

## Minimum metadata

A future trajectory should identify the run, revision, prompt/model versions, input reference, tool events, outputs, approvals, and outcome. It should make it possible to understand what happened without embedding unnecessary sensitive source content.

## Safety rules

- Redact secrets, credentials, and unnecessary personal information.
- Never include holdout expected outputs or evaluator-only scoring details in implementation-facing trajectories.
- Keep proposed actions separate from approved actions.
- Preserve links to immutable source identifiers and derived-artifact versions where appropriate.
- Treat trajectories as append-only records; corrections should be new annotations or new trajectory records.

Trajectory format and storage tooling remain deliberately unspecified until the evaluation and runtime contracts are implemented.
