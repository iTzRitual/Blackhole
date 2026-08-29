# Human-authorized task instruction

This file records the human-authorized instruction for trajectory 017. It is
copied from the user-provided attachment
`C:\Users\natan\.codex\attachments\7b6c0e8e-b253-4d70-a3e5-06f043c7f050\pasted-text-1.txt`.
It is a task record, not a fabricated or reconstructed historical transcript.

---

# GOAL — DEFERRED END-TO-END BLACKHOLE INGESTION

The development-benchmark optimization phase is finished.

Experiment 005 is KEEP and is the FINAL development-benchmark optimization
experiment.

Current latest kept advanced result:

LQA-0M = 0.8695006212
DSCR = 40

Previous milestones remain preserved:

E004:
LQA-0M = 0.8630770101
DSCR = 41

E003:
LQA-0M = 0.8157180034
DSCR = 45

Official baseline remains frozen:

LQA-0M = 0.3014914553
DSCR = 277

Do NOT begin Experiment 006.

Do NOT optimize against scenario-001 further.

Do NOT modify:

- benchmark cases;
- expected outputs;
- query bundle;
- response-contract-v2;
- evaluator;
- baseline-v1;
- existing experiment results.

--------------------------------------------------
CONCURRENT UI WORK
--------------------------------------------------

UI/UX work is happening independently in another git worktree.

This goal is BACKEND / PRODUCT-RUNTIME ONLY.

Do NOT modify:

- app/web/**
- CSS;
- HTML;
- frontend JavaScript;
- PWA assets;
- visual design.

Do not switch branches or create another worktree.

Remain in the current main backend worktree.

Avoid unnecessary edits to app/web_app.py as well.

Prefer introducing clean service boundaries that the UI can integrate with
later.

--------------------------------------------------
PRODUCT DECISION
--------------------------------------------------

Blackhole intentionally does NOT analyze every capture synchronously.

The core capture UX is:

CAPTURE
→ SAVED
→ END INTERACTION

This is intentional.

The user should not wait for:

- semantic classification;
- entity resolution;
- relationship reconciliation;
- duplicate analysis;
- suggestions;
- follow-up questions;
- model reasoning.

The product is designed around reducing capture-time cognitive friction.

However:

semantic work is DEFERRED, not absent.

Information captured earlier must become useful when the user later asks
Blackhole for value.

--------------------------------------------------
TARGET PRODUCT LOOP
--------------------------------------------------

Implement this real backend lifecycle:

raw capture
→ immutable storage
→ pending derived-processing state

later:

process pending
→ semantic extraction
→ deterministic selective completeness
→ retrieval-assisted relation reconciliation
→ duplicate-aware evidence consolidation
→ rebuildable SQLite projection

then:

query / attention / memory
→ use updated structured state

Conceptually:

MORNING

"pick up the kids Tuesday"
→ Saved.

"Adobe apparently increased again"
→ Saved.

"insurance might end in November"
→ Saved.

NO MODEL WORK REQUIRED AT CAPTURE TIME.

EVENING

"What needs my attention this week?"

Blackhole:
→ notices pending captures
→ processes them
→ updates structured state
→ answers from Blackhole-owned state.

--------------------------------------------------
ARCHITECTURE REQUIREMENT
--------------------------------------------------

Extract the smallest reusable ingestion engine from the existing KEPT
benchmark architecture.

Do NOT create a second independent implementation of semantic ingestion.

The benchmark runner already contains working pieces for:

- semantic extraction;
- completeness;
- relation recovery;
- duplicate-aware consolidation;
- StateStore;
- rebuild_projection.

Create a production-facing service boundary conceptually similar to:

IngestionEngine

with operations such as:

process_event(...)
process_pending(...)
processing_status(...)
retry_failed(...)

Exact API is your design decision.

The implementation must be generic.

It must NOT know:

- benchmark scenario IDs;
- benchmark event IDs;
- expected values;
- benchmark entity names;
- evaluator query IDs.

--------------------------------------------------
PROCESSING STATUS
--------------------------------------------------

Raw sources remain immutable.

Do NOT update raw event JSON to represent processing progress.

Create a SEPARATE derived processing-state representation.

It should minimally track:

- event_id;
- processing status;
- processing version;
- attempt count;
- last attempted timestamp;
- last successful timestamp where applicable;
- last error;
- extractor version;
- completion version;
- relation-recovery version.

Suggested lifecycle:

pending
processing
processed
failed

Use a schema that remains rebuildable and auditable.

If an existing event already contains historical demo metadata such as
semantic_status, do not rely on it as the authoritative runtime processing
state.

--------------------------------------------------
PROCESSING ORDER
--------------------------------------------------

Pending events must normally be processed chronologically.

Preserve temporal semantics.

Use bounded batches.

Do not let a later event become authoritative merely because it happened to be
processed before an earlier capture.

If processing one batch fails:

- preserve previously valid state;
- record the failure;
- allow retry;
- do not corrupt the pending queue.

--------------------------------------------------
IDEMPOTENCY
--------------------------------------------------

This is a hard requirement.

Running:

process_pending()

twice with no new captures must NOT:

- duplicate observations;
- duplicate relationships;
- double financial totals;
- duplicate tasks;
- change duplicate counts;
- introduce new current-state transitions.

Use stable transformation/run identities where useful.

Add explicit tests proving idempotency.

--------------------------------------------------
PROVIDER
--------------------------------------------------

Primary semantic provider remains:

Codex CLI
subscription-first
locally authenticated externally

Blackhole must not:

- request provider credentials;
- read auth files;
- copy auth tokens;
- persist auth tokens.

Reuse the existing provider boundary.

For real semantic processing use the currently approved runtime model and
configuration used by the KEPT advanced architecture.

Do not introduce Claude in this goal.

--------------------------------------------------
LATEST KEPT PIPELINE
--------------------------------------------------

Deferred processing must incorporate the KEPT architecture through E005:

1. immutable raw capture;
2. semantic extraction;
3. E004 deterministic evidence scanning / selective completeness;
4. E003 retrieval-assisted relation reconciliation;
5. E005 duplicate-aware evidence consolidation;
6. rebuildable current/history projection;
7. deterministic calculations.

Do not regress those mechanisms merely because they were originally introduced
inside benchmark/replay flows.

Where possible refactor common code rather than copy-pasting it.

--------------------------------------------------
NO EXPECTED-OUTPUT DEPENDENCY
--------------------------------------------------

The production ingestion service must be executable with:

- raw events;
- public ontology/configuration;
- existing Blackhole state;
- provider.

It must not require:

- benchmark expected JSON;
- evaluator;
- score artifacts;
- DEV failure diagnostics.

Add a test that exercises ingestion using completely neutral synthetic data
outside benchmark/dev.

--------------------------------------------------
ASK-TIME FRESHNESS
--------------------------------------------------

Expose a backend boundary suitable for future Ask integration.

For example:

ensure_state_fresh()

Conceptually:

if pending_count == 0:
    return immediately

otherwise:
    process_pending()
    rebuild state

Then the caller may execute a structured query.

Do NOT implement frontend Ask integration in this goal.

Do NOT modify app/web/**.

Do NOT modify app/web/**.

Provide only a clean Python/service API that UI work can call after merge.

--------------------------------------------------
EXPLICIT PROCESSING COMMAND
--------------------------------------------------

Provide a UI-independent command for judges/development.

Prefer something such as:

python -m app.process_pending

or:

python scripts/process_pending.py

It should:

- detect pending count;
- process pending captures;
- report concise status;
- avoid printing secrets;
- return non-zero on unrecoverable failure.

Example output:

Blackhole
3 pending captures
3 processed
state rebuilt

Do not dump raw model chain-of-thought.

--------------------------------------------------
DEFERRED PRODUCT DEMO TEST
--------------------------------------------------

Build an automated deterministic integration test using a fake provider.

The test must demonstrate the actual product philosophy.

FLOW A — BASIC

1. create clean DB;
2. capture:
   "Renewal for CloudBox is 2027-02-01."
3. confirm raw event exists immediately;
4. confirm capture returns without semantic state;
5. confirm processing state = pending;
6. run process_pending();
7. confirm derived structured fact now exists;
8. confirm processing state = processed.

FLOW B — LATER CORRECTION

capture:
"CloudBox costs 20 EUR"

later:
"CloudBox will cost 25 EUR from March"

process chronologically.

Expected:
- history preserves 20 EUR;
- current state reflects supported later value;
- raw history preserved.

FLOW C — UNKNOWN

capture:
"The insurance renewal date is somewhere in November, I need to check."

Expected:
do not fabricate an exact date.

FLOW D — DUPLICATE

submit the same raw capture twice.

Expected:
raw events both preserved;
semantic evidence may consolidate;
real-world occurrence/financial totals are not doubled.

FLOW E — IDEMPOTENCY

run process_pending twice.

Expected:
second run produces zero new semantic effects.

FLOW F — FAILURE + RETRY

fake provider fails for one event.

Expected:
status = failed;
raw capture preserved;
state remains valid;
retry can later process it successfully.

Use neutral names and values not present in benchmark scenario-001.

--------------------------------------------------
OPTIONAL REAL CODEX SMOKE
--------------------------------------------------

After deterministic tests pass, you MAY perform ONE small real Codex CLI smoke
test with 1-3 neutral captures if runtime availability makes this cheap.

Do not use benchmark examples.

Do not perform a 200-event live run.

Record provider calls/tokens/runtime if exposed.

If real provider execution is inconvenient, do not block completion.

The deterministic fake-provider integration test is mandatory.

--------------------------------------------------
CAPTURE LATENCY PRINCIPLE
--------------------------------------------------

Do not accidentally make append_capture() or equivalent synchronously call the
provider.

Capture path must remain:

validate
→ immutable insert
→ derived pending status
→ return Saved

Any semantic provider call on the synchronous capture request is a regression
against the product design.

Add a test proving capture works when NO provider exists.

--------------------------------------------------
PROCESS-ON-ASK SEMANTICS
--------------------------------------------------

Implement backend support for:

capture during the day
→ no semantic work

later:

ensure_state_fresh()
→ process pending
→ query current state

This does NOT mean every future Ask must necessarily process everything.

A more selective strategy may be explored later.

For the MVP, processing all pending captures at Ask-time is acceptable.

Document this as an engineering tradeoff.

--------------------------------------------------
CONSEQUENTIAL ACTIONS
--------------------------------------------------

Deferred processing may identify:

- payment;
- cancellation;
- signing;
- sending;
- account change;

as proposed actions.

It must NEVER execute them.

Existing human-approval boundary remains unchanged.

Add or retain a test showing:

semantic detection of a proposed consequential action
!= execution.

--------------------------------------------------
TRAJECTORY
--------------------------------------------------

Follow AGENTS.md.

Create the next coding trajectory such as:

trajectories/coding/017-deferred-ingestion/

Record:

- human instruction;
- product rationale;
- architecture before;
- architecture after;
- refactoring choices;
- failures/retries;
- fake-provider integration results;
- optional real provider smoke;
- benchmark regression check;
- commit.

This is a PRODUCT/ARCHITECTURE milestone.

Do not pretend it is Experiment 006.

Do not add a DEV score experiment entry merely because product runtime changed.

Update docs/DECISIONS.md because deferred semantic processing is a durable
product decision.

Update IMPROVEMENT_CHANGELOG.md only if appropriate under its existing rules;
do not manufacture another benchmark experiment.

--------------------------------------------------
DOCUMENTATION
--------------------------------------------------

Update relevant documentation so it clearly states:

CAPTURE NOW.
UNDERSTAND LATER.

Explain:

- capture is synchronous and cheap;
- semantic interpretation is deferred;
- pending state is derived, not raw-source mutation;
- structured state belongs to Blackhole;
- Ask can require fresh processing;
- provider auth remains external;
- processing failures are retryable.

Do NOT rewrite video/UI documentation broadly because UI is being developed in
another worktree.

Avoid touching:
- docs/VIDEO_SCRIPT.md
- docs/VIDEO_SHOT_LIST.md

unless absolutely required to fix a factual contradiction.

--------------------------------------------------
BENCHMARK REGRESSION CHECK
--------------------------------------------------

After the product-runtime refactor:

run deterministic replay of the latest KEPT E005 result.

Expected reference:

LQA-0M = 0.8695006212
DSCR = 40

The goal is NO REGRESSION.

Do not optimize benchmark code during this validation.

If score changes:

STOP and diagnose the refactor.

Do not silently accept a score increase or decrease caused by altered benchmark
semantics.

Frozen benchmark/evaluator/baseline hashes must remain unchanged.

Do not rerun expensive baseline-v1.

--------------------------------------------------
VALIDATION
--------------------------------------------------

Run at minimum:

- full stdlib tests;
- new deferred-ingestion integration tests;
- benchmark generator --check;
- contract smoke;
- compileall;
- E005 deterministic replay;
- git diff check.

Verify protected benchmark/baseline artifacts are unchanged.

--------------------------------------------------
STOP CONDITION
--------------------------------------------------

When complete return:

DEFERRED INGESTION GATE

Include:

1. architecture introduced;
2. files/modules added or refactored;
3. exact synchronous capture behavior;
4. processing-status schema;
5. process_pending behavior;
6. idempotency mechanism;
7. retry/failure behavior;
8. before/after example with a NEW neutral capture;
9. correction example;
10. UNKNOWN example;
11. duplicate example;
12. provider independence at capture time;
13. optional real Codex smoke result;
14. test count;
15. E005 replay result after refactor;
16. frozen artifact integrity confirmation;
17. remaining product limitations;
18. commit SHA.

STOP.

Do NOT:
- start a shadow/generalization benchmark;
- start E006;
- touch UI/UX work;
- implement background scheduling;
- implement Claude.
