# Summary of initiating instruction

The initiating user message was:

> /goal Referenced pasted text files:
> - pasted text file: `/Users/natan/.codex/attachments/b8747b4e-3105-43e3-8d03-b5b1a5401779/pasted-text-1.txt`. Read this file before continuing.

The referenced instruction was read before continuing. The following is a
faithful summary of the authorized task (not a verbatim transcript):

> BLACKHOLE — FINAL RELATIVE-DAY TEMPORAL CORRECTNESS HOTFIX.
>
> Work directly on `master`, only from the clean starting SHA
> `ec7665a98082d0f343d0d8e587c5db7eea185fd0`, and stop if the branch,
> worktree, or `origin/master` differs. Reproduce the live deterministic Ask
> failure in which a capture on 2026-08-31 describing “yesterday” was rendered
> as Aug 29 instead of Aug 30. Trace the exact normalized fact/temporal shape
> and deterministic occurrence renderer. Interpret relative temporal meaning
> from capture timestamp plus capture timezone, never provider/retry/Ask/current
> wall-clock time. Add bounded deterministic tests for English and Polish
> today/yesterday/tomorrow, realistic provider temporal shapes, a ZoneInfo DST
> boundary, the occurrence aggregate, and existing deadline/reschedule paths.
> Repair the generic relative-day normalization boundary with local calendar
> semantics. Do not change UI, provider/model/reasoning/batch configuration,
> benchmark/evaluator semantics, V1 oracle/evidence, or frozen benchmark
> behavior. Run every listed regression/static gate. Create this trajectory,
> update the trajectory index, commit directly to `master`, push, verify the
> remote, and only after a full PASS create the single annotated tag
> `hackathon-submission-final`; then stop.

The complete source instruction remains at the referenced attachment path
above; it was not modified or copied into benchmark/evaluator artifacts.
