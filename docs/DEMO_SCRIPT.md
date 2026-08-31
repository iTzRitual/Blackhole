# Blackhole demo script

Target length: five minutes or less. Use only the prepared synthetic Home and
one live capture. Do not wait for a multi-item live provider burst on camera.

## Before recording

Prepare a fresh or empty demo Home through the normal Product V2 HTTP contract:

```text
python scripts/prepare_product_v2_demo.py --home <new-empty-demo-home>
python -m app.web_app --home <new-empty-demo-home> --host 127.0.0.1 --port 8080
```

The preparation utility uses the visible deterministic acceptance provider,
processes the state before the demo, and prints only safe counts and paths. It
uses synthetic content: a parking deadline, a Polish preference, a bilingual
key correction, a PocketWave price change, and an uncertain boiler-warranty
mention. It refuses to populate a non-empty Home.

The `?fixture=1` browser mode is only a visual-test fixture and must not be
presented as Product V2 state. Never point the demo at a personal Home.

## 0:00–0:30 — Problem

Show the Blackhole title and Capture view.

Say:

> Life information arrives faster than people organize it: a reminder, a
> receipt, a location, a preference, a bill. Most tools add work at the exact
> moment someone is trying to get something out of their head.

Blackhole is zero-organization external memory: capture now, understand
automatically, find it later.

## 0:30–1:00 — Capture

Type one ordinary synthetic note, for example:

> I need to bring the library books back tomorrow.

Press Enter. Show the normal `Out of mind` feedback. Do not wait for semantic
processing or imply that the capture has already been understood.

Say:

> Capture returns immediately. The `Out of mind` feedback means the raw evidence
> has been accepted and saved; semantic understanding happens asynchronously in
> the background.

The live capture is the proof of the immediate-save boundary. It may remain
pending in the prepared demo Home, which is an honest state.

## 1:00–1:30 — Attention

Open Attention in the already-prepared state. Show:

- the open parking-permit deadline and its date;
- the `Why this is here` detail; and
- the active badge containing only unresolved/open items.

If the warranty item is visible, show that its December mention is uncertain,
not a confirmed deadline. Do not mark an item complete on camera unless the
purpose is to show that it leaves the active list.

Say:

> Attention is not an inbox of everything Blackhole has seen. It is the small
> set of things that still need the user: a deadline, an unresolved point, a
> meaningful change, or a proposed action. Completed and cancelled items do not
> remain active by default, but remain inspectable in Memory/history.

## 1:30–2:15 — Memory

Open Memory and show current-first cards. Use the prepared synthetic examples:

- current basement-key location at the desk, with the earlier Mum's-house
  statement retained as correction/history;
- Kuba's green Lidl pasta preference, captured in Polish; and
- PocketWave at `11 EUR`, with the earlier `9 EUR` value visible as history.

Expand one detail so the source capture/provenance is visible. If the warranty
card is shown, call out `unknown` or uncertain explicitly.

Say:

> Memory is open-world. It can retain a preference or a location without a
> form, and it separates current state from history. Unknown is a result, not a
> blank to fill with a guess.

## 2:15–3:00 — Ask

Open Ask and ask in English about the Polish capture:

> Where are the basement keys now?

Show the answer and its supporting source reference. Then ask a contextual
follow-up such as:

> And what does Kuba like?

The follow-up demonstrates bounded, temporary Ask thread context. If a
provider-backed answer is required and the local Codex CLI is unavailable, say
so and continue with the prepared Memory view; do not turn the failure into a
fabricated answer and do not start a live multi-capture burst during the
recording.

The normal READY semantic path may take real provider time. It renders natural
prose from the bounded structured result; deterministic evidence selection,
arithmetic, temporal normalization, lifecycle, occurrence aggregation, and
provenance validation remain local. A provider-unavailable path may show an
explicitly degraded deterministic fallback.

Say:

> Ask is grounded retrieval over the same personal state. The capture language
> does not become the memory's identity, and supporting evidence is selected
> narrowly rather than citing every candidate that happened to be retrieved.

## 3:00–3:30 — Semantic truth

Return to the key correction or PocketWave history. Show:

> Mum's house → desk

or:

> 9 EUR → 11 EUR

Say:

> This is not last-write-wins. A correction changes the current projection while
> preserving the earlier evidence and the relationship between the two values.
> Conflicting or uncertain claims stay visible instead of being silently made
> certain.

## 3:30–3:50 — Undo

Point to Undo on a disposable capture, or explain it from the prepared state:

> Undo is an explicit permanent-forget action for the selected Product V2
> capture. It removes the capture's source-linked Memory, Attention, provenance,
> and unreferenced attachment state inside the Product V2 Home. It is not
> automatic cleanup and it does not silently rewrite unrelated evidence.

Do not Undo a prepared fact that is needed for the remaining shots.

## 3:50–4:30 — Measured engineering result

Show [`docs/SUBMISSION.md`](SUBMISSION.md) or the linked result artifacts.

Say:

> The scientifically evaluated V1 development track improved from a stateless
> baseline LQA-0M of `0.3014914553` to the kept Experiment 005 result of
> `0.8695006212`, with DSCR improving from 277 to 40. The benchmark is frozen at
> 200 events and four checkpoints.

Then immediately add:

> On three fresh synthetic post-freeze worlds, the macro LQA difference was
> only `+0.0120635896`. That is a shadow/generalization result, not an official
> holdout or a significance claim. The large DEV gain did not transfer as
> strongly as expected.

Use the lesson as the transition:

> Optimizing an agent for measurable structured correctness can accidentally
> optimize the product away from the user.

## 4:30–5:00 — Close

Show the final Product V2 screen, then the README and reproduction links.

Say:

> Blackhole makes capture easy first, then makes the resulting state reviewable:
> current memory, open attention, grounded questions, uncertainty, history, and
> an explicit Undo. The repository separates V1 scientific evidence from the
> Product V2 product acceptance evidence and includes the deterministic checks
> needed for a judge to clone, run, and inspect it.

## Recording guardrails

- Use synthetic state only; no private human dogfood capture, screenshot, log,
  or browser profile belongs in the recording or repository.
- Show the normal `Out of mind` feedback long enough to show that the raw
  evidence was accepted and saved.
- Do not claim that background understanding is instant. Prior live dogfood
  measured a first useful state around 23 seconds and a remaining burst around
  129.562 seconds.
- Do not present Product V2's `50/50` acceptance as unseen generalization or
  present V1 benchmark scores as Product V2 scores.
- Do not open benchmark holdout expected output, V1 oracle/scoring worktrees,
  credentials, or local machine-specific files.
