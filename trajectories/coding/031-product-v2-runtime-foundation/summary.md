# Product V2 runtime foundation — trajectory summary

## Goal

Build the explicitly authorized post-evaluation Product V2 runtime foundation
in the isolated `product/v2-runtime` worktree, preserving the frozen V1R1
benchmark, evaluator, baseline evidence, calibration evidence, and frozen V1
runtime. The scope was capture-first open-world memory with durable deferred
processing, deterministic Attention/Ask paths, immutable attachments,
retraction, safe V1 migration, and reproducible no-live-provider tests.

## Agent/tool used

Codex coding agent using PowerShell, Python standard-library `unittest`,
`compileall`, the repository's deterministic benchmark-contract checker, and
read-only inspection of the installed Codex CLI help (`codex-cli
0.150.0-alpha.12.2`). No live semantic provider call was used for this task.

## Initial hypothesis

Product V2 can satisfy capture-first behavior without destabilizing the
evaluated V1 boundary if it owns a separate database/blob store and a durable
lease-based processing queue, while reusing only safe local provider discovery
and keeping deterministic projection/calculation logic in Blackhole-owned
code.

## Important implementation decisions

- Product V2 uses `blackhole-v2.db` and `blobs/` inside Blackhole Home; V1's
  `blackhole.db` remains a separate compatibility store.
- Captures append immutable source events and content-addressed blobs, then
  return `Saved.` before semantic processing. Text-only, attachment-only, and
  combined captures are supported; HTTP accepts bounded base64 bytes, while
  the local Python API may accept a caller-supplied path.
- Processing is chronological and lease-based. Stale claims recover, failed
  work is retryable, competing owners cannot claim the same event, later work
  waits behind an earlier non-processed event, and semantic rows plus the
  rebuildable projection commit atomically.
- The semantic contract is open-world and preserves known/inferred/unknown
  values, provenance, corrections, supersession, contradictions, duplicates,
  relations, Attention candidates, and append-only retractions.
- Relative time, timezone normalization, Attention state, and Decimal cost
  totals are deterministic. Product Ask uses bounded retrieval first and only
  calls bounded provider synthesis for questions that need it; simple paths do
  not call a provider.
- The local Codex adapter uses the inspected `codex exec` surface with
  ephemeral/read-only execution, isolated temporary output, structured output,
  `--image` for image attachments, and no token access or persistence. The
  product default remains `gpt-5.6-luna` with `high` reasoning, separate from
  the frozen benchmark's `max` configuration.
- V1 migration opens the legacy database read-only, copies raw and available
  derived state without rewriting the source, records imported semantic rows
  as processed, and leaves raw-only migrated events pending for explicit V2
  interpretation.
- Product V2 state/processing/attachment GET routes are read-only with respect
  to semantic work. Product Ask is POST-only. The legacy query GET route was
  also made read-only so URL prefetch cannot trigger V1 provider work.

## Tools/actions used

- Verified the target worktree and branch were based exactly on
  `68b7b15d353b12cffb65a770f8583aa0ebb849dd`.
- Added `app/product_v2.py`, `app/product_v2_store.py`,
  `app/product_process.py`, the versioned Product V2 prompt, deterministic
  Product V2 unit/HTTP tests, and the Host/API facade.
- Updated the required architecture, product, decision, reproduction,
  README, and trajectory-index documentation without rewriting historical
  experiment results.
- Inspected and then restored the unchanged tracked
  `eval/results/contract-smoke.json` after its checker rewrote only working
  tree line endings.

## Failures, retries, and changed approaches

- The first architecture documentation patch used a stale ending context and
  was rejected by `apply_patch`; the same addition was reapplied using the
  exact current final lines.
- An early HTTP lifecycle smoke exposed SQLite thread-affinity during managed
  server shutdown. The V1 connection now explicitly permits the already
  serialized Host ownership model to close across handler/main threads; V1
  schema and projection behavior did not change.
- During implementation, sequence allocation was moved into the Product V2
  capture transaction to avoid concurrent Host sequence races. Blob
  publication was tightened from replace semantics to collision-safe atomic
  hard-link publication with content verification.

## Human feedback or checkpoints

The human-provided pasted instruction authorized this exact isolated
post-evaluation scope and required the `031-product-v2-runtime-foundation`
trajectory. No additional human feedback or checkpoint was received during
implementation.

## Evaluation performed

- `python -m unittest discover -s app/tests -p "test_*.py" -q` — 92 tests,
  pass.
- `python -m unittest discover -s . -p "test_*.py" -q` — 102 tests, pass.
- `python -m compileall -q app eval scripts` — pass.
- `python benchmark/dev/generate_benchmark.py --check` — pass; 200 events and
  4 checkpoints structurally checked, with no scoring run.
- `git diff --check` — pass.
- No holdout/oracle/scoring worktree or benchmark expected output was
  accessed. The machine-readable non-scored validation record is
  `eval/results/product-v2-runtime-foundation.json`.

## Result

`PRODUCT V2 RUNTIME FOUNDATION GATE: PASS` for the authorized backend/API and
deterministic-test scope. The captured behavior, processing lifecycle,
open-world state, time/Attention projection, bounded Ask, attachments,
retraction, migration, and V1 compatibility checks are covered by the passing
suite.

## Regressions or unresolved issues

No known test regressions remain. This change does not claim a redesigned PWA,
production hosting, LAN pairing, remote access, multi-user isolation, OCR, a
Claude adapter, or consequential-action execution. No live Codex semantic
smoke was run; provider wiring is covered by the injected fake seam and the
inspected CLI invocation contract. Product V2 has no benchmark score and must
not be used to infer or tune V1R1/generalization performance.

## Final decision

KEEP the authorized Product V2 runtime foundation as a post-evaluation product
development milestone. It is not Experiment 006 and does not alter the frozen
V1 evidence.

## Related git commit

`2ec991d` (`product: add V2 runtime foundation`)
