# Hackathon video script

Target length: about 4 minutes 30 seconds. Every number below is taken from a
committed artifact or from the deterministic local demo; no claim depends on a
private holdout result.

## 0:00–0:25 — The problem

**On screen:** Blackhole title, then the Capture view.

**Voiceover:**

“Everyday information arrives as fragments: a receipt, a reminder, a bill, a
contract, a task. The friction is that most tools ask us to organize before we
have even captured the thought. Blackhole is a zero-organization personal
inbox: capture now, organize later.”

## 0:25–1:05 — Capture

**On screen:** Type a short reminder and click Save capture. Show the `Saved.`
feedback and the new raw capture in the inbox.

**Voiceover:**

“The first interaction is intentionally quiet. One universal input accepts a
fragment without a folder, category, or schema. In this local demo, the capture
is immediately stored as an immutable raw event. It is not synchronously
classified, and the demo does not silently call a model.”

## 1:05–2:00 — Attention and memory

**On screen:** Open Attention, then Memory. Pause on the open deadline and the
approval-gated proposed transfer. Scroll to subscription history, task
reassignment, missing period, unknown amount, and duplicate.

**Voiceover:**

“Later, structured state can do the organizing. Attention is a short list: this
open deadline needs review, and this proposed transfer is not executed because
approval is required. Memory keeps the current subscription price separate from
its earlier charge and price. It shows that a task moved from Alex to Sam and
was then cancelled. It also shows a missing bill period as unobserved, not zero,
and a missing repair amount as unknown. Evidence references stay attached to the
facts.”

## 2:00–2:30 — Ask

**On screen:** Ask Blackhole; run “What changed recently?” and “What
information is incomplete?”

**Voiceover:**

“Ask is a structured lookup over the same state, not a second giant chat
memory. The demo routes a question to a deterministic projection and renders
the answer with known, inferred, or unknown status and source references.”

## 2:30–3:15 — Architecture and safety

**On screen:** Show the architecture diagram in `docs/ARCHITECTURE.md`, then the
repository tree or files `state_store.py`, `response_projector.py`, and
`demo.py`.

**Voiceover:**

“The core boundary is append-only raw SQLite events, structured observations and
relationships, a rebuildable projection, and query-scoped responses. Raw
sources are immutable. Derived state can be rebuilt. Deterministic arithmetic,
dates, duplicate checks, and aggregates belong to code or SQL. Unknown remains
unknown. No consequential action is executed automatically. The separate live
semantic runtime is subscription-first through an installed local Codex CLI;
Blackhole never reads or persists provider credentials.”

## 3:15–4:00 — What we measured

**On screen:** Open `eval/results/final-comparison-v1.json` and highlight the
baseline/advanced comparison and checkpoint table.

**Voiceover:**

“The fair public development benchmark is frozen at 200 events with checkpoints
at 50, 100, 150, and 200. The official stateless baseline is
`LQA-0M 0.3014914553`, with DSCR 277. The latest kept advanced replay is
`0.7492295899`, with DSCR 72. That is an absolute LQA-0M delta of
`0.4477381346`; it is development evidence, not a holdout or production claim.
The advanced checkpoint scores are 0.7963, 0.7523, 0.7064, and 0.7419. We do
not claim monotonic degradation. The measured interpretation is narrower:
long-context access alone is not the same thing as a structured, rebuildable
memory system.”

## 4:00–4:30 — Honest close

**On screen:** README, reproduction commands, and the four runtime trajectory
folders.

**Voiceover:**

“The product is intentionally a scoped hackathon slice, not production
infrastructure. The public benchmark, response contract, baseline, and
calibration evidence remain frozen. Relation-detail extraction was audited and
deferred because the missing edges were not recoverable from recorded state
alone. The repository includes reproducible demo commands, deterministic tests,
runtime evidence, and a judge-facing reproduction protocol. Blackhole makes
capture easy first, then makes state trustworthy enough to review.”
