# Task summary

## Goal

Implement the authorized final Product V2 task from the referenced pasted
instruction on an isolated worktree based exactly on
`05c337b46798031adea8ee0f1cf6b34b40572bc1`: permanent Undo/forget, concise
sanitized operational logs, required deterministic regressions, the visible
50-case acceptance run, the bounded live smoke, documentation, and a coherent
target-branch commit. Preserve the frozen V1 benchmark/evaluator/baseline,
holdout boundary, source semantic-truth worktree, master, and other protected
worktrees.

## Agent/tool used

Codex desktop agent using PowerShell, `apply_patch`, local Python/Node
validation commands, the existing Product V2 acceptance/evaluator runners,
and the already-installed authenticated local Codex CLI through the normal
web launcher. No provider token was requested, read, copied, exported, or
persisted.

## Initial hypothesis

A narrow transactional forget operation with an event-ID-only tombstone,
lease-aware late-result handling, reference-safe attachment garbage
collection, and bounded lifecycle logging can permanently remove one mistaken
capture without mutating unrelated Product V2 state or reopening the frozen V1
track.

## Important implementation decisions

- Added `ProductStore.forget()` as the explicit destructive exception to normal
  source immutability. It removes the source event, processing state,
  source-linked derived/provenance rows, and unreferenced content-addressed
  blobs, then rebuilds the remaining projections.
- Added a minimal `deleted_events(event_id, deleted_at)` tombstone to make
  repeated Undo idempotent and prevent silent event-ID reuse. The existing
  `retract`/`product_retract`/`retractCapture` names remain compatibility
  surfaces for the permanent operation; `product_forget` is the explicit host
  method.
- Scrubbed shared fact/relation/Attention references and removed deleted
  target relations. The processing ownership check plus bounded survivor
  recheck prevents a late provider result, including a mixed batch, from
  resurrecting deleted content or retrying an unrelated live event.
- Added `ProductOpsLogger` with timestamped, line-oriented capture, queue,
  provider, Memory, Attention, Ask, Undo, worker, and server events. IDs,
  errors, and paths are bounded/sanitized; capture/question/provider payloads
  and credentials are not logged.
- Updated only the visible Product V2 acceptance Undo expectation and
  adapter/harness contract from raw preservation to permanent forgetting. No
  `benchmark/`, evaluator-owned holdout, official baseline, calibration, or
  V1 result artifact was changed.

## Tools/actions used

- Read the referenced pasted instruction before implementation.
- Verified the semantic-truth source worktree was clean at
  `05c337b46798031adea8ee0f1cf6b34b40572bc1`, created target worktree
  `Blackhole-v2-undo-logs` on `product/v2-undo-logs`, and worked there only.
- A first trajectory-file patch was accidentally applied to the master
  workspace root; the two files were immediately removed with `apply_patch`,
  and master/source cleanliness and SHAs were reverified.
- Added the implementation, 18 dedicated Undo/logging tests, acceptance
  contract updates, the live runner, documentation, changelog, and this
  evidence record.
- Ran the one authorized live sequence through `python -m app.web_app` with a
  fresh temporary `BLACKHOLE_HOME`, without using `/api/v2/process` or
  `/api/v2/retry`.

## Failures encountered

- The first dedicated logging run exposed a positional-name collision in the
  logger API and underscore-normalized human event labels; both were fixed at
  the logger boundary.
- An orphan-blob regression initially called the public `blob_path()` helper
  after its database row had correctly been removed; the test was corrected
  to inspect the content-addressed path directly.
- Review identified a mixed-batch Undo/commit race that could have retried a
  surviving event; survivor filtering and bounded lease rechecks were added
  and the regression passed.
- The live runner's Windows signal shutdown did not capture the final worker
  and server stop lines. This leaves the live artifact `structural_ok=false`
  for that logging subcheck only; deterministic clean-stop coverage passed.

## Retries or changed approaches

- Re-ran the focused and full deterministic suites after each logging and
  batch-race repair. Re-ran the visible 50-case acceptance after the final
  implementation repair.
- Did not repeat the capped live sequence after the shutdown-stream
  limitation; no additional live captures, Ask requests, or provider retries
  were issued.

## Human feedback or checkpoints

The user supplied the scoped `/goal` instruction and the exact pasted-file
reference. No additional human feedback or checkpoint was received.

## Evaluation performed

- Exact-base baseline before implementation: `python -m unittest discover -s
  app/tests -p 'test*.py'` -> `146` passed.
- Dedicated Undo/logging suite: `18/18` passed.
- Final application suite: `python -m unittest discover -s app/tests -p
  'test*.py'` -> `164/164` passed.
- Evaluator suite: `10/10` passed.
- Product acceptance harness: `7/7` passed; combined focused Undo plus
  harness check: `24/24` passed.
- Visible Product V2 integrated acceptance: `50/50 PASS`, zero FAIL/PARTIAL/
  NOT TESTED, latency gate PASS; report in
  `eval/results/product-v2-integrated-acceptance.json`.
- `python benchmark/dev/generate_benchmark.py --check` -> `200` events and
  `4` checkpoints; qualification had no hard failures and four pre-existing
  warnings; compileall and `node --check app/web/app.js` passed.
- Authorized live smoke: `3/3` saves, capture 2 permanently forgotten, `2/2`
  remaining provider processes at attempt 1, zero failures/retry scheduling,
  `2/2` HTTP-200 provider-free Ask responses with relevant refs, Attention
  children item present, sanitized logs max `277` characters. Final record:
  `live-validation.json`.

## Result

The authorized Product V2 implementation and documentation are complete. The
deterministic and visible acceptance gates pass. The live functional gate
passes for capture, permanent Undo, processing, Memory, Attention, Ask,
provenance absence, and retry safety; the overall live artifact is PARTIAL
only because the Windows launcher stop signal did not expose two final log
lines.

## Regressions or unresolved issues

- No deterministic, evaluator, acceptance-harness, visible 50-case, V1,
  benchmark-structure, compile, JavaScript, or source-boundary regression
  remains.
- The live runner should use a more reliable graceful Windows shutdown
  mechanism if a future authorized smoke needs to assert the final stop lines.
  This was not retried under the three-capture/two-Ask live cap.

## Final decision

**KEEP** the permanent Undo/forget, batch-race handling, attachment GC, and
sanitized operational logging changes. Report the live validation as
**PARTIAL** only for shutdown-line capture; deterministic clean-stop logging
passes.

## Related git commit

a719e9a (`product: make Product V2 Undo permanent and add ops logs`).
