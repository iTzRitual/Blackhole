# Runtime trajectory summary: Experiment 001 malformed-query replay

This non-official replay reused the recorded public 50-event semantic
extraction from the initial FAST work and requested a fresh scoped model query.
The query response ended without its final root JSON brace and was rejected by
the strict parser. No score was accepted from this run.

The replay prompt and raw response are retained in `calls/`. The later parser
change was deliberately limited to an unambiguous closing-delimiter repair and
was evaluated as a separate run.
