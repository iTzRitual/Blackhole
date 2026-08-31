/goal BLACKHOLE — FINAL LIVE ASK + MEMORY + UI HOTFIX

THIS IS THE LAST AUTHORIZED PRODUCT HOTFIX BEFORE THE FINAL BENCHMARK / VIDEO.

Work DIRECTLY on master in the current Mac clone.

Do NOT create another branch.
Do NOT create another worktree.

Expected starting master HEAD:

bcf43aed7870c69f0a2501f744641b5fda5778a7

Verify:

branch = master
worktree = clean
origin/master = bcf43aed7870c69f0a2501f744641b5fda5778a7

If not:
STOP.

==================================================
WHY THIS TASK EXISTS
==================================================

Fresh real human dogfood on macOS after the portability hotfix exposed:

1. Ask answers that expose retrieval-oriented/internal wording instead of
   answering naturally like an assistant.

2. Ask thread context contaminating a new explicit question.

3. Real provider occurrence captures still appearing as "Needs clarification"
   / competing Memory history even though deterministic Ask can aggregate them.

4. Several visible final-demo UI defects:
   - Capture composer geometry/alignment;
   - Attention Done placement;
   - Memory History expanded by default;
   - "Needs clarification" is a dead-end state with no useful user action.

Fix ONLY these observed classes.

Do not reopen architecture.

==================================================
LIVE REPRODUCTION — ASK THREAD CONTAMINATION
==================================================

Observed real session:

Question 1:

Where are the basement keys?

Blackhole answered roughly:

Relevant memory: Klucze do piwnicy location: backpack at
2026-08-31T09:42:22...

Then, IN THE SAME ASK THREAD:

Ile kaw wypiłem łącznie?

Blackhole incorrectly answered immediately with the PREVIOUS basement-key
memory:

Pasujące wspomnienia: Klucze do piwnicy location: backpack ...

A NEW THREAD with the exact same coffee question correctly answered after
normal reasoning:

Łącznie 3 kawy — 2 wczoraj i 1 dzisiaj.

This strongly indicates stale thread context/retrieval is overriding the
current explicit question.

==================================================
P0/P1 — CURRENT QUESTION HAS PRIORITY
==================================================

Fix Ask thread semantics generically.

RULE:

The CURRENT user question is authoritative for routing and retrieval.

Thread context is supplementary.

Do NOT concatenate previous conversation terms into retrieval in a way that can
override a fully specified current question.

For a current explicit question such as:

"How many coffees did I drink in total?"

previous discussion about:

basement keys

must have ZERO effect on candidate selection.

==================================================
WHEN THREAD CONTEXT SHOULD HELP
==================================================

Thread context should be used for genuinely referential / elliptical follow-ups
such as:

"What does that mean?"
"Why?"
"And yesterday?"
"Where was it before?"
"And what about the other one?"
"Co to znaczy?"
"A wcześniej?"

Use bounded context to resolve the missing referent.

But for a new self-contained question:

route/retrieve primarily from that current question.

Do NOT solve this by removing thread context entirely.

==================================================
THREAD CONTEXT IS NOT EVIDENCE
==================================================

Preserve the existing boundary:

previous user/assistant messages help interpret references;

they are NOT Product Memory evidence.

Previous assistant output must never become factual evidence.

Final source_refs/supporting memories must correspond to evidence supporting the
CURRENT answer, not evidence used in a previous turn.

==================================================
REGRESSION — SAME THREAD TOPIC SWITCH
==================================================

Add a deterministic regression:

Memory contains:

basement keys -> backpack

plus occurrence captures equivalent to:

yesterday consumed amount 2 of X
today consumed amount 1 of X

Ask in one thread:

1.
Where are the basement keys?

Expected:
backpack-grounded answer.

2.
How many X did I consume in total?

Expected:
3

NOT:
basement keys.

Supporting memories for question 2 must contain occurrence evidence, not the
keys evidence.

3.
What does that mean?

Expected:
resolves the immediately preceding aggregate answer.

Also verify:

New thread
→ same aggregate answer
→ Product Memory unchanged.

Do not hard-code coffee or keys.

==================================================
P1 — ASK MUST ANSWER LIKE AN ASSISTANT
==================================================

Current real output included:

Relevant memory: Klucze do piwnicy location: backpack at
2026-08-31T09:42:22...

and:

Pasujące wspomnienia: ...

This is not acceptable final product UX.

The primary Ask answer should be a HUMAN ANSWER.

Example:

Question:
Where are the basement keys?

Answer:
The basement keys are in your backpack.

Question:
Gdzie są klucze do piwnicy?

Answer:
Klucze do piwnicy są w plecaku.

Question:
Ile kaw wypiłem łącznie?

Answer:
Łącznie 3 kawy — 2 wczoraj i 1 dzisiaj.

Exact wording may differ.

==================================================
NO RETRIEVAL LANGUAGE IN PRIMARY ANSWER
==================================================

Do not intentionally expose in primary answer text:

Relevant memory:
Pasujące wspomnienia:
matching memory:
candidate:
subject:
predicate:
object:
entity key:
raw timestamp
raw structured tuple
raw semantic field names.

These may be internal retrieval concepts.

The user asked a question.

Answer the question.

==================================================
PROVENANCE REMAINS SEPARATE
==================================================

Do NOT remove source grounding.

Keep:

Supporting memories

as a secondary/collapsible provenance surface underneath the natural answer.

Primary answer:
human-readable response.

Secondary:
supporting evidence/source.

Do not merge provenance diagnostics into the prose answer.

==================================================
DETERMINISTIC FAST PATHS MUST REMAIN FAST
==================================================

Do NOT call the provider merely to turn:

location = backpack

into:

"The keys are in your backpack."

If a deterministic answer mode already has sufficient structured information,
render a natural answer deterministically.

Existing occurrence aggregate path already demonstrated a natural deterministic
answer:

Łącznie 3 kawy — 2 wczoraj i 1 dzisiaj.

Reuse/generalize the product answer-formatting boundary rather than adding a
second semantic provider call.

If a genuinely semantic answer requires provider synthesis, bounded provider
Ask remains allowed.

Do not change Product V2 model/reasoning/batch.

==================================================
LANGUAGE
==================================================

Primary Ask answer should normally follow the current question language.

Do not let an earlier thread message override the current language.

Do not introduce noun-specific or coffee-specific translation rules.

Do not create per-language keyword tables as a capability boundary.

Use the existing language-invariant product architecture.

==================================================
P1 — REAL OCCURRENCES STILL LOOK LIKE CONFLICTS
==================================================

Observed real provider state:

Capture:

Wczoraj wypiłem 2 kawy.

Capture:

Dzisiaj wypiłem 1 kawę.

Ask correctly produced:

Łącznie 3 kawy — 2 wczoraj i 1 dzisiaj.

But Memory rendered approximately:

Memory
3

Needs clarification

Needs clarification
Captured just now · needs clarification

History

Previously: Coffee Consumed: 2
Previously: Coffee Consumed: 1

This is semantically wrong UX.

Those are TWO OCCURRENCES.

They are not two competing values of one current-state property.

==================================================
STATE VS OCCURRENCE — REAL PROVIDER SHAPE
==================================================

Investigate the ACTUAL structured provider output shape produced by these
captures.

The existing deterministic fixtures apparently did not fully exercise the real
shape.

Fix the generic projection boundary.

STATE examples:

keys location
current subscription price
current appointment time
current status

These may have:

current
previous
superseded
conflicting

semantics.

OCCURRENCE examples:

drank
ate
bought
paid
visited
ran
watched
received

Distinct temporal occurrences COEXIST.

They are not:

Previously: occurrence A
Previously: occurrence B

unless the user explicitly corrected the same occurrence.

Do NOT add coffee-specific logic.

==================================================
MEMORY PRESENTATION FOR OCCURRENCES
==================================================

Do not force occurrence collections into a state/history card model.

A reasonable generic presentation could be:

Coffee consumed

3 total across 2 captured occurrences

Occurrences · 2
  Today — 1
  Yesterday — 2

Exact visual copy is flexible.

The important semantics are:

- multiple occurrences coexist;
- numeric aggregate may be shown when deterministic;
- occurrences are not presented as conflicting history;
- no false "Needs clarification".

Keep the design quiet.

Do not build an activity-tracking product.

==================================================
GENUINE CLARIFICATION
==================================================

"Needs clarification" should appear only when Blackhole genuinely needs more
information from the user.

It must NOT be generated merely because multiple valid occurrences exist.

If a genuine clarification remains:

do not make it a dead-end label.

Provide a small actionable UX:

Clarify in Ask

or equivalent.

Clicking it should:

- navigate to Ask;
- provide/prefill useful clarification context;
- NOT auto-submit;
- NOT create Product Memory automatically.

If current Attention architecture already supports unresolved clarification,
it may also surface there because Attention represents things that still need
the user.

Do NOT build a new clarification database/workflow subsystem.

==================================================
MEMORY HISTORY DEFAULT CLOSED
==================================================

History is secondary information.

Memory history should be collapsed by default.

Prefer native/simple disclosure behavior.

Example:

History · 2   >

closed initially.

When opened:

previous values.

Preserve accessible keyboard behavior.

For occurrence collections, use a suitable label such as:

Occurrences · 2

rather than falsely calling independent occurrences "History".

==================================================
P2 BUT DEMO-VISIBLE — CAPTURE COMPOSER
==================================================

The Capture composer has visible geometry problems.

Observed:

- real input text is vertically too high;
- placeholder is vertically too high;
- trailing submit button geometry does not visually match the pill/container;
- outer container is strongly rounded while the button uses mismatched rounded
  corners.

Use the EXISTING ASK COMPOSER as the primary visual/geometry reference.

Do not invent another design language.

Make Capture and Ask feel like members of the same component family.

Fix:

- vertical centering;
- textarea/input line-height;
- padding;
- min-height;
- button height;
- trailing-edge radius;
- border alignment;
- focus state;
- disabled state;
- mobile touch target.

The submit button and outer shell should visually form one intentional control.

Do not reduce usable typing width unnecessarily.

==================================================
ATTENTION — DONE ACTION
==================================================

Current Done action is awkwardly positioned.

Rework only the action placement/style.

The hierarchy should be:

Attention item content
due/urgency
optional explanation
completion action

Done should be easy to find but not visually dominate the deadline.

Use a restrained compact action such as:

✓ Done

in a dedicated card action area / footer or another visually intentional
location.

Do not leave it floating or misaligned with content.

Preserve >=44px practical mobile touch target where possible.

Click behavior remains:

Done
→ immediately leaves active Attention
→ badge updates.

Do not change lifecycle semantics.

==================================================
DESIGN REVIEW
==================================================

Use existing Product V2 visual principles and the Ask composer as reference.

Do not redesign the application.

Check at minimum:

390x844
1280x900

Review:

visual hierarchy
alignment
radii
spacing
touch targets
focus-visible
reduced motion
Safari/macOS rendering
Chrome rendering where available.

==================================================
TESTS — ASK
==================================================

Add/extend deterministic tests for:

- topic switch within same thread;
- explicit current question wins over stale thread context;
- follow-up still resolves previous turn;
- New thread clears temporary context;
- previous assistant text is never evidence;
- supporting memories correspond only to current answer;
- location answer is natural, not "Relevant memory:";
- no raw ISO timestamp in normal primary location answer;
- aggregate answer remains natural;
- current question language controls answer language where existing deterministic
  support applies;
- no raw dict/object/internal field output.

==================================================
TESTS — MEMORY / OCCURRENCES
==================================================

Use generic entities.

Test:

occurrence yesterday amount=2
occurrence today amount=1

Expected:

- two coexist;
- no conflict;
- no Needs clarification;
- deterministic aggregate=3;
- occurrence presentation is not "Previously A / Previously B".

Also retain tests proving:

state A
then state B

can still represent current/history or conflict correctly where semantically
appropriate.

==================================================
TESTS — CLARIFY UX
==================================================

Verify:

false clarification from multiple occurrences:
NOT shown.

genuine unresolved ambiguity:
may show clarification.

If shown:
Clarify in Ask action exists and transfers useful bounded context without
persisting a new fact or auto-submitting.

==================================================
TESTS — UI
==================================================

Update static/UI tests as appropriate for:

Capture composer alignment/component contract;
History default closed;
occurrence disclosure default closed;
Done action placement;
Clarify in Ask;
Ask natural primary answer;
secondary Supporting memories remain available.

Do not assert fragile pixel-perfect geometry.

==================================================
LIVE VALIDATION — BOUNDED
==================================================

This failure was discovered with the REAL provider, so a bounded live validation
is authorized.

MAXIMUM:

4 live captures
5 Ask requests

Use a fresh temporary BLACKHOLE_HOME.

Do not use private data.

Do not exceed the cap.

At minimum validate a natural sequence structurally equivalent to:

state/location capture

occurrence amount=2 yesterday

occurrence amount=1 today

actionable near-future item

Then Ask IN ONE THREAD:

location question
aggregate occurrence question
referential follow-up

Expected:

- location answer natural;
- aggregate answer correct;
- aggregate answer does not reuse location memory;
- follow-up understands previous aggregate;
- source refs change appropriately with topic.

Then inspect Memory:

- repeated occurrences are not false clarification/history conflict.

Inspect Attention:

- exactly one active actionable item;
- Done placement and behavior sane.

==================================================
NO PERFORMANCE RESEARCH
==================================================

Do not reopen:

model comparison
reasoning effort
batch size
prompt benchmarking
latency optimization

Existing Product V2 config stays frozen.

Do not benchmark yet.

==================================================
FULL REGRESSION
==================================================

After focused tests:

python3 -m unittest discover -s app/tests -p "test_*.py"
python3 -m unittest discover -s eval/tests
python3 -m unittest product_acceptance.harness.test_harness
python3 -m unittest discover -s . -p "test_*.py"
python3 scripts/run_product_v2_integrated_acceptance.py
python3 -m compileall -q app eval product_acceptance scripts
node --check app/web/app.js
python3 benchmark/dev/generate_benchmark.py --check
python3 eval/contract_smoke.py
python3 scripts/qualification_check.py --inventory
git diff --check

Do not weaken existing tests.

==================================================
TRAJECTORY
==================================================

Create:

trajectories/coding/046-final-live-ask-memory-ui-hotfix/
  prompt.md
  summary.md

Update trajectory index honestly.

Record:

- live same-thread topic contamination;
- retrieval-style primary Ask answer;
- real-provider occurrence/clarification mismatch;
- Capture composer issue;
- Attention Done issue;
- History disclosure;
- clarification UX;
- bounded live result.

==================================================
GIT / TAGS
==================================================

Commit directly to master.

Push:

git push origin master

Verify:

origin/master == local master HEAD

PRESERVE BOTH EXISTING TAGS:

product-v2-submission
product-v2-submission-final

Do NOT move, delete, or overwrite them.

They remain historical frozen snapshots.

After ALL gates pass, create a NEW annotated tag:

product-v2-submission-release

pointing to the final fixed master HEAD.

Push:

git push origin product-v2-submission-release

Verify the tag dereferences exactly to final master.

Update current judge-facing documentation only where necessary so the
authoritative final submission snapshot is:

product-v2-submission-release

Do not rewrite historical trajectory evidence referencing earlier tags.

==================================================
FINAL GATE
==================================================

Return:

# BLACKHOLE FINAL LIVE UX HOTFIX GATE

PASS / PARTIAL / FAIL

ASK
- current-question precedence
- same-thread topic switch
- referential follow-up
- natural answer formatting
- source/provenance behavior
- language behavior

MEMORY
- real occurrence behavior
- aggregate
- false clarification removed
- genuine clarification UX
- History/Occurrences disclosure

UI
- Capture composer
- Attention Done
- Memory disclosure
- Clarify in Ask
- mobile/desktop review

LIVE
- captures used
- asks used
- exact observed result
- provider failures/retries
- no private data

REGRESSION
- focused tests
- app test count
- evaluator
- harness
- root count
- integrated acceptance
- static gates

GIT
- starting SHA
- implementation SHA
- final master SHA
- origin/master SHA
- product-v2-submission-release target

Explicitly confirm:

- no coffee-specific rule;
- no keys-specific rule;
- no provider config changed;
- no benchmark/evaluator semantics changed;
- no V1 oracle accessed;
- current explicit Ask question outranks stale thread context;
- thread context still works for genuine follow-ups;
- previous assistant output is not evidence;
- primary Ask answer no longer intentionally exposes retrieval diagnostics;
- occurrence events are not represented as competing current-state history;
- genuine clarification is actionable;
- old tags were not moved.

PASS only if the same-thread topic-switch reproduction is fixed AND real
occurrence Memory no longer falsely shows Needs clarification.

Then STOP.

Do not start benchmark or another implementation task.
