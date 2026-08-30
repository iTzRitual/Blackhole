# Product V2 UI integration contract

Status: frontend contract for the integrated, post-evaluation Product V2 UI and Host. This document does not change the frozen runtime contract or benchmark.

## Adapter boundary

The web client owns presentation state only. Its adapter is expected to expose these domain operations:

```text
getState() -> StateSnapshot
capture({ text?: string, attachment?: Attachment }) -> CaptureResult
retractCapture(captureId) -> UndoResult
ask(question) -> AnswerResult
```

`text` is optional when an attachment is present. An `Attachment` should carry the source handle or upload result plus `name`, `type`, `size`, and whether it is an image. The transport preserves the original source during normal operation; an explicit Undo is the user-authorized deletion exception. The UI must not OCR a file or copy its contents into the text composer as a fallback.

## Response shapes

The UI normalizes responses at the boundary. A compatible `StateSnapshot` can provide:

- `attention`: an array, or an object containing `items`, with human-readable title, context, urgency, status, evidence, and optional action metadata;
- `memory`: open-world `entities`, `topics`, or `groups`, or equivalent arrays. Each item may include a human name/kind, summary, facts, status, and evidence/provenance;
- optional processing and freshness metadata.

An `AnswerResult` should provide a direct `summary` or `answer` first, followed by grouped supporting `items`, `groups`, or `sections`. Supported states include `ready`, `no_match`, `unsupported`, and `provider_unavailable` (or an equivalent typed error). Unknown, missing, and not-yet-checked values must remain distinguishable from false, zero, or completion.

`CaptureResult` should return a durable capture identifier, saved status, and processing status. `UndoResult` should identify the capture and report `forgotten`, `deleted`, or `already_deleted`; it must not expose the deleted capture's content. The existing `retractCapture` name and route are compatibility names for this permanent operation.

## Integrated Host transport and fixture mode

The integrated client uses the Product V2 same-origin routes:

- GET /api/v2/state for read-only Memory, Attention, source, attachment, and processing state;
- POST /api/v2/capture for text-only, attachment-only, and combined capture;
- POST /api/v2/retract for permanent user Undo/forget;
- POST /api/v2/ask for natural Ask; and
- GET /api/v2/attachments/<sha256> for retrieval of live immutable attachment bytes; forgotten blobs are unavailable.

Browser attachments are sent as bounded data_base64 content with filename and
MIME metadata. The UI never reads file text as a fallback and never waits for
semantic processing before clearing the composer. Processing status is read from
the V2 snapshot and polled while work is pending or running; a failed provider
leaves the saved capture visible as a retryable state.

The ?fixture=1 (with ?fixture=empty and ?fixture=unavailable variants) query
modes remain deterministic UI-only fixtures for visual interaction checks. They
are not benchmark data, ground truth, or the normal Host path.
