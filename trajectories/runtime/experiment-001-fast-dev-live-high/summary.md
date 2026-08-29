# Runtime trajectory summary: Experiment 001 FAST live semantic extraction

This was the successful non-official 50-event live semantic run. It used the
installed authenticated Codex CLI with `gpt-5.6-luna` and reasoning `high`
because the default `max` setting was not practically usable for the earlier
attempt. The extraction call took about 220 seconds and reported 27,831 input,
19,151 output, and 15,020 reasoning tokens.

The deterministic query projection scored LQA-0M `0.6083333333`, DSCR `15`,
with `TP=17, FP=7, FN=8`. The raw prompt/output, state, checkpoint, and
candidate are retained. The four-query baseline slice was `0.2217948718` with
DSCR `41`; this comparison is diagnostic and non-official.
