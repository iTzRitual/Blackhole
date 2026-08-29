# Runtime trajectory summary: Experiment 001 deterministic projector v1

This non-official FAST run replayed the recorded public 50-event extraction and
used SQLite state projection plus the first deterministic query projector. It
scored LQA-0M `0.5924242424`, DSCR `16`, with `TP=17, FP=8, FN=8`.

The state database, checkpoint response, extraction input, deterministic query
record, and result are retained. Financial arithmetic, date handling, and
state projection happened in code; no provider query was required for this
replay.
