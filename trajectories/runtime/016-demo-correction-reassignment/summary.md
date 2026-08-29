# Representative runtime trajectory: correction and reassignment history

This is a representative deterministic local-demo trace, not a provider
transcript. It reads an evolving task state and its linked change records.

## Input and state

- Question: `What tasks are active or completed, and what reassignment or cancellation history is supported?`
- Follow-up question: `What changed recently?`
- Seed state contains the original owner, a reassignment, and a later
  cancellation for the family-pickup task.
- No provider call was made.

## Instructions and operations

- Read task state and relation projections through `GET /api/query`.
- Keep the original source references while showing the current task state.
- Do not execute the cancellation or treat the relation record as a new
  external action; it is already a captured historical observation in the
  synthetic seed.

## Result

- `family_pickup` owner is currently `Sam`, source `demo-005`.
- `family_pickup` status is `cancelled`, source `demo-006`.
- The linked reassignment is `demo-005 → demo-004`, changed field `owner`.
- The linked cancellation is `demo-006 → demo-004`, changed field `lifecycle`.
- The separate recent-change projection also reports the recorded subscription
  price change from `demo-003` to `demo-002`.

## User-visible outcome

The Memory and Ask views show current task fields alongside evidence-backed
relationship records. The condensed result is in `trace.json`.
