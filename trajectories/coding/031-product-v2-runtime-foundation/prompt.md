# Product V2 runtime foundation — task prompt

Source: the human-provided pasted text file
`C:\Users\natan\.codex\attachments\2fd6c534-2aa0-47e2-9d7d-fc096c7c7a4e\pasted-text-1.txt`,
referenced by the user message `/goal ... Read this file before continuing.`

The following is a faithful summary of the instruction that directly
authorized this task (it is not an invented transcript):

Build the post-evaluation BLACKHOLE PRODUCT V2 runtime foundation as real
personal memory product development. Use a separate worktree
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-runtime`, branch
`product/v2-runtime`, based exactly on master SHA
`68b7b15d353b12cffb65a770f8583aa0ebb849dd`; do not work in the main
worktree, merge to master, or access local oracle/scoring worktrees.

Preserve the frozen V1R1 benchmark, oracle, scoring evidence, and historical
runtime. Do not tune against benchmark/generalization expected outputs or
V1R1 failures. Do not add production infrastructure, a Claude adapter,
holdout material, or evaluator-owned ground truth. Product V2 is not part of
the reported V1R1 generalization score.

Implement a zero-organization product with immediate durable capture followed
by background semantic processing. Capture must validate, store immutable raw
evidence, return before provider completion, and enqueue durable pending work.
Processing must have one owner per event, crash/stuck recovery, retryable
failures, idempotency, chronological consistency, atomic semantic commits
where possible, and Host-observable status.

Introduce a separate open-world memory representation for generic entities,
facts, events, tasks, deadlines, relationships, documents, transactions,
observations, and proposed actions. Preserve provenance, known/inferred/unknown
semantics, contradictions, corrections, supersession, duplicate evidence, and
immutable source references without inventing facts or requiring benchmark
ontology subjects/predicates.

Add deterministic time-aware Attention state for due/starts times, deadlines,
relative captures, open/completed/cancelled status, upcoming and overdue items.
Give semantic extraction capture timestamp, local timezone, and current date/time
context; normalize final timestamps and scheduling in deterministic code. Update
Attention from background ingestion, not from viewing it. Make no medical or
ADHD claims.

Replace Product V2 Ask keyword/fixed-query behavior with natural-language
retrieval over processed structured memory and source evidence, deterministic
calculations where appropriate, and optional bounded Codex synthesis. Avoid
replaying all capture history for every question; support ordinary personal
questions; use no provider for simple deterministic questions when avoidable;
choose and document a reasonable product model/reasoning configuration rather
than defaulting to benchmark `max`.

Persist real immutable local attachments in a collision-safe content-addressed
blob store inside `BLACKHOLE_HOME`. Support text-only, attachment-only, and
combined captures with filename, MIME type, byte length, hash, and source
linkage. Investigate actual installed Codex CLI file/image support; never claim
OCR or invent unsupported content. Preserve unsupported/unreadable status.

Implement immediate capture Undo as a retract/void semantic: raw evidence is
never deleted, retracted evidence stops contributing to active derived state,
rebuilds honor retractions, and Host API exposes a short-lived suitable action.

Keep V1 reproduction intact. Provide deterministic migration or a clear failure
for existing local data; never silently corrupt BLACKHOLE_HOME. Address scoped
reliability findings such as stuck processing recovery, atomic retries,
stale-state behavior, avoiding provider-triggering GETs, POST semantic Ask,
safer CLI invocation where supported, and no token exposure. Do not expand to
LAN pairing, HTTPS, or cloud relay.

Add deterministic, no-live-provider tests covering immediate capture latency,
eventual processing, provider failure and retryable evidence, crash/stuck
recovery, duplicate processing, relative time normalization, Attention
upcoming/overdue state, attachment-only capture and blob integrity, retract/
Undo rebuild behavior, open-world facts, deterministic Ask, and mocked-provider
semantic Ask. Existing V1 tests must continue to pass.

Create `trajectories/coding/031-product-v2-runtime-foundation/` with
`prompt.md` and `summary.md`; update only the architecture/product docs needed
to distinguish frozen V1 from post-evaluation Product V2; do not rewrite
historical trajectories. Commit only to `product/v2-runtime`. Run the
deterministic test suite and return a `PRODUCT V2 RUNTIME FOUNDATION GATE`
report with PASS/PARTIAL/FAIL, branch/base/final SHAs, architecture and
behavior summaries, model/reasoning configuration, tests, limitations, and
changed files. Do not claim visual/UI completion.
