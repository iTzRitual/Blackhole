# Representative runtime trajectory: simple capture

This is a representative deterministic local-demo trace, not a provider
transcript. It records one observed execution of the capture path.

## Input

`Remember to ask about the renewal date.`

## State before

- Demo seed loaded from `data/synthetic/demo-seed.json`.
- 14 raw captures, 24 current facts, and four relationships.
- No provider call was made.

## Instructions and operations

- User-facing instruction: save the fragment without asking for a category.
- `POST /api/capture` received the text.
- `app.demo.append_capture()` created a new raw event and rebuilt the local
  projection.

## Result

- New event: `capture-0015`, sequence 15.
- Source type: `text`.
- Semantic status: `pending`.
- No observation was created for the new event.
- Raw text remained available in the Recent captures view.

## User-visible outcome

`Saved.`

The capture route does not classify the input, read provider credentials, or
perform an external action. The machine-readable condensed trace is in
`trace.json`.
