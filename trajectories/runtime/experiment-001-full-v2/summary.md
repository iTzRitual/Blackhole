# Runtime trajectory summary: Experiment 001 full projector v2 replay

This non-official 200-event replay reused each of the four public semantic
extraction outputs recorded by `experiment-001-full-v1`. It applied the
query-specific deterministic projector and the then-current SQLite projection
without making provider calls.

The result was schema-valid with no safety or source-integrity failure and
scored LQA-0M `0.7445278102`, DSCR `87`, with `TP=276, FP=96, FN=99`.
