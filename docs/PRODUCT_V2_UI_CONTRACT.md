# Product V2 UI integration contract

Status: frontend contract for the isolated, post-evaluation Product V2 UI worktree. This document does not change the frozen runtime contract or benchmark.

## Adapter boundary

The web client owns presentation state only. Its adapter is expected to expose these domain operations:

```text
getState() -> StateSnapshot
capture({ text?: string, attachment?: Attachment }) -> CaptureResult
retractCapture(captureId) -> RetractionResult
ask(question) -> AnswerResult
```

`text` is optional when an attachment is present. An `Attachment` should carry the source handle or upload result plus `name`, `type`, `size`, and whether it is an image. The transport must preserve the original source as immutable evidence; the UI must not OCR a file or copy its contents into the text composer as a fallback.

## Response shapes

The UI normalizes responses at the boundary. A compatible `StateSnapshot` can provide:

- `attention`: an array, or an object containing `items`, with human-readable title, context, urgency, status, evidence, and optional action metadata;
- `memory`: open-world `entities`, `topics`, or `groups`, or equivalent arrays. Each item may include a human name/kind, summary, facts, status, and evidence/provenance;
- optional processing and freshness metadata.

An `AnswerResult` should provide a direct `summary` or `answer` first, followed by grouped supporting `items`, `groups`, or `sections`. Supported states include `ready`, `no_match`, `unsupported`, and `provider_unavailable` (or an equivalent typed error). Unknown, missing, and not-yet-checked values must remain distinguishable from false, zero, or completion.

`CaptureResult` should return a durable capture identifier, saved status, and processing status. `RetractionResult` should identify the derived retraction and its capture identifier; it must not claim that immutable source evidence was physically deleted.

## Current compatibility and fixture mode

The current Host-compatible adapter uses same-origin `/api/state`, `/api/capture`, and `/api/query` where available. That path currently requires text for capture, accepts metadata rather than a binary upload, and has no `/api/capture/retract` route. The V2 UI therefore uses `?fixture=1` (with `?fixture=empty` and `?fixture=unavailable` variants) for deterministic attachment, Undo, populated/empty, and provider-error behavior. Fixture results are UI fixtures only and are not benchmark data or ground truth.

The next Host integration must add the approved binary-source transport and derived retraction capability behind the adapter. It must not make capture wait for provider work, expose provider internals as primary copy, or weaken the approval and provenance boundaries.
