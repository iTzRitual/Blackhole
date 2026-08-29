# Host + PWA end-to-end integration

## Status

Complete. No authentic coding-session
transcript was available and none was fabricated. A separate authentic runtime
trajectory was recorded for the real neutral smoke.

## Goal

Integrate the approved `ui/mobile-pwa` PWA with the Blackhole Host through a
same-origin local HTTP transport, reuse HostRuntime/StateStore for all domain
state, preserve the approved UI, and prove the capture-now/understand-later
flow with fake-provider HTTP tests and one neutral real Codex smoke when
available.

## Initial hypothesis

The existing local PWA can remain visually unchanged while a thin HTTP layer
maps its Capture, Memory, Attention, and Ask interactions to HostRuntime. Ask
can safely trigger deferred freshness and then use a deterministic query/view
boundary over the Host-owned snapshot, without direct app-to-Codex access or a
second demo database.

## Starting state and human checkpoints

- Backend base: `11d8a041fedc027ca705e8616085c05ef18d9b57`.
- UI branch: `ui/mobile-pwa` at
  `0cc665397ddf50fb4fb4f816e2c88bf0b27eeb64`.
- Integration branch/worktree: `integration/host-pwa` at
  `C:/Users/natan/OneDrive/Dokumenty/ChatGPT/Blackhole-integration`.
- The UI branch was merged with `--no-ff` before implementation; the merge had
  no conflicts.
- `master` and the UI worktree are outside the implementation scope.

## Scope constraints

- Preserve the frozen Gate A benchmark, response contract, evaluator,
  baseline-v1, calibration evidence, and E005 result.
- Do not start E006, generalization, Claude, OCR, scheduling, production
  infrastructure, public networking, or device pairing.
- Do not visually redesign the approved PWA or claim binary attachment
  persistence/offline sync that does not exist.

## Important implementation decisions

- Created the integration worktree from backend Host Foundation SHA
  `11d8a041fedc027ca705e8616085c05ef18d9b57` and merged UI SHA
  `0cc665397ddf50fb4fb4f816e2c88bf0b27eeb64` with `--no-ff`. The merge was
  conflict-free; the merge commit is `d275a71`.
- Replaced the seeded demo transport with a same-origin HostRuntime transport.
  Requests use a serialized server lock and request-scoped HostRuntime/SQLite
  connections. Normal startup never seeds the demo database.
- Added `POST /api/capture`, `POST /api/process`, `POST /api/retry`, and
  `POST /api/query`, plus safe health/status/processing/state reads. Capture
  persists immutable raw evidence and pending status without provider work.
  Ask calls `ensure_state_fresh()` before querying.
- Extracted the earlier deterministic view/routing behavior into the
  database-free `app/query_service.py`. Added a benchmark-independent generic
  runtime contract so product entities are not constrained to frozen benchmark
  subjects. The frozen benchmark contract remains untouched.
- Kept the PWA's approved visual and interaction treatment. Changed only Ask
  to POST to the Host and removed the destructive demo-reset action that had
  no safe normal-Host meaning. The service worker continues to bypass `/api/`.
- Default binding is loopback. Non-loopback binding requires explicit
  `--trusted-lan-demo` and prints a no-auth/private-network warning. No
  pairing, device tokens, TLS, tunnels, cloud relay, public networking, shell
  routes, OCR, scheduler, or arbitrary attachment persistence was added.

## Tools and actions

- Inspected the backend and UI worktrees, created the isolated worktree, and
  performed the intentional no-conflict UI merge.
- Used `apply_patch` for source, test, documentation, and trajectory changes.
- Added fake-provider HTTP/PWA tests and a small reproducible real-smoke
  harness under `scripts/host_smoke.py`.
- Ran the real local Codex CLI discovery (`codex-cli 0.150.0-alpha.12.2`,
  authenticated) and one neutral HTTP smoke with the synthetic Northstar Cloud
  storyline. Its safe trace is in
  `trajectories/runtime/019-host-pwa-real-neutral/trace.json`.
- Ran generator/contract checks, the frozen deterministic E005 replay, protected
  artifact hash audits, compilation, the full stdlib suite, and diff checks.

## Failures and changed approaches

- Direct execution of `scripts/host_smoke.py` failed because Python's import
  path started in `scripts/`; the documented/reproducible module form
  `python -m scripts.host_smoke` succeeded.
- The first E005 replay attempt used a trajectory path outside the repository;
  the existing runner requires repository-relative call paths. The replay was
  rerun in a newly created repository-local validation directory and the exact
  temporary directory was removed afterward.
- The worktree's line-ending normalization initially made raw PowerShell
  hashes differ from the clean master checkout. Protected files were restored
  byte-for-byte from the clean master checkout and staged only with
  `git add --renormalize`; no protected Git content changed.

## Human checkpoint and scope

The task was explicitly authorized as App + Host end-to-end integration on a
new branch. Master was not modified and the UI worktree was not modified in
place. This is a product-runtime milestone, not Experiment 006 and not a
benchmark optimization. The frozen Gate A benchmark, expected output,
response-contract-v2, official baseline-v1, evaluator, calibration evidence,
and E005 result remained outside the change set.

## Evaluation

- Full stdlib suite: 70 tests passed.
- Fake HTTP/PWA suite: 7 Host web lifecycle/security tests plus 3 static PWA
  checks passed; included immediate capture, pending state, Ask freshness,
  idempotent Ask, provider-unavailable behavior with and without pending work,
  retry, no-secret/auth surface, traversal, bind policy, and asset routes.
- `python benchmark/dev/generate_benchmark.py --check`: 200 events and four
  checkpoints verified.
- `python eval/contract_smoke.py`: non-scored contract smoke passed.
- Deterministic E005 replay: four checkpoints, `LQA-0M=0.8695006212469447`,
  `DSCR=40`, and zero provider usage; the kept E005 artifact was not rewritten.
- Protected hashes matched the clean master checkout for the development case,
  expected output, response contract, baseline-v1, and E005 result.
- Real neutral smoke: two immediate pending saves, one real deferred Codex
  processing call, rebuilt state with 2 captures/3 current facts/1 relation,
  and a history answer containing 18 and 22 EUR. The safe HTTP layer does not
  expose provider token usage.

## Result and unresolved issues

The integration proves the intended `Capture -> Saved. -> pending -> Ask ->
Host freshness -> deferred provider -> rebuild -> deterministic answer` path
without a second database or direct PWA-to-Codex coupling. The real neutral
provider call did not link both mentions to one stable named entity; it emitted
capture-scoped subjects. The effective date was stored but not surfaced by the
bounded history answer. These are recorded as limitations, not concealed by
prompt tuning. The fake-provider suite proves the intended same-entity
correction path.

## Final decision

KEEP as the scoped Host/PWA integration milestone. Do not merge this branch to
master as part of this task. Pairing/authentication, robust novel-entity
resolution, richer query planning, and public/remote networking remain future
human-approved work.

## Related git commits

- `d275a71 merge: integrate mobile PWA workstream`
- `integration: connect PWA to Blackhole Host` (final integration commit;
  the resulting SHA is reported in the task handoff because embedding a
  commit's own hash in its content would be self-referential).
