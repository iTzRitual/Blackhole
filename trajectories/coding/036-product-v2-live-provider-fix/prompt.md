# Human task instruction

Source: `C:\Users\natan\.codex\attachments\5e1d6c7a-be69-462d-9feb-b8daca478b67\pasted-text-1.txt`, which was read before work began.

The requested task is **BLACKHOLE PRODUCT V2 — REAL CODEX PROVIDER ADAPTER FIX**.
It is a narrow, post-dogfood provider-integration task. The deterministic Product
V2 lifecycle fixes are complete; this task must investigate and repair the real
authenticated Codex provider path without changing the frozen benchmark or
protected worktrees.

Use source worktree
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-dogfood-fixes`, branch
`product/v2-dogfood-fixes`. Resolve its exact `HEAD` with `git rev-parse HEAD`
and require that it begins with `b9478c6`. Create and use only the isolated
worktree
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-provider-fix` on
branch `product/v2-provider-fix`, based exactly on that resolved SHA. Do not
modify the source, integration, runtime, UI, dogfood, or main Blackhole
worktrees, and do not access V1 oracle/scoring worktrees.

The prior live smoke produced two immediate captures but semantic processing
exited with code 1. Investigate the complete sanitized output and identify the
actual fatal cause. Do not assume that the Windows PowerShell
`shell_snapshot` warning is causal, suppress stderr, or convert a non-zero exit
to success.

Required work:

1. Inspect the actual Product V2 provider adapter and record a sanitized exact
   invocation boundary: executable path, argv, cwd, stdin behavior, environment
   changes, model, reasoning effort, sandbox, approval mode, config/feature
   flags, output mode, and timeout. Never record credentials.
2. Inspect `codex exec --help` and `codex features list`, then run a small
   disposable-directory control matrix with at most six live diagnostic model
   calls. Establish the simplest authenticated exec, the adapter settings, the
   exact adapter flags with a trivial prompt, and—only if supported—an explicit
   shell-snapshot-disabled variant. Do not process Blackhole captures or run
   benchmark prompts. Test authentication behavior explicitly if
   `--ignore-user-config` is involved; never extract or persist tokens.
3. For non-zero exits, retain the return code, terminal machine-readable error
   where available, sanitized stderr tail, and timeout status. Distinguish an
   incidental warning from the terminal failure.
4. Once trivial execution works, verify the exact Product V2 semantic request,
   schema parsing, and the existing attachment path. Text-only provider success
   is required; unsupported arbitrary-file formats may remain documented.
5. Implement the smallest evidence-backed adapter/configuration change. Do not
   downgrade or reinstall Codex, modify global Codex configuration, silently
   switch models, or weaken semantic validation.
6. Add deterministic adapter tests for Windows argv construction, relevant
   shell-snapshot/auth flags, exit handling, warning-vs-fatal behavior, JSON
   terminal failures, successful structured output, and sanitized diagnostics.
   No live provider calls in CI.
7. After deterministic tests pass, run the normal human launch only with a fresh
   temporary `BLACKHOLE_HOME`: `python -m app.host init` and
   `python -m app.web_app --host 127.0.0.1 --port <free-port>`. Use at most two
   captures (the basement-key sentence and the children sentence), then at most
   two Ask queries. PASS requires immediate capture responses, pending events,
   useful semantic state in Memory and Attention, useful evidence-grounded Ask
   responses, and no retry spin. Do not run G01/G02/G03 or tune semantics from
   wording.
8. Run the required provider, Product V2 runtime/UI/HTTP, 50-case acceptance,
   V1 historical, compileall, qualification, and benchmark-structure checks
   without weakening expectations.

Create/update the trajectory files, `docs/PRODUCT_V2_HUMAN_DOGFOOD.md`, and
the sanitized `provider-diagnostics.json`; preserve the previous PARTIAL result
as history. Commit only on `product/v2-provider-fix`. The final report must
state PASS/PARTIAL/FAIL, exact base and final SHAs, Codex version/path, actual
fatal root cause, shell-snapshot causality, final argv shape, auth behavior,
model/reasoning, smoke results, retry count, acceptance and test counts,
limitations, and explicit confirmations that no global config changed, no
reinstall/downgrade occurred, protected worktrees and V1 oracle were untouched,
and no G01/G02/G03 tuning occurred. KEEP only if the normal human launch works
with the real authenticated Codex CLI.
