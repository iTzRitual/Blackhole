# Human instruction summary

This file records the human-authorized instruction from the pasted request
“GATE A FINAL — APPROVED WITH ONE REQUIRED EXECUTION RULE”. It is a faithful
summary of the authorization, not an exported or fabricated historical
transcript.

Gate A is approved with these decisions:

- Freeze a 200-event chronological primary benchmark with checkpoints at 50,
  100, 150, and 200.
- Keep 400 events as an optional secondary stress track, but do not design or
  run an 800-event benchmark and do not claim monotonic calibration
  degradation.
- Treat successful full-history execution only as empirical runtime evidence;
  never invent an undocumented Codex context limit.
- Do not repeat the 50/100/200/400 calibration before benchmark freeze.
- Freeze duplicate semantics explicitly as the number of captured duplicate
  events excluding their originals. A distinct duplicate-group metric may be
  separate; do not use an ambiguous generic `duplicate_count`.
- Use Codex CLI with the user's existing authenticated subscription,
  `gpt-5.6-luna`, and `max` reasoning. Do not require or store `OPENAI_API_KEY`
  or Codex authentication material. Claude remains optional and must not delay
  Codex completion.
- Enforce checkpoint query isolation: keep one canonical ingestion thread with
  only the frozen instruction and chronological captures; fork it at each
  checkpoint, ask read-only queries on the fork, capture/score the result, and
  never continue the fork. Use an equivalent isolated mechanism only if fork
  behavior proves unreliable.
- Freeze the final benchmark using a deterministic synthetic-world generator
  with realistic state churn, normalized synthetic content, fixed checkpoints,
  query bundle, schemas, UNKNOWN semantics, duplicate semantics, and scoring
  rules. Create a human-review artifact without requiring manual inspection of
  hundreds of generated assertions.
- Implement the deterministic evaluator with LQA-0M, secondary metrics, safety
  reporting, DSCR, and tests.
- After benchmark/evaluator freeze, implement and run the fair Codex baseline
  with the frozen prompt, canonical ingestion session, isolated checkpoint
  forks, no Blackhole database/state/retrieval/tools/expected outputs, and save
  `eval/results/baseline-v0.json`.
- After the baseline, report LQA-0M, checkpoint scores, DSCR, secondary metrics,
  runtime/tokens, failure examples, whether degradation is evidenced, recall
  versus state-maintenance failures, and one smallest advanced experiment.
  Do not implement the advanced system. End with `GRILL ME — GATE B` and stop.
