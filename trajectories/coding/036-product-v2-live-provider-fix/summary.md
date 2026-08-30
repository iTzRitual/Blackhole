# Task summary

## Goal

Investigate the real authenticated Codex provider failure in Product V2 and
make the smallest evidence-backed adapter fix in an isolated worktree.

## Agent/tool used

Codex agent using PowerShell, Git, and repository-local tools. Work is in
`product/v2-provider-fix` at
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-provider-fix`.

## Initial hypothesis

None. The task explicitly requires determining whether the PowerShell
`shell_snapshot` warning is causal instead of assuming it is the exit-code-1
cause.

## Important implementation decisions

The exact source SHA was verified as
`b9478c6a15752b22c0bee8843381c1bf56bebd45`; all implementation was kept in
the isolated `product/v2-provider-fix` worktree. The shell-snapshot warning was
not treated as causal because successful controls emitted it and disabling it
did not remove the schema failure. The adapter now emits a strict typed
structured-output schema, retains terminal JSONL failures and bounded
sanitized tails, and records the invocation boundary without reading provider
credentials or changing global configuration. The final invocation keeps the
normal ChatGPT-authenticated CLI, read-only sandbox, inherited environment, and
default shell-snapshot behavior. A separate deterministic Polish Ask routing
collision found during the live smoke was fixed narrowly and covered by a
regression; it was not provider or benchmark tuning. Image attachments use the
installed `--image` surface, while document/PDF attachments remain explicit
metadata-only limitations without OCR.

## Tools/actions used

- Read the referenced pasted task file before continuing.
- Checked source and main worktree status and source branch presence.
- Created the isolated `product/v2-provider-fix` worktree.
- Created this trajectory before implementation.
- Inspected `codex --version`, `codex exec --help`, `codex features list`, and
  `codex login status`.
- Ran six disposable-directory diagnostic controls, the maximum authorized
  diagnostic model-call budget.
- Implemented and tested the provider schema, terminal-error diagnostics,
  invocation boundary, redaction, image forwarding, and deterministic Ask
  routing correction.
- Ran the normal web-app smoke with exactly two captures and two Ask queries;
  recorded the representative execution in the runtime trajectory.

## Failures encountered

- The original exact adapter schema failed with exit code 1 and a terminal
  `turn.failed` `invalid_request_error` / `invalid_json_schema` HTTP 400.
- An initial combined smoke command was rejected by the command runner before
  execution; the same checks were rerun as separate bounded commands.
- The first live keys Ask was misrouted to an unrelated Attention item because
  the deterministic router treated standalone Polish `do` as a task/time
  marker. The narrow correction passed offline, but the live two-Ask limit
  prevented revalidation.

## Retries or changed approaches

- The warning-first diagnostic was changed to preserve and prefer the terminal
  machine-readable failure, with sanitized bounded diagnostics for later
  inspection.
- The permissive schema was replaced only after controls E/F demonstrated the
  installed contract also required typed array items and strict nested objects.
- No additional live capture or Ask was issued after the live limit was
  reached.

## Human feedback or checkpoints

No additional human feedback or checkpoint has occurred.

## Evaluation performed

Performed:

- Provider diagnostic suite: 6 passing tests.
- Full application suite: 115 passing tests.
- Evaluator suite: 10 passing tests.
- Product acceptance harness: 7 passing tests.
- Integrated Product V2 acceptance: 50/50 PASS.
- Frozen benchmark structure: 200 events and 4 checkpoints verified.
- Contract smoke: PASS, semantic score 1.0, TP 6, FP 0, FN 0.
- Qualification: PASS_WITH_WARNINGS, 0 hard failures and 4 existing warnings.
- `python -m compileall -q app eval product_acceptance scripts`: PASS.
- `node --check app/web/app.js`: PASS.
- Live smoke: both captures processed on the first attempt with no retries;
  Memory and Attention were populated. The task Ask passed; the keys Ask did
  not, before its offline correction.

## Result

The provider adapter repair is evidenced and the deterministic suites pass.
The overall prescribed live gate is PARTIAL because the corrected keys Ask
could not be run live within the authorized two-Ask limit.

## Regressions or unresolved issues

The corrected Polish keys Ask still needs one separately authorized bounded
normal-launch validation. Document/PDF attachments remain metadata-only and
unread/unverified by the provider; OCR was not added. Qualification retains
four pre-existing warnings.

## Final decision

KEEP the provider adapter/schema/diagnostic repair. REVISE the overall live
gate pending the bounded Ask validation described above. This follow-up is not
E006 and did not alter frozen V1 benchmark, baseline, evaluator, calibration,
holdout, or protected-worktree material.

## Related git commit

Recorded after the implementation commit; the exact SHA is included in the
final response and in the final commit history.
