# Human-authorized integration task

This file records the human instruction that authorized the App + Host
end-to-end integration. It is a faithful task summary prepared from the
referenced task document, not an exported agent transcript.

The deferred-ingestion and Host Foundation workstreams are complete and KEEP.
The backend base is `11d8a041fedc027ca705e8616085c05ef18d9b57`, with frozen E005
evidence of LQA-0M `0.8695006212469447` and DSCR `40`. The UI worktree is
`C:/Users/natan/OneDrive/Dokumenty/ChatGPT/Blackhole-ui` on
`ui/mobile-pwa`, UI SHA `0cc665397ddf50fb4fb4f816e2c88bf0b27eeb64`.

Create a new integration worktree at
`C:/Users/natan/OneDrive/Dokumenty/ChatGPT/Blackhole-integration` on branch
`integration/host-pwa`, based on the backend SHA. Preserve both histories by
merging `ui/mobile-pwa` with `git merge --no-ff`; resolve conflicts intentionally
if any. Do not work directly on `master`, do not modify the UI worktree in
place, and do not merge the integration branch back into `master` in this
task.

Integrate the approved mobile PWA with Blackhole Host through a local
same-origin HTTP transport:

```text
BLACKHOLE APP -> BLACKHOLE HOST HTTP TRANSPORT -> HostRuntime
              -> IngestionEngine / StateStore -> Codex CLI
```

The final product flow must demonstrate `capture now -> Saved immediately`,
then `Ask -> ensure state fresh -> deferred Codex semantic processing ->
rebuild structured state -> answer from Blackhole-owned state`. Do not redesign
the benchmark or visually redesign the approved PWA.

Refactor `app/web_app.py` from the demo transport into a HostRuntime-backed
same-origin server that serves the PWA static assets and domain API. The web
server must contain request validation and safe response mapping only; it must
not contain extraction, Codex command construction, reconciliation, benchmark,
or expected-output logic. Implement the domain API for health, host status,
processing, state, capture, process, retry, and query. Do not expose shell,
arbitrary Codex commands, SQL, unnecessary paths, credentials, raw stderr, or
chain-of-thought.

Keep `/api/health` cheap and free of semantic/provider refresh work. Keep
capture synchronous, raw-only, provider-free, and small in its response. Allow
processing to be substantial and return a safe summary. Make Ask call
`HostRuntime.ensure_state_fresh()` before a bounded deterministic query service
answers from the Host database. Reuse the useful deterministic query/view
behavior from `app.demo` through the smallest reusable boundary; do not reopen
the demo database or build a large query planner. Unsupported questions must
return a clear bounded response rather than invented facts.

Define safe Ask error semantics for invalid questions, provider unavailable
with pending work, processing failure, and state/query failure. If no pending
work exists, existing structured state remains queryable even without Codex. If
pending work cannot be processed, do not pretend state is fresh.

The integrated `/api/state` must use the HostRuntime database for Memory and
Attention. Do not silently seed synthetic data in a new Blackhole Home; keep
explicit seed/reset development behavior if practical. Preserve the approved
PWA's Capture screen, attachment interaction, animation, milestone behavior,
navigation, accessibility, installability, and offline shell. The current
attachment UI supports selection/preview only; do not claim arbitrary binary
attachment persistence, OCR, offline sync, or a large file store.

Serve all PWA assets safely with correct MIME types, prevent traversal, and
keep `/api/` out of the service-worker static cache. Keep the default server
bind at `127.0.0.1`. Add an explicit `--trusted-lan-demo` opt-in for a
non-loopback bind, refuse non-loopback binds without that opt-in, and print a
clear warning that the mode has no device authentication and is only for a
trusted private hackathon network. Do not implement pairing, tokens, mDNS,
TLS, public Internet exposure, tunnels, cloud relay, or remote access.

Add neutral HTTP-level tests using temporary `BLACKHOLE_HOME`, fake providers,
and the real HostRuntime. Cover health, safe status, raw-only capture and
pending state, state before processing, Ask-time processing and query, query
idempotency, provider unavailable with and without pending work, retry, no
secret leakage, static traversal rejection, bind security, and manifest/
service-worker/icon routes. Add UI/PWA static checks. Run one real neutral
Codex smoke if the locally authenticated CLI remains available, without
benchmark entities or expected-output knowledge; record the capture responses,
pending state, safe provider metadata, processing, structured state, query
response, timing, and usage in an authentic runtime trajectory. Optionally
test an unknown November renewal if cheap, without extra unnecessary calls.

Update the frontend API adapter so Capture posts to `/api/capture` and keeps
the current collapse/milestone UX without waiting for the provider. Ask posts
to `/api/query`, shows calm product-language loading while freshness processing
runs, and does not expose implementation terms such as semantic extraction,
Codex reasoning, or reconciliation. Memory and Attention load from the Host
state; offline behavior remains calm and must not fake answers.

Update `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and
`docs/REPRODUCTION.md` to describe App -> Host -> Codex ownership, loopback
default, explicit trusted-LAN demo mode, and absent pairing/auth. Do not claim
Internet-safe remote operation and avoid broad README/UI-document rewrites.

Preserve the UI trajectories, create this coding trajectory, and create an
authentic runtime trajectory for the real smoke if run. This is not Experiment
006. Do not alter benchmark behavior, rerun the baseline, change expected
outputs, start generalization, add Claude/OCR/scheduling, or expose the Host
publicly. Run the full stdlib suite, HTTP/static/PWA tests, generator check,
contract smoke, compileall, deterministic E005 replay, protected hashes, and
`git diff --check`. Commit only on `integration/host-pwa`; leave `master`
unchanged. The final report must include the integration worktree/branch,
base/UI SHAs, merge result, architecture, endpoints, Capture/processing/Ask
evidence, fake and real smoke results, PWA/security results, E005 integrity,
remaining pairing/query limitations, commits, and final integration SHA.
