# Runtime trajectory summary

## Run

Normal Product V2 web-app lifecycle smoke after the provider-adapter repair,
using a fresh temporary Home and the installed externally authenticated Codex
CLI. The run was executed from the isolated `product/v2-provider-fix`
worktree.

## State before

Fresh Home initialized by `python -m app.host init`; no captures, semantic
facts, Attention items, or retries existed.

## Instructions and provider boundary

Product V2 used its versioned semantic interpreter prompt, model
`gpt-5.6-luna`, reasoning `high`, ephemeral Codex CLI execution, read-only
sandbox, JSONL output, strict temporary output schema, and stdin prompt input.
Authentication remained owned by the normal Codex ChatGPT login. No token was
read or recorded.

## Inputs

1. `Klucze do piwnicy są u mamy.`
2. `Odbieram dzieci za 10 minut.`

## Tool and process events

- Normal `app.web_app` started and served the health endpoint.
- Both POST `/api/v2/capture` calls returned immediately with `Saved.` and
  `processing: pending`.
- The managed background worker invoked the provider once per event.
- Both provider calls returned usable structured semantic output and exited
  successfully; no retry occurred.
- GET `/api/v2/state` and GET `/api/v2/processing` were used for observation.
- POST `/api/v2/ask` was issued exactly twice, for the two authorized questions.
- The server was stopped after the smoke.

## Resulting state

Memory contained a known location fact for `Klucze do piwnicy` with value
`u mamy` and source reference `provider-smoke-basement`. Attention contained an
open appointment `Odebrać dzieci`, due ten minutes after capture, with source
reference `provider-smoke-kids`. Processing ended at 2 processed, 0 pending,
0 processing, 0 failed, and one attempt per event.

## Ask results

The task question returned the useful children Attention item with its source
reference. The keys question was incorrectly routed to that unrelated
Attention item because the deterministic router treated the standalone Polish
preposition `do` as a task/time marker. This was not a provider failure. A
small deterministic router correction and regression test were added after the
smoke; no further live Ask or capture was run because the authorized limit had
already been reached.

## Outcome

Provider semantic processing: PASS. Overall prescribed live Product V2 gate:
PARTIAL pending a fresh normal-launch validation of the corrected keys Ask.
