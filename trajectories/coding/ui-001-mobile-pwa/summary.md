# UI/PWA Workstream Summary

## Goal

Implement the Blackhole mobile-first UI/UX and installable PWA in an isolated `ui/mobile-pwa` worktree while preserving the primary backend worktree and all benchmark/evaluator boundaries.

## Agent/tool used

Codex in the Codex desktop app. Work used PowerShell, `apply_patch`, the existing Python local server, direct HTTP checks, and the in-app Browser skill for responsive screenshots and interaction checks. No external service or provider credential was used. No authentic session transcript was exported.

## Initial hypothesis

A calm, capture-first mobile shell with a messaging-style composer, explicit attachment state, quiet milestone feedback, and an installable offline application shell will better express “Capture now. Organize later.” while remaining compatible with the current deterministic demo API.

## Important implementation decisions

- Kept the frontend dependency-free and static under `app/web/`; retained the four destinations Capture, Attention, Memory, and Ask.
- Reduced Capture to a focused mobile composition: small brand mark, breathing room, “What’s on your mind?”, an expanding “Throw anything in…” composer, integrated attachment action, and bottom navigation.
- Added a single API adapter in `app.js` for `/api/state`, `/api/capture`, `/api/query`, and `/api/reset`.
- Kept attachment bytes honest: camera/photo/file selection returns to the composer, previews the selected item, and never submits automatically. The current API receives only the note text plus `source_type`/`filename`; arbitrary bytes are not claimed as persisted. Text-like files may be read into the note for explicit text capture.
- Added fast success motion that contracts toward a small orbit, with a reduced-motion fade path. Save confirmation happens before the animation; failed saves retain the note and attachment.
- Added localStorage-backed milestones at 10, 25, 50, 100, 250, 500, and 1000 local captures. Seeded demo captures do not trigger milestones; no streaks, quotas, XP decay, or missed-day state was added.
- Reframed Attention as a short, calm list and Memory as grouped human-readable cards. Known, inferred, and unknown states remain visible with evidence references; unavailable offline state is not rendered as an empty/zero state.
- Kept Ask separate from Capture with concise structured answers and a future-compatible “Looking through your memory…” pending state.
- Added a standalone portrait manifest, iOS metadata, safe-area-aware layout, original SVG mark plus maskable SVG mark, and a service worker that caches only the static shell and bypasses `/api/` requests.
- Avoided `docs/DECISIONS.md` because the concurrent backend workstream may change it; UI decisions are recorded here for handoff.

## Tools/actions used

- Recorded primary repository root, branch, HEAD, and dirty status without changing it. The primary worktree was `master` at `46b60856e30b44f7898b6d4c723964bf2efed38f`; it contained unrelated backend changes.
- Created `C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-ui` from that exact HEAD on `ui/mobile-pwa` and performed all UI edits/tests/commits there.
- Inspected the existing `app/web/`, `app/web_app.py`, `app/demo.py`, and relevant API behavior before implementation.
- Ran temporary local servers on loopback ports with temporary databases outside the repository. Temporary validation databases were not added to the worktree.
- Captured a 390px preview at `C:\Users\natan\AppData\Local\Temp\blackhole-ui-preview-390.png`.
- Final isolation audit: the primary stayed on `master` and this task issued no writes there, while the concurrent backend work advanced its HEAD from the recorded base to `0c60da9` (`product: add deferred ingestion runtime`). The concurrent commit did not touch `app/web/`; UI integration should be performed by the project owner after review.

## Failures, retries, and changed approaches

- The first combined delete-and-add patch was rejected by the patch tool before changing files. The three frontend files were then replaced through separate safe patches.
- Initial visual review found the hidden SVG symbol sprite occupying a 150px layout block above the header. Added a zero-size positioned sprite rule and versioned the service-worker cache; a fresh origin was used to avoid stale development cache during review.
- One browser locator matched both the brand and bottom-nav Capture buttons. No action occurred; the test was retried with an exact accessible-name locator.
- The browser’s isolated evaluation context did not expose `fetch`/`navigator` for a combined probe. Static manifest/asset checks and an actual offline reload were used instead; no product behavior was changed by the failed probe.

## Human feedback or checkpoints

The human-provided goal required strict sibling-worktree isolation, a static dependency-light PWA, mobile-first Capture, honest attachment behavior, milestone-based relief feedback, accessibility, visual review, and no backend/benchmark changes. No later human checkpoint was provided.

## Evaluation performed

- `node --check app/web/app.js` passed.
- Python AST parse of `app/web_app.py` passed.
- Full existing suite: `python -m unittest discover -s app/tests -p 'test_*.py'` — 42 tests passed.
- Manifest contract and icon-resolution checks passed, including standalone display, portrait orientation, root start URL/scope, theme/background colors, `any` and `maskable` icon purposes, and required metadata.
- Direct local-server checks returned `200` for `/`, `/index.html`, `/styles.css`, `/app.js`, `/manifest.webmanifest`, `/sw.js`, both icon assets, `/api/health`, and `/api/state`. Existing capture/query behavior also passed with a temporary synthetic validation capture.
- Browser review covered 360×800, 390×844, 430×932, and 1280×900. All tested sizes had no horizontal overflow. Capture, Attention, Memory, Ask, attachment menu, file preview, success feedback, and structured Ask output were inspected.
- Offline review stopped the local server, reloaded the cached app shell, confirmed explicit unavailable-state messaging, and confirmed the unsent draft remained in the composer. Browser console error/warning review was empty.

## Result

The mobile-first Blackhole UI/PWA workstream is implemented and compatible with the current local demo API. The primary worktree and protected benchmark/backend files were not edited by this task.

## Regressions or unresolved issues

- Arbitrary camera/photo/file bytes are still not persisted end-to-end because the current backend contract does not accept them. The UI exposes this limitation and still supports normal text capture.
- PWA icons are deliberately simple SVG assets; platform install surfaces that specifically prefer raster home-screen icons may need PNG variants in a later packaging pass.
- The local milestone counter is browser-local until a backend user statistic can replace it; this limitation is intentional and isolated.

## Final decision

KEEP for UI branch handoff and merge review. This is not a benchmark experiment and no benchmark metric or improvement changelog entry was added.

## Related git commit

The final UI branch tip commit is `feat: redesign Blackhole as mobile-first PWA`; its exact SHA is reported in the handoff.
