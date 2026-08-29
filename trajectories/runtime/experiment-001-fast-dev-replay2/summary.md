# Runtime trajectory summary: Experiment 001 repaired-query replay

This non-official diagnostic reused the same public 50-event extraction and
applied the bounded closing-delimiter JSON repair. The fresh model-query path
was schema-valid after repair but scored LQA-0M `0.0990021008` with DSCR `56`
(`TP=6, FP=37, FN=19`) on the four-query FAST slice. It was not kept as the
primary query path.

The evidence is in the candidate/result files and `calls/`. The failure led to
the deterministic response projector; it did not lead to baseline-prompt
tuning or any benchmark/ground-truth change.
