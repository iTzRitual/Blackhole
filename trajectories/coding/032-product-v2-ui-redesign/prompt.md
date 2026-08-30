# Human instruction

The following is the pasted task instruction supplied by the project owner. It is preserved verbatim from:
C:\Users\natan\.codex\attachments\bd808438-a7a8-4133-a731-ab0719c53d0b\pasted-text-1.txt

---

/goal BLACKHOLE PRODUCT V2 — MOBILE UI / UX REDESIGN

This is a PARALLEL PRODUCT V2 task.

Another Codex agent is independently working on:

branch:
product/v2-runtime

worktree:
C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-runtime

YOU MUST NOT:

- use that worktree;
- edit files inside that worktree;
- switch that branch;
- merge that branch;
- cherry-pick from that branch;
- wait for or interfere with that agent.

Your task has its own isolated worktree and branch.

==================================================
BASE / WORKTREE ISOLATION
==================================================

Repository:
https://github.com/iTzRitual/Blackhole

Required base master:

68b7b15d353b12cffb65a770f8583aa0ebb849dd

Create/use ONLY:

C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-ui

Branch:

product/v2-ui

Base it EXACTLY on:

68b7b15d353b12cffb65a770f8583aa0ebb849dd

Do NOT work in:

C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole

Do NOT work in:

C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-runtime

Do NOT work in any generalization/oracle/scoring worktree.

If the designated UI worktree already exists unexpectedly and its state is not
clearly this task's clean branch, STOP instead of reusing an unknown workspace.

==================================================
SCOPE BOUNDARY
==================================================

This task owns the PRODUCT V2 FRONTEND experience.

Primary allowed product scope:

app/web/**

plus frontend-focused tests and documentation required for this task.

Do NOT redesign backend/runtime implementation here.

Do NOT modify semantic extraction, StateStore, provider execution, benchmark
runtime, evaluator, or historical V1 behavior.

Another agent owns runtime V2.

If a desired frontend behavior requires a backend capability that does not yet
exist on this base:

- define a clean frontend adapter / expected API contract;
- use deterministic mocks/fixtures for frontend testing where needed;
- document the integration requirement;
- DO NOT implement the backend in this branch.

The future integration task will reconcile UI and runtime contracts.

==================================================
PRODUCT CONTEXT
==================================================

Blackhole is a zero-organization personal external memory.

The product promise:

Capture now.
Understand automatically.
Find it later.

The current UI was dogfooded and found substantially insufficient.

The UI must stop looking like a benchmark debugger and start behaving like a
premium personal memory application.

Design priorities:

- mobile first;
- near-zero capture friction;
- premium restrained near-black appearance;
- subtle violet/blue accents;
- calm and sparse;
- no dashboard clutter;
- no gamified streaks;
- no fake productivity pressure;
- no medical claims;
- silent by default;
- interrupt only when useful.

==================================================
P0 — CAPTURE COMPOSER REDESIGN
==================================================

The Capture screen should remain intentionally minimal.

Default screen:

- small Blackhole mark;
- heading similar to:
  "What's on your mind?"
- composer;
- large visual breathing space;
- bottom navigation.

REMOVE unnecessary dashboard-like copy, counts, runtime status, recent capture
lists, explanatory panels, or system-debug information from the default Capture
experience.

The composer must be redesigned.

REQUIRED:

- significantly lower / more compact than current implementation;
- fully pill-shaped / rounded rather than rectangular;
- near-black surface;
- simple PLUS character/icon on the left;
- do NOT use a plus inside a circle;
- no decorative circled-cross appearance;
- textarea/input grows only when content needs additional lines;
- clear send affordance on the right;
- send affordance may retain restrained violet/blue treatment.

Keyboard behavior:

ENTER
= send capture

SHIFT+ENTER
= newline

On mobile, normal keyboard submission should behave naturally.

Prevent accidental double-submit.

Sending must work for:

- text-only capture;
- attachment-only capture;
- text + attachment.

The UI must NOT require typed text when an attachment is selected.

==================================================
P0 — ATTACHMENT EXPERIENCE
==================================================

The plus button opens a simple attachment menu:

- Camera
- Photo library
- File

Selecting an attachment:

- must NOT automatically submit;
- keeps the composer active;
- shows a compact preview;
- supports removing/replacing the attachment;
- allows optional text context;
- allows submission with NO text.

Image preview should be visual.

Document/file preview should show a concise filename/type/size representation.

Do NOT fake OCR or extracted text in the UI.

Do NOT silently copy text-file contents into the composer as if the user typed
them unless there is an explicit product reason and clear UX.

Attachment is evidence, not merely an accessory to required text.

==================================================
P0 — SUCCESS + UNDO
==================================================

After a capture is successfully durably saved:

- clear composer;
- clear sent attachment;
- preserve immediate feeling of completion;
- show Blackhole collapse/fall micro-animation;
- total animation roughly 350–650 ms;
- respect prefers-reduced-motion.

Success feedback should be ephemeral.

Preferred language:

+1 off your mind

Alongside it provide:

Undo

or another very clear short equivalent.

Do NOT use a persistent "things off your mind" score.

Do NOT create streaks.

Do NOT create level/progress mechanics.

Milestones may remain extremely restrained and ephemeral if already supported,
but are secondary to the core UX.

Undo UI should call the V2 retraction capability when available.

On this isolated UI branch, if backend retraction is not yet present, implement
the frontend contract/mocked behavior and document the required integration.

Do NOT physically delete evidence from frontend assumptions.

==================================================
P0 — PROCESSING STATE
==================================================

Product V2 runtime is expected to process captures asynchronously.

The UI should represent this without making the user babysit the system.

Capture success means:

"saved"

not:

"AI fully finished processing"

Avoid blocking overlays.

If useful, a subtle temporary state may communicate:

saved / understanding

but normal users should not need to understand queue internals.

Provider failures should be represented truthfully and recoverably without
dumping technical stack/runtime details into the primary UX.

==================================================
P0 — ATTENTION REDESIGN
==================================================

The existing Attention experience does not provide enough useful feedback.

Redesign it for a real user.

Attention should answer:

"What actually needs me?"

Examples:

Taxi in 10 minutes

Pick up the kids in 10 minutes

Parking permit due September 12

Upcoming appointment

Overdue task

Items should be human-readable cards, NOT raw semantic assertions.

Prefer presentation such as:

Pick up the kids
in 8 min

or:

Renew parking permit
Sep 12

Use urgency hierarchy carefully.

Do NOT use anxiety-inducing visual design.

Do NOT display raw fields like:

subject
predicate
knowledge_status
source_refs

as primary content.

Evidence/details may be available behind an expandable detail affordance.

Empty state should be genuinely useful and calm.

Attention badge in bottom nav:

- hidden when count = 0;
- visible only when actionable attention exists.

==================================================
P0 — MEMORY COMPLETE PRODUCT REDESIGN
==================================================

The current Memory tab is not understandable to a normal user.

Redesign it from first principles.

Memory should answer:

"What does Blackhole know for me?"

Do NOT organize the primary interface around internal benchmark categories or
raw assertion records.

Do NOT make users understand:

- predicates;
- ontology;
- known/inferred tags;
- source event IDs;
- duplicate components;
- projection versions.

Those may exist as debug/evidence detail, never as the main information
architecture.

Design a flexible human-oriented memory browser.

Possible presentation primitives include:

- people;
- places;
- things;
- money / recurring costs;
- tasks;
- documents;
- recent changes;
- topics/entities dynamically discovered by the system.

Do NOT hard-code the interface so that only these categories can ever exist.

It must tolerate an OPEN-WORLD runtime.

Examples that should be understandable:

Kuba
Likes the green pasta from Lidl

Car
Started knocking at the front-left

Basement keys
At Mum's place

PocketWave
€11 / month
Changed from €9 starting Sep 1

Parking permit
Renew by Sep 12

The UI may group related facts beneath entity/topic cards.

Prefer concise natural summaries.

Provide search/filter affordance if it materially improves usability.

Evidence/provenance should be available through:

Details
Why does Blackhole know this?
Source

or equivalent.

Unknown/ambiguous information should be represented in human language rather
than raw "knowledge_status=unknown".

==================================================
P0 — ASK COMPLETE REDESIGN
==================================================

The current Ask interface behaves like a small set of benchmark query buttons.

Product V2 should feel like asking your own memory.

Primary interaction:

natural question input

Examples:

"What do I need to do today?"

"What am I paying for?"

"What do I know about my car?"

"When did I last mention the apartment?"

"What changed recently?"

"What do I know about Kuba?"

"Anything coming up this week?"

The frontend must NOT imply that only a tiny fixed list of questions is
supported.

Suggested questions may exist as onboarding helpers, but they must look like
examples rather than the product's full capabilities.

Answer rendering must be redesigned.

Do NOT render raw assertion lists.

Prefer:

- direct natural answer first;
- structured supporting items underneath when helpful;
- readable money/date formatting;
- grouped related items;
- optional evidence/details.

For example:

You're currently paying for:

PocketWave
€11/month
changed from €9 on Sep 1

rather than a raw list of subject/predicate/value assertion objects.

Show loading state that feels responsive.

Handle:

- deterministic immediate response;
- semantic response that takes longer;
- provider unavailable;
- no matching memory;
- unsupported/unanswerable question;

as distinct truthful states.

Do not use "No supported observations" as the normal user-facing failure copy.

==================================================
P0 — BOTTOM NAVIGATION
==================================================

Keep the main destinations:

Capture
Attention
Memory
Ask

The current tab model is acceptable.

Improve visual consistency and mobile ergonomics where needed.

The active state should be clear without excessive glow.

Attention badge only when > 0.

Do not add unnecessary navigation complexity.

==================================================
ACCESSIBILITY / RESPONSIVENESS
==================================================

Must work well on:

- narrow mobile viewport;
- normal desktop browser;
- installed PWA-like viewport.

Respect:

prefers-reduced-motion

Provide usable:

- focus states;
- keyboard behavior;
- ARIA labels;
- touch targets;
- color contrast.

Do not depend solely on color for semantic meaning.

==================================================
FRONTEND CONTRACT ISOLATION
==================================================

Because runtime V2 is being built concurrently, create or refactor a thin
frontend API/client boundary if useful.

The UI should not scatter raw backend response assumptions throughout rendering
code.

Prefer something like:

capture(...)
retractCapture(...)
getAttention(...)
getMemory(...)
ask(...)

or equivalent internal adapter.

Do not force these exact names.

Document the expected V2 integration contract.

Where the current V1 API differs, preserve backward compatibility only where it
does not compromise the new frontend architecture.

Do not edit backend files merely to satisfy frontend tests.

==================================================
TESTS
==================================================

Add deterministic frontend tests where supported by the repository's existing
test setup.

At minimum verify logically:

- plus button has a simple plus visual;
- composer accepts text;
- Enter submits;
- Shift+Enter inserts newline;
- attachment-only submission is permitted by frontend validation;
- attachment preview/removal;
- success toast contains Undo;
- reduced-motion path;
- Attention zero badge hidden;
- Attention human-readable item rendering;
- Memory does not expose raw assertion internals as primary UX;
- Ask renders natural answer data;
- provider/unavailable state is understandable;
- capture double-submit protection.

Do not call a live provider in tests.

==================================================
MANUAL VISUAL REVIEW
==================================================

If tooling allows, run the PWA locally with deterministic mocked/sample state
or the current backend without invoking live semantic provider calls.

Inspect at least:

- Capture mobile;
- attachment selected;
- capture success;
- Attention populated;
- Attention empty;
- Memory populated;
- Ask answer;
- Ask loading/error;
- desktop layout.

Record any visual limitations honestly.

Do NOT claim native-phone behavior unless actually tested.

==================================================
DOCUMENTATION / TRAJECTORY
==================================================

Create:

trajectories/coding/032-product-v2-ui-redesign/

with:

prompt.md
summary.md

Document:

- dogfooding problems addressed;
- files changed;
- screenshots/manual checks if generated locally;
- runtime integration requirements.

Do not modify historical V1 trajectories.

Make it explicit:

Product V2 UI is post-evaluation work and is not represented by the frozen
V1R1 benchmark score.

==================================================
GIT
==================================================

Commit only to:

product/v2-ui

Do NOT merge into master.

Do NOT merge runtime branch.

Do NOT push or expose oracle/scoring material.

If you push this temporary product branch, explicitly state that it is an
active implementation branch and will be deleted after integration.

Return:

# PRODUCT V2 UI REDESIGN GATE

PASS / PARTIAL / FAIL

Include:

branch
base SHA
final commit SHA
worktree path
screens/views redesigned
Capture behavior
attachment behavior
Undo behavior
Attention UX
Memory UX
Ask UX
API integration assumptions
tests
manual visual checks
known limitations
files changed

Explicitly confirm:

- no runtime worktree was modified;
- no backend semantic implementation was changed;
- no V1 benchmark/evaluator behavior was changed.
