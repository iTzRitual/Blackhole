# Runtime trajectory summary

## Run

- Run: `final-h2h-20260831T143014Z`
- Frozen Product V2 commit: `cc0cca8e8d9c3a5ab0955f365ea71c639cac7548`
- Sealed manifest SHA-256: `5b38b14aac4e3f4ab88a7cff6a5d5d411f7275c8579e501a3da0ec7128243393`
- Input: four newly authored synthetic worlds, 20 captures each, checkpoints
  at 7/14/20, plus one post-checkpoint Undo query.

## Input and state boundary

System A received only the live raw captures for each query in a fresh
stateless Codex CLI call. System B received the same captures through the
normal Product V2 HTTP boundary, built a fresh temporary Home per world, and
was queried only after the normal processing queue was idle. Expected
assertions were kept outside both system prompts and read only by the
post-run scorer. No V1 expected output, holdout material, private transcript,
or Product V2 acceptance fixture was used.

## Observable execution

For Product V2, the trace is: capture receipt → durable pending row → normal
background extraction → `/api/v2/state` checkpoint inspection → `/api/v2/ask`
→ post-checkpoint `/api/v2/retract` for the Undo case → final Ask. All 80
captures processed on their first attempt with zero processing failures; all
13 query responses were schema-valid. The provider made 80 extraction calls
and the run issued 13 normal Ask requests. The raw-memory leg completed 13
fresh Codex calls with no call or schema failures.

## Failures and audit corrections

The first harness attempt stopped before a valid Product V2 result because of
a runner field-name bug (`query_id` versus the sealed `query_ids` list). No
semantic result was produced from that attempt. The runner was corrected,
the unchanged cases/expected/scoring/spec were resealed, and the complete run
was repeated from fresh Homes. After completion, a logger-label collision was
found: Product V2 event IDs overwrote the logger event-name field. Extraction
call counts were recovered deterministically from the recorded processing
success boundaries; semantic responses and scores were not changed.

## Result

The raw run record remains in the separate disposable local clone used for
execution. The sanitized machine-readable result committed to the main repository is
`eval/results/final-h2h-001-summary.json`. The run is descriptive post-freeze
evidence, not an optimization result or a replacement for the frozen V1
benchmark.
