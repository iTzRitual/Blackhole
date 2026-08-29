# Representative runtime trajectory: longitudinal change

This is a representative deterministic local-demo trace, not a provider
transcript. It exercises current-versus-history lookup after a subscription
price change.

## Input and state

- Question: `What subscriptions am I paying for?`
- Follow-up projection: `What subscription price changes are supported by the history?`
- Seed state: 14 captures, with no provider call.

## Instructions and operations

- Read the current structured projection through `GET /api/query`.
- Read the historical price projection through a second `GET /api/query`.
- Do not infer a total from the presence of a charge; return the stored facts
  and their evidence references.

## Result

- Current subscription price: 10.99 EUR per month, source `demo-003`.
- Latest observed charge: 8.99 EUR, source `demo-002`.
- Historical prices: 8.99 EUR/month from `demo-001`, then 10.99 EUR/month from
  `demo-003`.
- The earlier value remains history; it is not overwritten.

## User-visible outcome

The Ask view renders a current Subscriptions section and a separate Price
history section. The condensed result is in `trace.json`.
