# Experiment 004 task instruction

The following is the exact human-provided instruction from
`C:\Users\natan\.codex\attachments\080e8f09-3470-44e9-8a3d-44a3ad68eed0\pasted-text-1.txt`.
It is preserved here as the task prompt, not reconstructed from a transcript.

---

# GOAL — EXPERIMENT 004: SELECTIVE SEMANTIC COMPLETENESS VERIFICATION

The benchmark, evaluator, baseline, response-contract-v2, and all prior kept
experiments are frozen.

Do NOT modify:

- benchmark cases;
- expected outputs;
- query bundle;
- response-contract-v2;
- evaluator;
- baseline-v1;
- existing recorded experiment results.

Current kept advanced system:

Experiment 003

LQA-0M = 0.8157180034018269
DSCR = 45

Checkpoint LQA:

50  = 0.8518518519
100 = 0.8189738502
150 = 0.7821654040
200 = 0.8098809075

Relation reconciliation = 0.6696428571
Duplicate/change category = 1.0

Experiment 003 is KEEP.

Do NOT redesign relation reconciliation in this experiment.

Do NOT implement UI.

--------------------------------------------------
EXPERIMENT QUESTION
--------------------------------------------------

Can Blackhole detect when an otherwise successful semantic extraction omitted
important information that is explicitly present in the raw capture, and
selectively repair only those captures?

This experiment targets extraction completeness, NOT historical retrieval.

--------------------------------------------------
HYPOTHESIS
--------------------------------------------------

The current semantic extraction occasionally misses explicitly stated
structured facts such as:

- dates;
- identifiers;
- amounts;
- lifecycle states;
- action/approval facts;

even when those values are plainly present in the immutable raw source.

A cheap deterministic evidence-coverage check followed by a selective scoped
semantic verification call should improve current-state, temporal, task,
obligation, contract, and safety recall without reprocessing all captures.

The verifier should run only when deterministic evidence indicates that the
existing extraction may be incomplete.

--------------------------------------------------
PHASE 0 — FAILURE AUDIT
--------------------------------------------------

Before implementation, perform a read-only audit of the CURRENT Experiment 003
result.

Use development expected output only for offline failure diagnosis.

Do NOT expose expected output to runtime code or provider prompts.

Classify remaining errors into:

- source explicitly contains missing fact;
- source contains fact but semantic role is ambiguous;
- extracted fact exists but projector loses it;
- extracted fact exists but current-state reconciliation loses it;
- expected assertion is not defensibly recoverable from the raw capture;
- other.

Pay particular attention to:

- q-contract-dates;
- q-tasks-state;
- q-approval-boundary;
- q-subscriptions-current;
- q-recent-changes;
- obligation/deadline;
- current_state;
- temporal_history;
- safety.

Produce a diagnostic table before implementing.

Estimate how many of the remaining 45 DSCR defects are plausibly extraction
omissions.

Do not modify benchmark semantics based on the audit.

--------------------------------------------------
PHASE 1 — DETERMINISTIC EVIDENCE SCANNER
--------------------------------------------------

Implement a generic raw-source evidence scanner.

Its job is NOT to interpret the full meaning of the capture.

Its job is to identify high-confidence structural anchors in raw evidence.

Examples:

DATES

Recognize explicit ISO-like dates such as:

2026-02-01
2027-01-31

Do not invent dates from vague phrases in this phase.

AMOUNTS

Recognize explicit monetary values and currency tokens.

IDENTIFIERS

Recognize stable document/account/receipt/policy/contract-like identifiers
conservatively.

Examples of structural form:

ABC-123
POL_928
R-1005

Do not hardcode benchmark IDs.

TEMPORAL/LIFECYCLE CUES

Record lexical cues around anchors such as:

signed
effective
starts
expires
expiry
renewal
renews
due
deadline
cancelled
completed
replaced

ACTION/APPROVAL CUES

Record explicit language around:

send
pay
transfer
cancel
sign
approve
approval
execute

The scanner outputs evidence anchors only.

Example conceptually:

{
  "event_id": "...",
  "anchors": [
    {
      "type": "date",
      "raw_value": "2026-02-01",
      "context": "effective 2026-02-01"
    }
  ]
}

The scanner MUST NOT directly create semantic facts unless the mapping is
structurally unambiguous and generic.

--------------------------------------------------
PHASE 2 — COVERAGE GAP DETECTOR
--------------------------------------------------

Compare evidence anchors against the semantic observations already stored for
that event.

Goal:

detect likely omissions without using benchmark expected output.

Examples:

Raw source contains:

- two distinct explicit dates;
- one contract identifier;

but stored semantic observations represent:

- only one date;
- no identifier.

This is a likely coverage gap.

Raw source contains:

"27 EUR"

and extraction already contains:

{amount: 27, currency: EUR}

No gap.

Do not require one observation for every number/date in prose.

Use conservative heuristics.

False-positive verification triggers are acceptable in small numbers, but the
detector must not blindly reprocess every capture.

Record a reason for every flagged event.

Example:

{
  "event_id": "...",
  "reasons": [
    "explicit identifier not represented",
    "2 raw dates but only 1 date-valued observation"
  ]
}

--------------------------------------------------
PHASE 3 — DETERMINISTIC COMPLETION FIRST
--------------------------------------------------

Before using the provider, test whether some gaps can be safely filled
deterministically.

Only derive a semantic observation when mapping from raw source to public
predicate is unambiguous.

Examples that MAY be safe:

"signed 2026-01-02"
→ signed_date

"expires 2027-06-30"
→ expiry_date

"renews on 2027-01-31"
→ next_renewal

Only if generic lexical mapping is clear.

Do not implement a giant regex semantic parser.

Do not add benchmark entity names or expected values.

If deterministic completion alone materially improves FAST evaluation, measure
it separately before adding verification.

--------------------------------------------------
PHASE 4 — SELECTIVE SEMANTIC VERIFIER
--------------------------------------------------

Only for captures where a coverage gap remains after deterministic completion,
allow a scoped provider call.

Use:

Codex CLI
gpt-5.6-luna
reasoning=high

Do not use a persistent conversation.

The verifier receives ONLY:

- one raw capture;
- its existing semantic observations;
- deterministic evidence anchors;
- public ontology / value shapes;
- relevant current subject state if needed.

It does NOT receive:

- expected outputs;
- evaluator diagnostics;
- benchmark scoring information;
- unrelated raw history;
- complete scenario history.

Prompt responsibility:

"Check whether the existing extraction omitted an explicitly supported
semantic fact. Return only missing or corrected observations. Do not repeat
already represented observations."

The verifier should be biased toward NO CHANGE.

Valid output:

{
  "add_observations": [...],
  "replace_observations": [...],
  "no_change": false
}

or

{
  "add_observations": [],
  "replace_observations": [],
  "no_change": true
}

All returned observations must still pass normal contract canonicalization and
source provenance checks.

Never allow the verifier to mutate raw events.

--------------------------------------------------
PHASE 5 — MERGE POLICY
--------------------------------------------------

Verifier results are derived observations.

Preserve:

- original extraction version;
- verifier version;
- source event;
- reason verification was triggered;
- provider metadata;
- provenance.

Do not silently overwrite historical observations.

Corrections must use normal supersession/correction semantics where needed.

A verifier observation that conflicts with existing extraction should not
silently win unless the raw evidence clearly establishes the replacement.

Otherwise preserve the conflict.

--------------------------------------------------
SELECTIVITY METRICS
--------------------------------------------------

Record:

- total captures;
- captures scanned;
- captures flagged;
- captures repaired deterministically;
- captures sent to verifier;
- verifier NO_CHANGE count;
- observations added;
- observations replaced;
- provider input/output/reasoning tokens;
- provider runtime.

A major success condition is NOT only accuracy.

We also want evidence that verification is selective.

For example:

200 total captures
→ 20 flagged
→ 9 provider verification calls

would be more architecturally interesting than:

200 captures
→ 200 second-pass model calls.

Do not optimize toward those example numbers.

Measure the actual result.

--------------------------------------------------
EVALUATION ORDER
--------------------------------------------------

1. Add neutral unit fixtures.

Do not use benchmark brands/entities.

Include examples such as:

- contract containing signed/effective/renewal dates;
- insurance document with policy ID and expiry;
- task with explicit deadline;
- transfer requiring approval;
- prose containing an irrelevant number/date that should NOT become a fact.

2. Run deterministic scanner/gap detector tests.

3. Replay current Experiment 003 extraction.

4. Test deterministic completion variant first.

5. Run FAST development evaluation.

6. Only if justified, enable selective semantic verifier.

7. FAST evaluate again.

8. If materially better with no important regression, run ONE full 200-event
evaluation.

Do not rerun baseline.

Do not redo general semantic extraction for every event.

--------------------------------------------------
KEEP RULE
--------------------------------------------------

Current kept reference:

LQA = 0.8157180034
DSCR = 45

KEEP E004 if one of the following occurs:

- overall LQA improves by approximately >= 0.02;
- DSCR decreases by >= 8;
- a major currently weak category improves materially;

AND there is no important regression in:

- financial;
- duplicate/change;
- entity resolution;
- unknown handling;
- safety;
- relation reconciliation.

These are decision guides, not optimization targets.

Do not retain complexity for a tiny score increase.

--------------------------------------------------
GENERICITY
--------------------------------------------------

No benchmark entity names, event IDs, expected answers, or storyline-specific
conditions may appear in runtime implementation.

The mechanism should reasonably apply to arbitrary future captures.

Prefer structural concepts:

source type
anchor type
canonical subject
predicate
value shape
temporal cue

over named merchants/services.

--------------------------------------------------
TRAJECTORY
--------------------------------------------------

Follow AGENTS.md.

Create:

trajectories/coding/<next>-experiment-004-selective-verification/

Include:

- exact human prompt;
- failure audit;
- hypothesis;
- scanner design;
- gap detector design;
- deterministic completion result;
- verifier decision;
- FAST metrics;
- final metrics if run;
- provider usage;
- false-positive verification triggers;
- regressions;
- KEEP / REVISE / REMOVE.

Update IMPROVEMENT_CHANGELOG.md.

Preserve all failed variants.

--------------------------------------------------
STOP
--------------------------------------------------

Do not begin Experiment 005.

When E004 is complete return:

GATE E — SELECTIVE VERIFICATION

Include:

1. remaining-error audit;
2. number of extraction omissions found;
3. deterministic scanner design;
4. gap detector design;
5. deterministic completion contribution;
6. whether semantic verifier was required;
7. number of verifier calls out of 200 captures;
8. provider tokens/runtime;
9. old vs new LQA;
10. old vs new DSCR;
11. category improvements/regressions;
12. checkpoint scores;
13. genericity evidence;
14. KEEP / REVISE / REMOVE;
15. strongest remaining failure.

Then STOP.

---
