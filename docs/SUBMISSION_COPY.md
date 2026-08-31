# Submission copy

## Title

Blackhole — zero-organization external memory

## One-line pitch

Capture the fragments of ordinary life now; Blackhole turns them into a
reviewable Memory, a small Attention list, and grounded answers later.

## Problem

Life information arrives as scattered receipts, reminders, locations,
preferences, documents, and half-formed tasks. Existing tools often require
classification before capture is safe. Blackhole starts with one quiet inbox:
save the evidence first, then organize it automatically.

## What we built

Blackhole is a local-first Product V2 application with immediate `Out of mind`
Capture feedback after raw evidence is durably saved, asynchronous
understanding, current-first Memory, open Attention, bounded Ask, provenance,
multilingual semantic identity, and explicit permanent Undo. Raw sources stay
immutable during normal operation; derived state is rebuildable; unknown
remains unknown; dates, arithmetic, lifecycle, and aggregation remain
deterministic; consequential actions require approval.

The application uses an already-installed, already-authenticated local Codex
CLI. The CLI owns authentication. Blackhole never requests, reads, copies,
exports, or persists provider tokens.

For a normal READY semantic Ask with usable evidence, the configured provider
turns the bounded deterministic result into natural prose. Blackhole owns
evidence selection, arithmetic, temporal normalization, lifecycle, occurrence
aggregation, and provenance validation; a degraded deterministic fallback is
reserved for provider-unavailable cases.

## Evidence

The frozen V1 development track is one 200-event scenario with four
checkpoints. Its official stateless baseline is `LQA-0M 0.3014914553`,
`DSCR 277`; the final kept Experiment 005 replay is `LQA-0M 0.8695006212`,
`DSCR 40`. Those are V1 development measurements, not Product V2 scores.

The final Product V2 stateful-vs-raw-memory comparison is a separate,
post-freeze descriptive run over four new synthetic worlds. Both systems used
`gpt-5.6-luna` with low reasoning. Raw-memory Prompt-to-Truth Score (PTS) was
`0.8575`; Product V2 PTS was `0.7928`. Product V2 Attention F1 was `0.6795`
versus `0.5641` for raw-memory, with 80/80 captures processed and 13/13
queries schema-valid.
The mixed result is published honestly: Product V2 is a product architecture
and trust-boundary submission, not a claim that a small new set proves
generalization.

## Why it matters

The important design lesson was that benchmark correctness and user trust are
not identical. A good personal-memory product must preserve history while
showing current truth, keep uncertainty visible, avoid Attention noise, ground
answers in evidence, and let the user permanently forget a mistaken capture.

## Limitations

This is a local single-user hackathon implementation, not production
infrastructure. Live provider processing is slower than desired, attachment
understanding is bounded, and pairing, cloud sync, hosted deployment, OCR
guarantees, and public remote security are out of scope. The final H2H result
is synthetic, descriptive, and not an official holdout.

## Links

- [README](../README.md)
- [Submission narrative](SUBMISSION.md)
- [Final H2H report](FINAL_H2H_REPORT.md)
- [Demo/video script](FINAL_VIDEO_SCRIPT.md)
- [Sanitized H2H result](../eval/results/final-h2h-001-summary.json)
