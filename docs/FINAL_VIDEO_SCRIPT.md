# Final submission video script

Target length: 3–4 minutes. Use only a fresh synthetic demo Home prepared by
`scripts/prepare_product_v2_demo.py`, plus one live Capture. Never show a
personal Home, private dogfood, credentials, V1 expected output, or holdout
material.

## 0:00–0:25 — The problem

Show the Capture view.

Say:

> Life information arrives as fragments: a receipt, a deadline, a location, a
> preference, or a task. Most tools ask you to organize the fragment before
> it is safely out of your head. Blackhole is a zero-organization external
> memory: capture now, understand automatically, find it later.

## 0:25–0:55 — Immediate Capture

Type:

> I need to return the library books tomorrow.

Press Enter. Show the normal `Out of mind` feedback briefly; do not wait for
semantic processing.

Say:

> Capture returns immediately. The `Out of mind` feedback means the evidence
> has been accepted and saved; semantic understanding continues asynchronously.

Do not imply that the live capture is already understood.

## 0:55–1:35 — Attention and Memory

Open the prepared Attention view. Show an open parking deadline, its date, and
the `Why this is here` explanation. Then open Memory and show the current key
location, a Polish preference, and a price correction with the earlier value
retained under history.

If you mark an Attention item Done, show that it leaves the active list while
remaining available in Memory/history.

Say:

> Attention is a projection of what still needs me, not a dump of everything
> Blackhole has seen. Memory is current-first but keeps history, uncertainty,
> and provenance available. Unknown is a result, not a guess.

## 1:35–2:15 — Ask and provenance

Ask:

> Where are the basement keys now?

Show the answer and its supporting source. Ask a bounded follow-up:

> And what does Kuba like?

Say:

> Ask selects bounded evidence from structured memory, and the current question
> wins over stale thread context. Deterministic evidence selection, arithmetic,
> temporal normalization, lifecycle, occurrence aggregation, and provenance
> validation stay in Blackhole. For a normal READY semantic answer with usable
> evidence, the configured AI provider turns that bounded result into natural
> prose. Supporting evidence is secondary rather than becoming an audit-shaped
> wall of text.

If the local CLI is unavailable, show the honest pending/degraded state; do
not fabricate an answer.

Allow the normal READY Ask to take real provider time; do not describe Ask as
instant.

## 2:15–2:40 — Correction and Undo

Show the key correction or price history, then point to Undo on a disposable
capture.

Say:

> A correction changes the current projection without deleting the earlier
> evidence. Undo is explicit permanent forget for the selected Product V2
> capture and its source-linked state. It is not silent cleanup and does not
> rewrite unrelated memory.

Do not forget a prepared item needed for later shots.

## 2:40–3:20 — Evidence, honestly framed

Show `docs/SUBMISSION.md` or `docs/FINAL_H2H_REPORT.md`.

Say:

> The frozen V1 development benchmark improved from a stateless LQA-0M of
> 0.3015 to the kept Experiment 005 result of 0.8695, with DSCR improving
> from 277 to 40. That benchmark is frozen and belongs to V1.

> We also ran a separate post-freeze synthetic head-to-head. Raw-memory
> Prompt-to-Truth Score (PTS) was 0.8575 and Product V2 PTS was 0.7928, so
> Product V2 did not win this small aggregate comparison. Product V2 Attention
> F1 was 0.6795 versus 0.5641, and all 80 captures and 13 queries completed
> successfully. We show the mixed result because the product's value is the
> durable, inspectable state boundary—not a claim that one small set proves
> generalization.

## 3:20–3:45 — Close

Return to the product loop:

```text
Capture → background understanding → Attention / Memory → Ask → Undo
```

Say:

> Blackhole makes capture easy first, then makes the resulting state
> reviewable: current memory, open attention, grounded answers, uncertainty,
> history, and an explicit forget boundary. The repository keeps V1 science,
> Product V2 acceptance, process history, and the final descriptive H2H
> evidence separate so a judge can inspect each claim.

## Recording guardrails

- Prepare only synthetic state and show the normal `Out of mind` feedback long
  enough to prove that the raw evidence was accepted and saved.
- Allow a normal READY semantic Ask to take real provider time; do not describe
  Ask as instant.
- Do not wait for a multi-item provider burst on camera or call processing
  instant.
- Do not present Product V2 acceptance as unseen generalization.
- Do not call Prompt-to-Truth Score (PTS) `LQA-0M`; these are different
  contracts and metrics.
- Do not display raw run records, raw provider output, private transcript text,
  credentials, V1 expected output, or holdout material.
