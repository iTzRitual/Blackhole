# Representative runtime trajectory: unknown information

This is a representative deterministic local-demo trace, not a provider
transcript. It checks that a missing amount remains explicit uncertainty.

## Input and state

- Question: `What information is incomplete?`
- Seed state includes a repair note whose quoted amount was not stated.
- No provider call was made.

## Instructions and operations

- Read the unresolved projection through `GET /api/query`.
- Preserve the `unknown` status and its reason.
- Do not substitute zero, false, an empty value, or an estimated amount.

## Result

The answer contains `repair_note.quoted_amount` with
`knowledge_status: unknown`, `unknown_reason: not_stated`, and source
`demo-013`. No numeric value is emitted.

## User-visible outcome

The Ask view renders the item under **Incomplete information** as “Unknown ·
Not stated.” The condensed result is in `trace.json`.
