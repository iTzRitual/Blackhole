# Runtime trajectory summary: Experiment 001 full semantic extraction and projector v1

This was the fresh non-official 200-event milestone run against the frozen
public development scenario, using checkpoints 50/100/150/200 and four fresh
chronological semantic extraction calls. Codex CLI used `gpt-5.6-luna` with
reasoning `high`; `max` was not practically usable for this milestone. The
calls returned successfully and took 887.453 seconds in total. Reported usage
was 132,514 input, 72,711 output, and 53,751 reasoning tokens.

The first projector revision used a catch-all state dump for unsupported query
families and scored LQA-0M `0.1589548193`, DSCR `299`, with `TP=127, FP=1900,
FN=248`. This was a measured failed architecture revision, not a baseline
change. The raw extraction, prompts, projected states, checkpoints, and result
are retained so later deterministic projector revisions can be compared fairly.

The Codex CLI emitted a non-fatal Windows hook warning about a filename being
too long; all four extraction calls returned. No expected output or holdout
material was supplied to the provider.
