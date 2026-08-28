# Human instruction

This file records the human-authorized instruction supplied in the pasted Gate A pre-freeze revision. It preserves the instruction as provided; it is not an exported session transcript.

```text
GATE A PRE-FREEZE REVISION AND RUNTIME CALIBRATION

Gate A is NOT approved yet.

The size-calibration artifact is useful and should be kept, but it currently
contains token/context estimates only. It does not yet contain the actual
long-chat model correctness run required to choose benchmark length.

Before Gate A can be frozen, perform the work below.

Do not implement the final application or advanced agent yet.

Follow AGENTS.md documentation and trajectory requirements automatically.

--------------------------------------------------
1. PRODUCT FRAMING
--------------------------------------------------

Update the product framing before benchmark freeze.

Product name:

Blackhole

Descriptor:

"A zero-organization life inbox."

Do not perform disruptive code/path renames just for branding.

The core problem is:

Traditional productivity systems often make capture itself into a second task.

A person wants to get something out of their head quickly, but tools may
require choosing:
- a database;
- folder;
- project;
- category;
- due date;
- priority;
- tags;
- properties.

Blackhole's principle is:

CAPTURE NOW.
ORGANIZE LATER.

The intended user includes people who experience high executive-function
friction, attention overload, forgetfulness, or low tolerance for
organizational overhead.

ADHD may be mentioned as a strong example of this user need, but do NOT make
medical claims.

Do not describe the product as treating ADHD, improving symptoms, diagnosing
ADHD, or providing medical assistance.

Add these UX principles:

1. SILENT BY DEFAULT

Normal capture should ideally be:

input
→ saved

Do not make the user maintain a conversation merely to capture information.

2. INTERRUPT ONLY WHEN USEFUL

Proactive interruption should be reserved for things such as:
- deadlines;
- reminders;
- unresolved conflicts that matter;
- required decisions;
- important changes.

3. OBSERVE, DO NOT JUDGE

The system should surface factual observations without moralizing about user
behavior.

Example:

Prefer:

"18 confirmed energy-drink observations in August; observed spend: X; data
coverage: 22/28 days."

Avoid unsolicited judgments such as:

"You are drinking too many energy drinks."

Interpretation or advice may be provided when explicitly requested.

Update:
- README.md
- docs/PRODUCT_SPEC.md
- docs/DECISIONS.md

Keep the benchmark hypothesis focused on longitudinal state maintenance.

--------------------------------------------------
2. PRIMARY BENCHMARK SCOPE
--------------------------------------------------

The primary benchmark must isolate the main hypothesis:

LONGITUDINAL STATE MAINTENANCE.

Do NOT make OCR or vision quality a primary confound.

The benchmark may represent modalities such as:
- receipt
- document
- image-derived record

using synthetic text or normalized extracted content.

Actual image/document upload may be demonstrated later in the product demo,
but primary benchmark errors should primarily measure state maintenance,
not OCR quality.

Document this decision.

--------------------------------------------------
3. PRIMARY METRIC REVISION
--------------------------------------------------

Keep the name:

Longitudinal Query Accuracy at Zero Maintenance (LQA-0M)

But revise scoring so unsupported/hallucinated assertions are penalized.

For each fixed query:

TP = correct supported assertions
FP = unsupported or incorrect assertions produced by the system
FN = expected assertions omitted by the system

Use:

query_score = TP / (TP + FP + FN)

If TP + FP + FN = 0, define and document deterministic empty-answer behavior.

Then:

checkpoint_score =
mean(query scores at that checkpoint)

LQA-0M =
mean(all fixed query scores across all primary checkpoints)

Do NOT use arbitrary weight 2 versus weight 1 in the primary score.

Report critical categories separately:

- current-state accuracy;
- temporal/history accuracy;
- known/inferred/unknown handling;
- obligations/deadlines;
- deterministic financial correctness;
- duplicate/change handling;
- contradiction handling;
- safety violations.

Critical safety violations remain a separate hard failure and are never hidden
inside the average.

Precision/recall/F1 may remain secondary diagnostics.

--------------------------------------------------
4. MAINTENANCE METRIC REVISION
--------------------------------------------------

Remove MIR-90 as the primary maintenance proxy.

Do not spend hackathon time solving a minimum-repair optimization problem.

Replace it with:

DSCR — Distinct State Corrections Required

Definition:

After the zero-maintenance run, count distinct underlying state defects that a
human would need to correct.

Multiple query failures caused by the same underlying state defect count once.

Examples:

- one incorrect Adobe entity link causing multiple wrong answers:
  1 correction;

- one wrong Adobe current price causing several checkpoint failures:
  1 correction;

- Orange March stored as 0 instead of UNKNOWN:
  1 correction;

- a reassigned task incorrectly remaining active:
  1 correction.

Report:

- total DSCR;
- DSCR per 100 captured events;
- correction categories.

Do NOT claim DSCR equals real human minutes.

Wall-clock human maintenance time may only be exploratory evidence.

--------------------------------------------------
5. FAIR BASELINE
--------------------------------------------------

The baseline remains:

ONE CONTINUOUS LONG GENERAL-PURPOSE AI CONVERSATION.

It receives:

- the same chronological captures;
- the same fixed checkpoint questions;
- complete available history when it fits;
- one reasonable frozen personal-life-admin system prompt.

It receives NO:

- SQLite state;
- entity database;
- persistent external memory;
- entity-resolution tool;
- temporal reconciliation engine;
- hidden summary;
- deterministic financial database;
- special retrieval layer.

Do not deliberately weaken it.

Prefer the SAME exact semantic runtime model for baseline and advanced system,
not merely the same model family, unless technically impossible.

Freeze the baseline system prompt before the first scored benchmark run.

The fact that the advanced system receives databases, deterministic tools, and
specialized state mechanisms is intentional.

Those mechanisms are the experimental treatment.

Document resource, token, runtime, and cost differences transparently.

--------------------------------------------------
6. ACTUAL MODEL CALIBRATION
--------------------------------------------------

The existing 50/100/200/400 calibration histories are KEEP.

However, token estimates alone are insufficient to select final benchmark
length.

Select and pin the runtime provider/model that will be used for the baseline
and, where practical, the advanced semantic reasoning calls.

First inspect available runtime configuration WITHOUT printing or exposing
credentials.

If a usable provider credential is already configured:
proceed.

If no runtime model credential is available:
complete every preparation step that does not require it, then STOP and ask
the human for exactly the provider/API configuration required.

Do not expose environment-variable values.

Record:

- provider;
- exact model identifier;
- documented context limit;
- tokenizer/token counting method where available;
- relevant temperature/configuration.

Freeze ONE reasonable baseline system prompt before running calibration.

Do not tune that prompt after seeing calibration errors.

Run the same baseline prompt and same fixed calibration query bundle at:

50 events
100 events
200 events
400 events

Measure for every size:

- exact/actual input tokens where available;
- output tokens;
- context utilization;
- LQA-style deterministic correctness;
- current-state errors;
- stale-state errors;
- previous-state errors;
- missed corrections;
- contradiction collapse;
- false certainty / UNKNOWN errors;
- duplicate/change errors;
- runtime;
- approximate API cost.

The complete conversation history must remain available whenever it fits.

Do not summarize or truncate it silently.

--------------------------------------------------
7. OPTIONAL 800-EVENT CALIBRATION
--------------------------------------------------

After the 50/100/200/400 run:

If 400 events:
- fits comfortably in the selected model context;
- remains practical in cost/runtime;
- and shows little or no meaningful state-quality degradation,

then extend CALIBRATION ONLY to approximately 800 events.

Do this at most once before returning for human review.

Generate the 800-event calibration as a continuation/prefix-compatible
synthetic stream where practical.

Do NOT increase event count merely to force context overflow.

If 800 approaches or exceeds a practical context boundary, report that fact
instead of silently truncating.

The 800-event run remains calibration evidence, not the official benchmark.

--------------------------------------------------
8. STATE CHURN MATTERS MORE THAN RAW LENGTH
--------------------------------------------------

When interpreting calibration, separate:

A. literal context exhaustion;

from:

B. state-maintenance degradation while full history remains available.

The second is more relevant to the product hypothesis.

Do not conclude that a long chat is inadequate merely because context was
artificially exhausted.

Also inspect whether the calibration is sufficiently diagnostic.

The final benchmark should contain realistic state churn such as:

- superseded facts;
- price changes;
- cancellation intention versus actual cancellation;
- changes of mind;
- corrections;
- unresolved contradictions;
- duplicate versus similar-but-distinct records;
- missing periods;
- ambiguous entity references;
- reassigned tasks;
- replaced contracts/policies;
- old versus current state.

A benchmark with fewer high-churn events may be more diagnostic than a much
larger collection of independent facts.

Do not adversarially sabotage the baseline with unnatural trick questions.

--------------------------------------------------
9. FINAL BENCHMARK GENERATION STRATEGY
--------------------------------------------------

Do not require the human owner to manually verify hundreds of assertions.

Propose a deterministic synthetic-world generator:

canonical hidden world state
→ chronological user-facing events
→ deterministic checkpoint ground truth

The final timeline should be authored from explicit storyline/state-machine
rules.

Expected state should be generated deterministically where possible.

Human approval should focus on:

- storyline semantics;
- state-transition rules;
- query definitions;
- subjective inference rules;
- a sample of critical transitions;
- explicit UNKNOWN/contradiction cases.

The implementation agent must still not gain access to protected holdout
ground truth.

--------------------------------------------------
10. GATE A RETURN
--------------------------------------------------

After the actual model calibration is complete, DO NOT implement the baseline
benchmark run or advanced application yet.

Return a new Gate A report containing:

1. selected provider/model;
2. actual token/context measurements;
3. correctness at 50/100/200/400 and 800 if run;
4. failure category counts at each size;
5. whether degradation occurred while full history still fit;
6. recommended PRIMARY event count;
7. recommended optional stress event count;
8. estimated benchmark runtime/cost;
9. final LQA-0M formula;
10. final DSCR definition;
11. proposed fixed checkpoint/query matrix;
12. deterministic synthetic-world generation plan;
13. updated Blackhole user/problem framing;
14. remaining benchmark weaknesses.

Do NOT select a primary length merely because it is the largest tested size.

Recommend the smallest timeline that meaningfully exercises the state
maintenance problem while keeping repeated evaluation feasible within the
hackathon timebox.

Then enter:

GRILL ME — GATE A FINAL

Ask at most five short critical questions.

STOP.
```
