/goal BLACKHOLE PRODUCT V2 — SEMANTIC TRUTH, CORRECTIONS, UNCERTAINTY + TEMPORAL MEANING

This is a focused Product V2 semantic-state correctness task.

SOURCE BRANCH:

product/v2-provenance-fix

SOURCE WORKTREE:

C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-provenance-fix

Required exact source HEAD:

7a76a1b660b49d28cb5aa29ab9e9b5099238aaee

Do NOT modify the source worktree.

==================================================
CREATE ISOLATED WORKTREE
==================================================

Create:

C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-semantic-truth

Branch:

product/v2-semantic-truth

Base EXACTLY on:

7a76a1b660b49d28cb5aa29ab9e9b5099238aaee

Do NOT modify any previous Product V2 worktree.

Do NOT modify master.

Do NOT access V1 oracle/scoring worktrees.

==================================================
KNOWN GOOD STATE
==================================================

The current Product V2 line already has:

- normal-launch background processing;
- one authoritative Product V2 store;
- bounded retries;
- working authenticated Codex provider;
- strict provider output schema;
- open-world semantic memory;
- Product V2 Ask planner;
- cross-language retrieval;
- language-neutral semantic fallback;
- precise answer provenance;
- 54/54 language-invariance matrix;
- 50/50 integrated product acceptance;
- 137/137 application tests at the provenance gate.

The provenance live validation showed:

4/4 captures processed first attempt
4/4 Ask answers cited only materially relevant sources
3/4 answers semantically correct

The remaining semantic failure:

Capture:

"Meeting z Markiem moved to Donnerstag 16:00."

Ask:

"Kiedy mam spotkanie z Markiem?"

The answer conservatively reported the meeting time as unclear.

Do NOT fix this with a special rule for:

Donnerstag
Markiem
meeting
16:00

or the exact live phrase.

This task addresses the GENERAL semantic truth model.

==================================================
PRODUCT PRINCIPLE
==================================================

Blackhole is not merely a bag of extracted statements.

It must maintain a useful view of:

- what appears currently true;
- what used to be true;
- what the user corrected;
- what changed;
- what is uncertain;
- what is contradictory;
- what somebody else merely claimed;
- what was retracted;
- what has a temporal interpretation.

Raw evidence remains immutable except for explicit permanent deletion, which is
OUT OF SCOPE for this task.

Derived semantic state is rebuildable.

==================================================
CORE REQUIREMENT — CURRENT TRUTH IS NOT LAST STRING WINS
==================================================

Consider:

Capture 1:
"Klucze do piwnicy są u mamy."

Capture 2:
"Jednak mam je w szufladzie."

Expected product state:

Basement keys
Current:
in the drawer

History/evidence:
previously at Mum's place

Ask:
"Gdzie są klucze?"

should prefer the corrected/current location.

But Ask such as:

"Gdzie wcześniej były klucze?"

should retain the previous information.

Do not delete historical evidence merely because a new fact supersedes it.

==================================================
SEMANTIC CASE 1 — EXPLICIT CORRECTION
==================================================

Recognize ordinary corrections such as:

"Actually, the keys are in my desk."

"Jednak spotkanie jest w piątek."

"Nie 11 euro, tylko 12."

"Correction: Marta has the garage keys, not Adam."

The new statement should supersede the appropriate previous current belief.

Preserve both sources.

Do not require explicit words like:

actually
correction
jednak

for every update.

==================================================
SEMANTIC CASE 2 — ORDINARY CHANGE OVER TIME
==================================================

A change is not necessarily an error correction.

Example:

"PocketWave kosztuje 9 EUR miesięcznie."

later:

"Od 1 września PocketWave będzie kosztować 11 EUR."

Expected:

current/planned price semantics respect effective time.

History remains:

€9 → €11

Ask:

"Ile kosztuje PocketWave?"

should use the temporally appropriate current value.

Ask:

"Ile wcześniej kosztował?"

should be able to retrieve €9.

Do not treat every newer value as evidence that the earlier source was wrong.

==================================================
SEMANTIC CASE 3 — UNCERTAINTY
==================================================

Examples:

"Chyba gwarancja kończy się w grudniu."

"I think the boiler warranty expires in December."

"Mechanik powiedział, że to prawdopodobnie lewe łożysko."

"Maybe Marta still has the spare key."

These must NOT silently become certain facts.

Preserve epistemic uncertainty.

Ask:

"Kiedy kończy się gwarancja?"

should answer roughly:

"It may expire in December; that wasn't confirmed."

not:

"It expires in December."

Do not require one exact wording.

==================================================
SEMANTIC CASE 4 — REPORTED CLAIMS
==================================================

Distinguish:

"My car has a broken left bearing."

from:

"The mechanic thinks the left bearing may be causing the noise."

The latter is:

- attributed to the mechanic;
- uncertain;
- evidence about a possible diagnosis.

Do not promote another person's speculation to confirmed reality.

==================================================
SEMANTIC CASE 5 — CONTRADICTION
==================================================

Example:

Capture A:
"Mechanik mówi, że hałas powoduje lewe łożysko."

Capture B:
"Drugi mechanik mówi, że łożysko jest okej i problem jest w oponie."

Blackhole should not arbitrarily choose one as certain.

Expected state:

conflicting explanations / unresolved diagnosis.

Ask:

"Co jest nie tak z samochodem?"

should communicate the conflict truthfully and cite both materially relevant
sources.

==================================================
SEMANTIC CASE 6 — LATER OBSERVATION CAN RESOLVE UNCERTAINTY
==================================================

Example:

"I think the keys might be at Mum's."

later:

"Found them — they're in the desk drawer."

Expected:

current location:
desk drawer

The speculative previous location remains historical evidence, not active
uncertainty.

==================================================
SEMANTIC CASE 7 — NEGATION
==================================================

Handle meaningful negation.

Examples:

"Adam doesn't eat peanuts."

"The permit is not due this week."

"Netflix nie jest jeszcze anulowany."

"To nie lewe łożysko."

Negation must not be dropped during extraction.

A negative fact is not equivalent to absence of a positive fact.

==================================================
SEMANTIC CASE 8 — CANCEL / COMPLETE / RESCHEDULE
==================================================

Attention must respect semantic changes.

Examples:

"Spotkanie z dentystą jest we wtorek o 14."

later:

"Dentysta przełożył wizytę na czwartek 16:30."

Expected:

old Tuesday occurrence no longer active
new Thursday 16:30 occurrence active

Similarly:

"Muszę odnowić parking do piątku."

then:

"Parking odnowiony."

Expected:

no active overdue/upcoming reminder for that completed task.

And:

"Nie muszę już odbierać dzieci, zrobi to Marta."

should cancel/supersede the previous actionable item where context supports it.

Do not leave ghost Attention items after corrections.

==================================================
TEMPORAL MEANING — GENERAL REQUIREMENT
==================================================

The live mixed-language meeting failure shows that temporal meaning needs a
general audit.

Separate responsibilities:

AI:
understand semantic temporal expression/context.

Deterministic code:
normalize final timestamps, dates, timezone-aware values and relative time when
sufficient information exists.

Do not make language-specific date dictionaries the product capability
boundary.

Examples that should be handled through general semantic understanding:

"Thursday at 16:30"

"w czwartek o 16:30"

"Donnerstag 16:30"

"el jueves a las 16:30"

"jeudi à 16h30"

and mixed:

"Meeting z Markiem moved to Donnerstag 16:00."

All should be capable of producing equivalent temporal meaning given the same
reference date/timezone.

==================================================
REFERENCE TIME
==================================================

Every capture has a capture timestamp and timezone/reference context.

Relative expressions must use it.

Examples:

"za 10 minut"

"in 10 minutes"

"tomorrow morning"

"jutro rano"

"next Thursday"

Deterministic normalization must not silently use wall-clock time from a later
processing attempt.

Retrying processing later must not shift the intended deadline.

==================================================
AMBIGUOUS TIME
==================================================

Do not invent precision.

Examples:

"next week"

"sometime in December"

"around 4"

"chyba w piątek"

If exact normalization is impossible, preserve an appropriately coarse or
uncertain temporal representation.

Do not fabricate:

2026-12-01T00:00

from:

"sometime in December"

unless the representation explicitly means a coarse interval rather than a
claimed exact date.

==================================================
TEMPORAL CHANGE VS MENTION
==================================================

Do not confuse temporal content with actionable scheduling.

Examples:

"My brother flew there last Thursday."
→ historical event, not Attention.

"The contract says 30 days notice."
→ document fact, not necessarily Attention.

"We're thinking about Japan next year."
→ plan/possibility, not an urgent deadline.

"Pick up the kids in 10 minutes."
→ actionable.

==================================================
SEMANTIC STATE MODEL
==================================================

Audit the current open-world fact/event representation.

Extend it only as necessary to represent concepts such as:

- current/superseded;
- correction;
- effective time;
- uncertainty/confidence;
- attribution;
- contradiction;
- negation;
- temporal interval/precision;
- task/event status.

Do NOT create a huge closed ontology.

Prefer general semantic primitives.

Do not expose these internal fields directly as the primary UI.

==================================================
SUPERSESSION MUST BE TARGETED
==================================================

Do not implement:

new fact about entity
→ supersede all old facts about entity.

Example:

"Car is blue."

later:

"Car is making a noise."

Both remain true.

Only semantically competing/change-related assertions should supersede each
other.

Similarly:

"Kuba likes green pasta."

later:

"Kuba wears size 43."

must coexist.

==================================================
DUPLICATE EVIDENCE
==================================================

If the same fact is captured twice:

"Klucze są u mamy."

later:

"Klucze do piwnicy są u mamy."

do not create misleading contradiction/history.

Multiple evidence sources may support the same active fact.

Preserve provenance.

==================================================
RETRACTION REGRESSION
==================================================

Existing Undo/retraction behavior must remain correct.

If the user captures:

"Klucze są w samochodzie."

then immediately Undo:

that source must not become active truth later after background processing.

Retraction must work for:

pending
processed
superseding/correcting facts

Do not resurrect retracted semantic state.

==================================================
ASK CONTRACT
==================================================

Ask should render semantic truth appropriately.

Examples:

KNOWN CURRENT:
"Where are the keys?"
→ "In the desk drawer."

UNCERTAIN:
"When does the warranty expire?"
→ "It may expire in December; that wasn't confirmed."

CONFLICT:
"What's causing the car noise?"
→ "There are conflicting notes: one mechanic suspected the left bearing, while
another said the bearing was fine and suspected the tyre."

HISTORY:
"What changed about PocketWave?"
→ "It changed from €9/month to €11/month."

NO EVIDENCE:
→ say there isn't supporting information.

Do not flatten these states into the same answer type.

==================================================
PROVENANCE MUST REMAIN PRECISE
==================================================

The source provenance-fix established:

candidate evidence != supporting evidence.

Preserve that.

A current answer should cite the current supporting source.

A history answer may cite old + new source.

A conflict answer may cite both conflicting sources.

An uncertainty answer should cite the uncertain source.

Do not regress into exposing all retrieval candidates.

==================================================
LANGUAGE INVARIANCE MUST REMAIN
==================================================

Corrections can cross languages.

Examples:

Capture PL:
"Klucze są u mamy."

Correction EN:
"Actually, I found the keys in my desk."

Ask DE:
"Wo sind die Schlüssel?"

Expected:
current desk location.

Likewise uncertainty and contradiction must survive language changes.

Do NOT build per-language correction keyword tables as the capability mechanism.

==================================================
PHASE — STRUCTURED PROVIDER EXTRACTION AUDIT
==================================================

Inspect the Product V2 provider extraction schema and prompt.

Determine whether it can faithfully express:

- correction/supersession hints;
- uncertainty;
- attribution;
- negation;
- temporal meaning;
- event/task lifecycle;
- relation between new observation and previous state.

If schema expansion is needed:

keep it strict and typed.

Do NOT regress the prior Codex invalid_json_schema fix.

Any new array must have typed items.

Avoid additionalProperties where strict schema rejects them.

==================================================
SPECIFIC MIXED-LANGUAGE TEMPORAL REGRESSION
==================================================

The previously observed live case must become a regression:

Capture:
"Meeting z Markiem moved to Donnerstag 16:00."

Given a fixed capture timestamp/timezone where the next Thursday is known.

Expected derived semantics:

- meeting with Marek;
- rescheduled/moved;
- Thursday;
- 16:00;
- normalized deterministic timestamp where unambiguous.

Ask:
"Kiedy mam spotkanie z Markiem?"

must surface Thursday 16:00.

This must pass because general mixed-language temporal semantics works.

NO exact-phrase special case.

==================================================
TEST SUITE — AT LEAST 50 SEMANTIC SEQUENCE CASES
==================================================

Create a dedicated semantic truth suite with at least 50 cases.

Include multi-capture sequences.

Cover:

- simple current fact;
- explicit correction;
- implicit update;
- time-effective change;
- historical value;
- duplicate evidence;
- uncertainty;
- resolution of uncertainty;
- attribution;
- contradictory claims;
- negation;
- cancellation;
- completion;
- rescheduling;
- deadline movement;
- retraction before processing;
- retraction after processing;
- cross-language correction;
- mixed-language correction;
- relative time;
- explicit date/time;
- coarse time;
- non-actionable time mention;
- entity facts that should coexist.

Do not assert one exact internal ontology.

Assert user-visible semantics and structured invariants.

==================================================
NO LAST-WRITE-WINS SHORTCUT
==================================================

Tests must include adversarial ordering that proves the implementation is not
merely:

latest capture wins.

Example:

1. confirmed value
2. later uncertain speculation

The later speculation must not necessarily overwrite the confirmed fact as
certain.

Example:

"Keys are in the drawer."

later:

"I wonder if I left the keys in the car."

Expected:

do NOT silently make "car" the certain current location.

==================================================
REBUILD DETERMINISM
==================================================

Derived Product V2 state is rebuildable.

For a fixed ordered evidence stream and fixed extractor outputs:

incremental processing

and

clean rebuild

must produce semantically equivalent active state.

Add regression coverage if current architecture supports rebuilding.

==================================================
ATTENTION REGRESSION MATRIX
==================================================

Specifically verify:

create deadline
→ active

reschedule
→ old inactive, new active

complete
→ inactive

cancel
→ inactive

correct mistaken date
→ only corrected active deadline

uncertain future mention
→ no false urgent item where actionability is insufficient

==================================================
LIVE VALIDATION AUTHORIZATION
==================================================

A NEW bounded live smoke is explicitly authorized for this semantic-truth task.

Use a FRESH temporary BLACKHOLE_HOME.

Normal app lifecycle only.

Do NOT manually run product_process.

Maximum live captures:

10

Use this sequence:

1.
"Klucze do piwnicy są u mamy."

2.
"Jednak znalazłem klucze w szufladzie biurka."

3.
"PocketWave kosztuje 9 EUR miesięcznie."

4.
"Od 1 września PocketWave będzie kosztować 11 EUR miesięcznie."

5.
"Chyba gwarancja na bojler kończy się w grudniu."

6.
"Mechanik mówi, że stukanie może powodować lewe łożysko."

7.
"Drugi mechanik mówi, że lewe łożysko jest okej i podejrzewa oponę."

8.
"Spotkanie z Markiem jest we wtorek o 14:00."

9.
"Meeting z Markiem moved to Donnerstag 16:00."

10.
"Muszę odnowić pozwolenie parkingowe do piątku."

Wait for normal background processing.

Maximum live Ask queries:

8

1.
"Gdzie są teraz klucze do piwnicy?"

2.
"Gdzie wcześniej były klucze?"

3.
"Ile kosztuje PocketWave i czy cena się zmieniała?"

4.
"Kiedy kończy się gwarancja na bojler?"

5.
"Co może powodować stukanie w samochodzie?"

6.
"Kiedy mam spotkanie z Markiem?"

7.
"What changed about my meeting with Marek?"

8.
"Was weißt du über die Kellerschlüssel?"

PASS requires semantic correctness across:

- current vs history;
- uncertainty;
- conflict;
- reschedule;
- cross-language retrieval;
- precise provenance.

Do NOT edit implementation between individual live requests.

Do NOT create phrase-specific rules from smoke output.

If a structural semantic failure appears:

record it and return PARTIAL.

==================================================
SECOND LIVE ATTENTION VALIDATION
==================================================

Within the same maximum capture budget, inspect Attention after the meeting
reschedule and parking deadline.

Verify:

- only correct current meeting occurrence is active if meeting belongs in
  Attention;
- no stale Tuesday event after Thursday reschedule;
- parking deadline appears appropriately;
- uncertainty/diagnostic claims do not become false urgent tasks.

No additional live captures required.

==================================================
FULL REGRESSION
==================================================

Run:

- new semantic-truth tests;
- provenance tests;
- language-invariance tests;
- Ask routing tests;
- provider adapter tests;
- lifecycle tests;
- Product V2 runtime tests;
- HTTP tests;
- UI tests;
- 50-case integrated acceptance;
- harness tests;
- historical V1 tests;
- evaluator tests;
- compileall;
- JavaScript syntax;
- qualification;
- benchmark structural check.

Do not weaken previous tests.

==================================================
DOCUMENTATION
==================================================

Create:

trajectories/coding/040-product-v2-semantic-truth/
  prompt.md
  summary.md
  live-validation.json

Update Product V2 architecture/spec documentation.

Document explicit principles:

- raw evidence is preserved;
- derived truth may change;
- correction != deletion;
- change != correction;
- uncertainty is first-class;
- conflicting evidence stays conflicting until resolved;
- reported claims retain attribution;
- newer does not automatically mean more certain;
- deterministic time normalization uses capture reference time;
- language does not define semantic capability.

Do not rewrite previous historical failures.

==================================================
GIT
==================================================

Commit only to:

product/v2-semantic-truth

Do NOT merge master.

Do NOT modify source worktrees.

==================================================
FINAL GATE
==================================================

Return:

# PRODUCT V2 SEMANTIC TRUTH GATE

PASS / PARTIAL / FAIL

Include:

- exact base SHA;
- final SHA;
- semantic state changes;
- correction behavior;
- ordinary change behavior;
- uncertainty behavior;
- attribution behavior;
- contradiction behavior;
- negation behavior;
- duplicate behavior;
- temporal normalization behavior;
- mixed-language temporal result;
- Attention reschedule/cancel/complete behavior;
- rebuild/incremental equivalence result;
- provenance regression result;
- language-invariance result;
- semantic truth test count;
- live capture outcomes;
- eight live Ask outcomes;
- live Attention result;
- 50-case acceptance result;
- full test counts;
- provider retries;
- known limitations.

Explicitly confirm:

- no exact-phrase rule for the mixed-language meeting example;
- no last-write-wins shortcut;
- no per-language semantic capability tables;
- uncertainty was not collapsed to certainty;
- provenance precision remains intact;
- source worktree unchanged;
- master unchanged;
- V1 oracle not accessed;
- G01/G02/G03 not used.

Decision:

KEEP only if Blackhole can distinguish what appears currently true from what
used to be true, might be true, conflicts with other evidence, or was explicitly
corrected.
