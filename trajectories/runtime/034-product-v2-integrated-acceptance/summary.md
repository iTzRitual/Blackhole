# Product V2 integrated acceptance runtime trajectory

This representative trajectory records the reproducible integrated acceptance
execution. It contains no benchmark holdout answers or evaluator-owned
material.

## Input received

The public dogfood case corpus supplied 50 ordinary-life English and Polish
capture/ask/state cases, including text, attachment-only, combined capture,
correction, duplicate, unknown, Attention, arithmetic/change, retry, restart,
and Undo dimensions. Each case ran in a fresh temporary Product V2 Home.

## State before execution

The V2 SQLite store was initialized and empty for each case. Attachment cases
used the committed small synthetic fixtures. The acceptance provider was a
deterministic local fixture with explicit failure modes; no live provider or
credential/token configuration was used.

## Agent instructions and externally observable decisions

The runtime used the Product V2 Host contract: save immutable raw evidence
first, keep semantic processing pending or retryable, process in chronological
order, preserve exact attachment bytes, project Attention/Memory from derived
state, keep unknowns explicit, and never execute consequential actions. The
runner drained `/api/v2/process` before semantic assertions, then separately
measured the default background-worker boundary.

## Tools invoked

- `POST /api/v2/capture` for text, attachment, and combined captures;
- `GET /api/v2/state` and `GET /api/v2/processing` for read-only state;
- `POST /api/v2/process` for bounded processing;
- `POST /api/v2/retry` after an intentional provider failure;
- `POST /api/v2/ask` for bounded retrieval and synthesis;
- `POST /api/v2/retract` for semantic Undo;
- attachment blob retrieval by SHA-256; and
- Host close/reopen for restart durability.

## Tool results and verification

The runner verified durable save before semantic work, duplicate idempotency,
explicit failure and retry, pending-state preservation across restart, exact
attachment bytes and hash, current Attention lifecycle, open-world retrieval,
deterministic totals/change answers, source references, uncertainty, and safe
no-evidence behavior. The normal-worker probe used a `120 ms` deterministic
provider delay and recorded capture return before processing completion.

## Resulting state and user-visible outcome

The machine-readable result at
`eval/results/product-v2-integrated-acceptance.json` reports `50/50 PASS`, all
quality gates passing, and no `PARTIAL`, `FAIL`, or `NOT TESTED` case. The
recorded latency probe returned capture in `110.706 ms` and completed
processing in `239.226 ms`.

## Retries and final decision

Earlier runner attempts exposed adapter, evaluator flattening, retrieval,
Attention mapping, and attachment assertions; each was corrected and the
runner progressed from 35/50 to 46/50, 49/50, and finally 50/50. The final
decision is **KEEP** for the authorized post-freeze Product V2 integration.
