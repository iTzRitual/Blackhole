# Runtime trajectory 019 — real neutral Host/PWA-equivalent smoke

## Status

Authentic HTTP-level run through the integrated local transport and the
authenticated local Codex CLI. This is product-runtime evidence, not a
benchmark score or Experiment 006. No transcript, chain-of-thought, token, or
raw provider stderr was recorded.

## Input and flow

The run used a temporary Blackhole Home and these neutral captures:

1. `Northstar Cloud costs 18 EUR per month.`
2. `Northstar Cloud will cost 22 EUR per month from 2027-03-01.`

The HTTP sequence was `GET /api/health`, `GET /api/host/status`, two
`POST /api/capture` calls, `GET /api/processing`, `POST /api/query` with
`What subscription price changes do I know?`, `GET /api/state`, and a final
processing-status read. The full safe request/response trace is in
`trace.json`.

## Observed result

- Health returned HTTP 200 without provider discovery work.
- Both captures returned HTTP 200, `saved=true`, `message=Saved.`, and
  `processing.status=pending`; the pre-Ask queue contained two pending events.
- Ask returned HTTP 200 after approximately 29.5 seconds and processed both
  events through the real Codex CLI, rebuilt SQLite state, and returned a
  deterministic subscription-history answer containing the 18 EUR and 22 EUR
  values.
- The resulting Host state contained two raw captures, three current facts,
  and one relationship. The second extraction included the effective date in
  the stored state, although the bounded history answer did not surface that
  field.
- Safe readiness reported `codex-cli 0.150.0-alpha.12.2`, authenticated and
  ready. Usage counts were not exposed by the HTTP transport and are recorded
  as unavailable rather than inferred.

## Limitation

The neutral real call did not resolve both mentions to one stable
`northstar_cloud` entity. It emitted capture-scoped subjects, so the smoke
proves the transport, deferred provider call, normalization, rebuild, and
state-backed answer path, but not reliable novel-entity linking. This was
reported rather than hidden or repaired by tuning the runtime prompt after the
run. The deterministic fake-provider HTTP suite separately proves the intended
same-entity correction path.

## Evidence boundary

The temporary Home was discarded after the run. `trace.json` contains only
neutral synthetic text, event IDs, safe HTTP payloads, timing, provider
readiness metadata, processing versions, and structured state. It contains no
benchmark entity, expected output, evaluator artifact, credential, raw CLI
output, or chain-of-thought.
