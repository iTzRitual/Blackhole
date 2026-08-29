# Failed attempt 001

This record preserves the observed operational failure before any successful
candidate was produced.

- Invocation: `python -m app.advanced_runner` with the frozen g01 configuration from the authorized blind-run prompt.
- Return code: `1`.
- Provider calls: `0`.
- Candidate output: not produced.
- Failure point: raw-event insertion before semantic extraction.
- Observed exception: `ValueError: raw event requires event_id, integer sequence, and payload object` at `app/state_store.py:192`.
- Public fixture fact checked structurally: all three public generalization scenarios contain 80 raw events whose `payload` values are strings.

The normal capture API wraps a string capture in an object before insertion, but
using that path for this run would change the received public raw record and its
declared payload hash. No runner, application, benchmark, prompt, or public
fixture was modified. No quality retry was performed.
