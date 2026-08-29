# Reference-led Capture Redesign Summary

## Goal

Move the Capture screen substantially closer to the attached premium Blackhole mobile reference while preserving behavior and PWA capabilities.

## Agent/tool used

Codex in the Codex desktop app, with `apply_patch`, the existing local Python server, direct static validation, and in-app browser screenshots/interactions.

## Initial hypothesis

Removing persistent explanatory and progress UI, shifting the brand from mint to restrained violet/blue, and making the composer/navigation the only strong controls will reduce dashboard density and make Capture feel like releasing information rather than managing a system.

## Important implementation decisions

- Kept the existing capture endpoint, immutable-event submission payload, attachment metadata path, other screens, install prompt, and service worker architecture unchanged.
- Reduced the default Capture view to the centered event-horizon brand, a single gradient invitation, the integrated `+ / textarea / up-arrow` composer, empty space, and the four-item bottom navigation.
- Removed persistent capture explanations, keyboard hints, privacy copy, recent-capture history, save-state copy, count/progress strips, and the persistent milestone card.
- Kept connectivity status for screen readers but removed it from visual chrome.
- Converted ordinary success and milestone feedback to the same transient raised toast pattern. Milestones remain local event thresholds and do not appear as persistent progress.
- Made successful submission animate the composer content toward a brief event-horizon effect. The reduced-motion branch remains a short fade.
- Changed the shell cache identifier to `blackhole-shell-v5` and aligned manifest/browser theme colors with the near-black surface.

## Tools/actions used

- Read the attached request and inspected the reference image at original detail.
- Used `apply_patch` for all source and trajectory changes.
- Ran the local Python web app on temporary ports and used the in-app browser at explicit responsive viewports.
- Captured two 390×844 comparison passes and refined the headline wrapping, vertical composition, mark, and no-scroll behavior after pass one.
- Exercised navigation, attachment-menu disclosure, submission, success animation, transient toast, and a server-disconnected offline-shell reload.
- Ran JavaScript/JSON/static checks and the complete existing app test suite.

## Failures encountered

- Reloading the first comparison origin returned service-worker-cached first-pass CSS. A fresh local port was used for the second visual pass so the comparison reflected the edited assets.
- The in-app browser harness timed out waiting for the native file chooser on both the visible File action and the hidden file input. The menu, mode selection wiring, selected-file source path, and existing automated tests were preserved, but native picker selection was not completed through this harness.

## Retries or changed approaches

- Moved the second visual pass to port 8771 after identifying the stale shell cache.
- Retried the file chooser directly through the file input with a caught timeout so the browser session remained stable; after the same limitation, testing continued with the visible menu and source/test validation.

## Human feedback or checkpoints

The user supplied one reference screenshot and an explicit correction brief. No additional checkpoint was requested during implementation.

## Evaluation performed

- Visual pass 1 at 390×844 identified a wrapped, oversized headline and 34 px of default-page overflow.
- Visual pass 2 at 390×844 produced a one-line headline and exact `390×844` document/viewport dimensions with no horizontal or vertical overflow.
- Responsive checks passed at 360×800 and 430×932 with exact document/viewport dimensions and the composer plus bottom navigation visible without scrolling.
- All four primary tabs remained reachable and visible.
- Submission smoke test reached `composer is-collapsing` and `capture-vortex is-active`, then produced `+1 off your mind`.
- A fresh cached tab loaded the Capture shell after the local server was stopped; after startup settled it reported `Offline`, kept the textarea enabled, and produced no browser warning/error logs.
- Visible primary controls measured at least 44×44 CSS px; the responsive stylesheet retains a `prefers-reduced-motion` override.
- `python -m unittest discover -s app/tests -p test_*.py`: 42 tests passed.
- `node --check app/web/app.js`, manifest JSON parsing, `git diff --check`, and HTTP 200/content-type checks for the shell, scripts, manifest, service worker, and icons passed.
- Final screenshot: `C:\Users\natan\AppData\Local\Temp\blackhole-ui-reference-redesign-390.png`.

## Result

The default Capture surface now matches the reference hierarchy and tone substantially more closely while preserving the scoped application behavior and PWA shell. No benchmark or evaluator artifacts were read or changed, and no scored evaluation was run because this was a UI-only correction.

## Regressions or unresolved issues

No known user-facing regression was observed. Native OS file-picker completion remains unverified in the in-app browser harness because its file-chooser event timed out; the visible attachment menu and implementation path remain intact.

## Final decision

KEEP. The correction achieves the requested hierarchy at all three target mobile viewports without changing the benchmark, backend contract, or other application screens beyond shared color/chrome styling.

## Related git commit

`feat: simplify capture around Blackhole interaction` (the commit containing this trajectory).
