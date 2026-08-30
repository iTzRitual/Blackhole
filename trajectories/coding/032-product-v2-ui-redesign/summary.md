# Product V2 UI redesign trajectory

## Goal

Implement the mobile-first Product V2 frontend redesign in the product/v2-ui worktree, without changing runtime/backend or frozen V1 benchmark behavior.

## Agent/tool used

Codex desktop agent with PowerShell, apply_patch, deterministic local tests, and local browser/manual visual checks where available.

## Initial hypothesis

A single calm product shell, a narrow frontend adapter, human-oriented presentation models, and a deterministic fixture mode can address the current benchmark-debugger feel while keeping the V2 UI independent from the concurrent runtime branch.

## Important implementation decisions

- Replaced the debugger-like V1 web surface with a mobile-first, dark near-black product shell organized around Capture, Attention, Memory, and Ask.
- Kept Capture intentionally minimal: a compact full pill composer, simple plus attachment control, growing textarea, Enter-to-save / Shift+Enter newline behavior, attachment previews, attachment-only fixture saves, success collapse, an ephemeral `+1 off your mind` toast, and an explicit Undo path.
- Added a thin frontend adapter for `getState`, `capture`, `retractCapture`, and `ask`. The adapter normalizes legacy assertion-shaped responses at the boundary into human summaries, evidence details, and open-world entity/topic/group cards.
- Added deterministic fixture modes for populated, empty, and provider-unavailable UI states. Fixtures are UI-only and are not benchmark data.
- Preserved unknown status as a humanized uncertainty state, kept evidence/provenance behind details, made Attention badge visibility count-gated, and avoided raw ontology/assertion fields in primary markup.
- Added `docs/PRODUCT_V2_UI_CONTRACT.md` and decision D-036 to document the expected future Host attachment/retraction contract and the current text-first compatibility limitation. Bumped the shell cache name to v6 and updated the PWA metadata.

## Tools/actions used

- Read the supplied pasted brief and the relevant product, architecture, decision, README, query-service, and agent-guidance documents.
- Created the requested isolated worktree from base `68b7b15d353b12cffb65a770f8583aa0ebb849dd` on `product/v2-ui`; the runtime worktree was not used.
- Used `apply_patch` for all repository edits; used PowerShell for read-only inspection, syntax checks, tests, status, and diff validation.
- Used the in-app browser with local static fixture servers for mobile and desktop visual checks, including attachment menu, file and image previews, removal/replacement, attachment-only save, success/Undo, Attention populated/empty, Memory filters/cards, Ask answer/no-match/provider-unavailable, and responsive layout.

## Failures encountered

- The first local visual origin retained an older service-worker shell and showed stale UI/duplicate Memory structure. A second fresh origin was used for verification, and the application shell cache version was bumped.
- The browser accessibility snapshot initially exposed the hidden file picker as an extra unlabeled control. The input was made explicitly hidden and the duplicate attachment-menu label was removed; the picker still worked through the user-triggered menu.

## Retries or changed approaches

- Re-ran visual checks on the fresh origin after the normalization and hidden-picker fixes rather than treating cached output as current.
- Added a robust Attention adapter branch for both array-shaped and `{items: [...]}` state responses after reviewing the current Host response shape.

## Human feedback or checkpoints

No additional human checkpoint was provided during implementation.

## Evaluation performed

- `node --check app/web/app.js` passed.
- `python -m unittest app.tests.test_pwa_static app.tests.test_web_v2_ui -v` passed: 12 tests.
- `python -m unittest discover -s app/tests -p "test_*.py" -v` passed: 84 tests, including the unchanged backend/runtime and Host test suite.
- `git diff --check` passed after the final CSS cleanup.
- Manual visual checks passed on 390x844 mobile and 1280x900 desktop fixture views. Reduced-motion behavior was covered by deterministic source tests and explicit CSS/JS handling; a system-level reduced-motion emulation was not available in the browser check.

## Result

Product V2 UI is implemented in the isolated frontend worktree. Capture is sparse and human, attachments are visual and non-destructive, Attention answers what needs action, Memory is open-world and human-readable, Ask leads with a natural answer and has distinct loading/error/no-match states, and the shell is responsive/PWA-compatible.

## Regressions or unresolved issues

- The current Host API still requires text for capture, accepts only attachment metadata rather than binary content, and has no `/api/capture/retract` route. Real attachment-only capture and real Undo therefore remain integration work; fixture mode exercises the complete UI contract and the live path reports the limitation truthfully.
- No benchmark score, benchmark content, evaluator, provider integration, runtime/backend implementation, or frozen V1 artifact was changed. This task has no benchmark metric by design.

## Final decision

KEEP for the explicitly authorized, isolated post-evaluation Product V2 UI scope. Do not merge it into the frozen runtime boundary without the separately documented Host capability work and human authorization.

## Related git commit

To be recorded after the final coherent commit.
