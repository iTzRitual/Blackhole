# Human instruction

This file records the human-authorized instruction for the benchmark-size calibration task. It is a faithful record of the request, not an exported session transcript.

```text
Before freezing Gate A, add a BENCHMARK SIZE CALIBRATION step.

I am concerned that approximately 80 events may be too short for a strong
2026 long-context model and may fail to exercise the longitudinal-memory
problem.

Do NOT optimize the benchmark merely to exhaust the model context window.

The primary question is whether state quality degrades as changing history
accumulates while the history is still reasonably available to the model.

Before final benchmark freeze:

1. Create a small NON-SCORED calibration dataset that is separate from the
   final benchmark.

2. Generate synthetic longitudinal histories at approximately:

   - 50 events
   - 100 events
   - 200 events
   - 400 events

3. Use simple synthetic facts and state changes.
   Do not reuse final benchmark storylines or ground truth.

4. Measure:

   - approximate input token count;
   - whether the complete history fits in the selected model context;
   - rough query correctness;
   - evidence of temporal/state degradation.

5. Do NOT tune the baseline prompt based on individual calibration failures.

6. Use calibration only to choose a sensible final benchmark length.

7. Prefer a primary benchmark that:

   - remains within the model's usable context where practical;
   - is long enough to expose longitudinal state-maintenance failures;
   - can still be executed repeatedly within hackathon time and cost limits.

My current preferred target is approximately 150-200 events if calibration
supports it.

8. Keep a separate optional stress track at a larger event count, potentially
   250-500 events, if runtime and cost allow.

The stress track must remain secondary and must not replace the realistic
primary benchmark.

Also prioritize STATE CHURN over raw event count.

A useful benchmark should contain repeated changes, corrections,
contradictions, superseded facts, cancellations, missing periods and entity
ambiguity.

For example, ten evolving storylines with multiple state transitions are more
valuable than hundreds of independent static facts.

Return the calibration proposal and estimated cost/runtime impact before
freezing Gate A.
```
