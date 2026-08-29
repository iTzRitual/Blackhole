# Runtime trajectory summary: Experiment 001 FAST retry

This is a failed, non-official diagnostic run over the public first 50 events.
It used ten-event semantic batches through the subscription-first Codex CLI
boundary. The first extraction call returned an empty model output after about
284 seconds, so the runner failed fast and did not produce a scored checkpoint.

The prompt and raw provider output are retained in `calls/`. No prompt tuning
or benchmark change followed this failure; a later successful recorded
extraction was used for controlled projection experiments.
