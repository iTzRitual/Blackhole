# Runtime trajectory 020 — post-consolidation neutral Host smoke

## Status

Authentic bounded HTTP-level run through the consolidated Host/PWA transport
and the already-authenticated local Codex CLI. This is product-runtime
evidence, not a benchmark score or Experiment 006. No transcript, chain of
thought, token value, raw provider stderr, benchmark input, or expected output
was recorded.

## Input and flow

The harness used a temporary Blackhole Home and the neutral synthetic captures:

1. `Northstar Cloud costs 18 EUR per month.`
2. `Northstar Cloud will cost 22 EUR per month from 2027-03-01.`

It exercised health and readiness reads, two immediate captures, processing
status, one Ask query, state reconstruction, and a final processing-status
read. The safe trace is in `trace.json`.

## Observed result

- Health, both captures, and Ask returned HTTP 200.
- Both captures returned `Saved.` with pending processing; the Ask boundary
  processed two events through the real Codex CLI.
- Ask completed in approximately 20.7 seconds and returned a deterministic
  subscription-history answer containing the 18 EUR and 22 EUR observations.
- The rebuilt state contained two captures, three current facts, one
  relationship, zero pending events, and zero failed events.
- Readiness reported `codex-cli 0.150.0-alpha.12.2`, authenticated and ready.
  Provider usage remained unavailable through the safe HTTP transport and was
  not inferred.

## Limitation

As in the earlier neutral smoke, the real provider call emitted
capture-scoped subjects instead of resolving both mentions to one stable
`northstar_cloud` entity. The effective date was stored, but the bounded
history answer did not surface it. This limitation was recorded rather than
addressed by prompt tuning after the run; the deterministic fake-provider
tests cover the intended same-entity correction path.

## Evidence boundary

The temporary Home was discarded by the harness. `trace.json` contains only
neutral synthetic text, safe HTTP payloads, timings, readiness metadata,
processing versions, and structured state. It contains no credentials,
benchmark material, holdout ground truth, evaluator internals, raw CLI output,
or chain of thought.
