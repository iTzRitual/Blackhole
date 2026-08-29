# Experiment 005 task instruction

The following is the exact human-provided instruction from
`C:\Users\natan\.codex\attachments\05a28f4f-80ed-4606-8b52-e239f2c70d76\pasted-text-1.txt`.
It is preserved here as the task prompt, not reconstructed from a transcript.

---

# GOAL — EXPERIMENT 005: DUPLICATE-AWARE EVIDENCE CONSOLIDATION

All benchmark/evaluation boundaries remain frozen.

Do NOT modify:

- benchmark cases;
- expected outputs;
- query bundle;
- response-contract-v2;
- evaluator;
- baseline-v1;
- previous experiment artifacts.

Current kept advanced result:

Experiment 004

LQA-0M = 0.8630770101358336
DSCR = 41

Checkpoints:

50  = 0.8888888889
100 = 0.8713728401
150 = 0.8321654040
200 = 0.8598809075

Experiment 003 relation reconciliation is KEEP.
Experiment 004 deterministic selective completeness is KEEP.

Do NOT implement UI.
Do NOT make new general semantic extraction calls.
Do NOT invoke the E004 semantic verifier unless explicitly justified by this
experiment's scope.

--------------------------------------------------
EXPERIMENT QUESTION
--------------------------------------------------

Does the current projection layer discard valid semantic evidence merely
because the raw event carrying that evidence is part of a duplicate group?

Can Blackhole consolidate semantic evidence across duplicate captures while
still treating the underlying real-world occurrence as a single source/event?

--------------------------------------------------
HYPOTHESIS
--------------------------------------------------

A duplicate raw capture should not create a second real-world event or double
financial/task counts.

However, semantic observations extracted from a duplicate capture can still
contain valid information about the same underlying source that an earlier
extraction missed.

The current projection behavior broadly excludes observations from
duplicate-source events.

This may cause valid extracted facts to disappear from current state.

A generic duplicate-group evidence consolidation layer should preserve the
deduplication guarantee while allowing non-conflicting semantic information
from duplicate captures to enrich the canonical source representation.

--------------------------------------------------
PHASE 0 — READ-ONLY FAILURE AUDIT
--------------------------------------------------

Before changing code, inspect the current E004 failures and SQLite state.

Identify remaining defects where:

A. the correct semantic observation already exists;

B. it is attached to an event classified as:
   - exact_duplicate;
   - normalized_duplicate;
   - duplicate;

C. the public projection or current state loses that observation because the
duplicate event is excluded.

Also distinguish:

- extraction omission;
- incorrect relation;
- incorrect semantic role;
- duplicate-projection loss;
- current-state conflict logic;
- unrelated failure.

Produce a diagnostic table.

Use expected DEV output only for offline diagnosis.

Never expose expected output to runtime code.

Estimate the maximum number of current DSCR defects plausibly recoverable by
duplicate-aware evidence consolidation.

If fewer than approximately 3 meaningful defects are in scope, STOP and
recommend skipping E005 rather than manufacturing complexity.

--------------------------------------------------
PHASE 1 — MODEL THE RIGHT SEMANTICS
--------------------------------------------------

Raw duplicate semantics:

Two captures may represent the SAME underlying source/evidence.

Therefore:

duplicate capture != new real-world occurrence.

But:

duplicate capture observations != automatically useless semantic evidence.

Introduce a generic concept of a duplicate/evidence component.

For example:

evt-A
    \\
     duplicate component C1
    /
evt-B

The component has one canonical underlying source identity for counting
purposes but may have semantic observations originating from multiple capture
attempts.

Do NOT rewrite raw events.

Do NOT physically merge/delete raw records.

Raw events remain immutable.

Derived state may consolidate their semantic evidence.

--------------------------------------------------
PHASE 2 — CANONICAL DUPLICATE COMPONENTS
--------------------------------------------------

Use the relationships already accepted by Experiment 003.

Build deterministic connected components only across true duplicate relation
types:

- exact_duplicate;
- normalized_duplicate;
- duplicate.

Do NOT merge:

- similar_not_duplicate;
- meaningful_change;
- correction;
- contradiction;
- task reassignment;
- other relation types.

Select a deterministic canonical source event for each component.

Prefer the earliest original event unless an existing explicit canonical rule
already exists.

Record all component member event IDs as provenance.

--------------------------------------------------
PHASE 3 — SEMANTIC EVIDENCE UNION
--------------------------------------------------

For observations belonging to members of the same duplicate component:

Group by:

subject
predicate

Then consolidate conservatively.

Rules:

1. IDENTICAL SEMANTIC FACT

If multiple duplicate captures yield the same canonical semantic value/status:

retain one projected fact.

Union provenance/source_refs.

Do not count it twice.

2. ADDITIONAL NON-CONFLICTING PREDICATE

If the original extraction has:

status=active

and duplicate extraction additionally has:

renewal_date=2027-01-01

retain both predicates.

The duplicate must not create a second entity/event occurrence.

3. CONFLICTING SEMANTIC VALUES

If duplicate captures of the same underlying source produce incompatible
values for the same subject/predicate:

do NOT simply choose the latest model extraction.

Prefer:
- explicit raw support;
- an existing correction/supersession rule;
- otherwise preserve an uncertainty/conflict state.

Do not use expected output to resolve the conflict.

4. KNOWLEDGE STATUS

Do not silently upgrade inferred/unknown to known merely because another
duplicate extraction exists.

Only upgrade when evidence semantics justify it generically.

5. COUNTS / AGGREGATES

Duplicate evidence consolidation MUST NOT increase:

- transaction count;
- purchase count;
- bill count;
- task count;
- duplicate-event count;
- financial totals;
- consumption totals;

unless the event is independently established as a separate occurrence.

This invariant is critical.

--------------------------------------------------
PHASE 4 — PROJECTION INTEGRATION
--------------------------------------------------

Avoid a special benchmark-only patch inside ResponseProjector.

Prefer fixing the state representation/projection boundary so all downstream
queries see the same consolidated evidence.

The desired conceptual pipeline is:

raw immutable events
→ semantic observations
→ duplicate components
→ consolidated evidence
→ temporal/current-state reconciliation
→ current facts
→ query projection

rather than:

query-specific code deciding whether duplicate observations matter.

Version this projection behavior.

Ensure rebuild_projection() remains deterministic and rebuildable.

--------------------------------------------------
PHASE 5 — GENERIC TESTS
--------------------------------------------------

Add neutral fixtures with unrelated names.

Required cases:

CASE A

Original receipt:
amount=20 EUR

Duplicate extraction:
amount=20 EUR

Expected:
one purchase / one amount occurrence.

CASE B

Original contract extraction:
status=active

Duplicate extraction:
status=active
renewal_date=2027-01-01

Expected:
one contract,
status retained,
renewal_date retained.

CASE C

Original:
amount=20

Duplicate extraction:
amount=25

with no correction evidence.

Expected:
do not silently count 45;
do not arbitrarily choose 25;
preserve appropriate conflict/uncertainty behavior.

CASE D

similar_not_duplicate documents.

Expected:
never consolidate.

CASE E

meaningful_change.

Expected:
never collapse into the duplicate component.

CASE F

duplicate chain:

A <- B <- C

Expected:
one duplicate component with stable canonical identity and provenance from all
members.

No benchmark names/event IDs in tests.

--------------------------------------------------
EVALUATION
--------------------------------------------------

Use the recorded semantic extraction.

No new provider calls.

Evaluation order:

1. unit tests;
2. generator --check;
3. contract smoke;
4. FAST replay;
5. compare to E004;
6. only if FAST/audit supports the hypothesis, run one full 200-event replay.

Record:

- number of duplicate components;
- number of member events;
- number of observations recovered from otherwise excluded duplicate events;
- number of consolidated identical observations;
- number of conflicts preserved;
- aggregate/count invariants;
- local runtime.

--------------------------------------------------
KEEP RULE
--------------------------------------------------

Reference:

LQA = 0.8630770101
DSCR = 41

KEEP if:

- LQA improves by >= approximately 0.015;

OR

- DSCR falls by >= 5;

OR

- a clearly identified projection-loss category materially improves;

AND:

- financial remains 1.0;
- duplicate/change remains 1.0;
- entity resolution does not regress;
- relation reconciliation does not materially regress;
- unknown handling does not regress;
- safety hard-pass remains true.

Do not keep complexity for a tiny cosmetic improvement.

If the audit reveals that duplicate projection loss explains only a trivial
number of remaining errors, REMOVE/SKIP E005.

--------------------------------------------------
NO SCORE CHASING
--------------------------------------------------

This is the LAST development-benchmark optimization experiment before system
freeze.

Do not begin Experiment 006.

After this experiment:

the advanced architecture will be frozen for a post-freeze generalization
evaluation.

Do not recommend another DEV-score experiment merely because some failures
remain.

--------------------------------------------------
TRAJECTORY
--------------------------------------------------

Follow AGENTS.md.

Create:

trajectories/coding/<next>-experiment-005-duplicate-evidence/

Record:

- initial audit;
- hypothesis;
- duplicate component semantics;
- implementation;
- neutral tests;
- FAST result;
- full result if run;
- regressions;
- KEEP / REMOVE;
- protected artifact hash validation.

Update IMPROVEMENT_CHANGELOG.md if this is a meaningful attempted experiment,
including REMOVE if unsuccessful.

--------------------------------------------------
STOP
--------------------------------------------------

Return:

GATE F — DUPLICATE EVIDENCE

Include:

1. how many remaining defects were actually in scope;
2. old projection behavior;
3. new duplicate-component semantics;
4. observations recovered;
5. count/financial invariant evidence;
6. old vs new LQA;
7. old vs new DSCR;
8. checkpoint scores;
9. category changes;
10. regressions;
11. runtime/provider usage;
12. genericity tests;
13. KEEP / REMOVE;
14. exact commit SHA.

Then STOP.

Do not start generalization evaluation automatically.
