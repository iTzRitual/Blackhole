# Runtime trajectory summary: baseline-fast-dev-retry2

- Label: `DEV FAST / NOT OFFICIAL SCORE`
- Scenario prefix: first 50 public events
- Contract: `response-contract-v2`
- Model/configuration: Codex CLI `0.150.0-alpha.12.2`, `gpt-5.6-luna`, reasoning `max`
- Query subset: `q-subscriptions-current`, `q-tasks-state`,
  `q-duplicates-changes`, `q-unresolved`
- Canonical/session isolation: one canonical session and one discarded atomic
  query fork; no expected output or evaluator was supplied to the provider
- Parser result: four query responses parsed successfully
- Runtime: `398.234` seconds total; query fork `394.406` seconds
- Query usage: `28,058` input tokens and `32,597` output tokens

This slice is diagnostic only and is not an official score or a replacement for
the four-checkpoint baseline. Earlier non-official attempts exposed a relative
trajectory-path metadata error and an incomplete output-file recovery case;
those attempts remain in their separate directories. The final runner now
normalizes paths and falls back to a complete agent message when an output file
is not parseable.
