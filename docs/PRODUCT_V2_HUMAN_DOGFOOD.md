# Product V2 human-dogfood P0/P1 repair

Status: **PARTIAL**. The deterministic normal-launch regression passes. The
normal `python -m app.web_app` live Codex smoke reached the app and returned
captures immediately, but both authorized live provider attempts failed before
semantic state was produced. No live Ask was issued after those failures, and
no semantic success is claimed.

## Scope and protected boundaries

This work was performed only on the `product/v2-dogfood-fixes` branch, based
on the Product V2 integration commit recorded in the coding trajectory. The
integration worktree, master, the frozen V1 runtime and benchmark, evaluator,
baseline evidence, calibration evidence, other Product V2 worktrees, and
holdout material were not modified or used. No G01–G03 tuning, provider token,
production infrastructure, Claude adapter, or consequential action was added.

The human-dogfood Home was inspected read-only. Its before/after hashes and
the sanitized database observations are recorded in
`trajectories/coding/035-product-v2-human-dogfood-p0-fixes/forensic-evidence.json`.

## Findings and changes

### P0-1 — one Product V2 store and queue

All Product V2 entry points now use the resolved
`<BLACKHOLE_HOME>/blackhole-v2.db` through `product_database_path()`. Host
status opens the Product V2 store before reporting counts, so its queue agrees
with `app.product_process status`. The legacy `<BLACKHOLE_HOME>/blackhole.db`
remains the V1 compatibility store and is not the Product V2 queue.

### P0-2 — actual PWA V2 route and shell update

The shipped client continues to use only `/api/v2/*` for normal Product V2
Capture, state, and Ask. The shell cache is versioned to `v7`; shell asset
URLs are versioned, navigation uses network-first with an offline fallback,
and an installed worker is asked to update with `updateViaCache: "none"`.
Existing controlled clients reload once after `controllerchange` so a stale
legacy shell cannot remain the visible route indefinitely. Dynamic API
responses remain excluded from the service-worker cache.

### P0-3 — normal worker lifecycle

The default `HostServer` starts the managed Product V2 worker during normal
server construction. The worker remains alive for the server lifetime and is
closed with the Host runtime. Test/fixture forms that explicitly disable the
worker remain deterministic and request-scoped.

### P0-4 — provider invocation diagnostics

The installed CLI was verified as `codex-cli 0.150.0-alpha.12.2`, authenticated
through ChatGPT. A safe parser probe showed that the previous
`--ask-for-approval never` flag was rejected by this installation. That flag
was removed. Each Product V2 call now records bounded operational diagnostics:
executable, CLI version, model, reasoning effort, safe invocation flags,
return code, timeout state, duration, and redacted diagnostic stdout/stderr.
Provider failures are retryable and never expose stack traces or credentials to
the product UI.

The live smoke then exposed a separate unresolved CLI exit-code-1 condition.
The exact sanitized persisted failure from the second fresh Home was:

```text
semantic provider failed (exit code 1): 2026-08-30T14:49:50.685864Z  WARN codex_skills::interface: ignoring interface.icon_small: icon path with '..' must resolve under plugin assets/
2026-08-30T14:49:50.685893Z  WARN codex_skills::interface: ignoring interface.icon_large: icon path with '..' must resolve under plugin assets/
2026-08-30T14:49:50.696158Z  WARN codex_core::shell_snapshot: Failed to create shell snapshot for powershell: Shell snapshot not supported yet for PowerShell
2026-08-30T14:49:51.132594Z  WARN codex_skills::interface: ignoring interface.icon_small: icon path with '..' must resolve under plugin assets/
2026-08-30T14:49:51.132630Z  WARN codex_skills::interface: ignoring interface.icon_large: icon path with '..' must resolve under plugin assets/; retry available
```

This is recorded as an operational failure, not a semantic result. Further
live attempts were deliberately stopped at the authorized limit of two
captures.

### P0-5 — bounded automatic retry

Automatic retries use durable delays of 1, 2, 4, and 8 seconds, with five
automatic attempts total. A terminal failed row is not hot-looped; an explicit
retry requeues it. Raw captures remain durable throughout.

### P0-6 — truthful degraded UX

Ask returns typed `processing` or `processing_failed` responses while work is
pending or failed, instead of claiming that no memory exists. Attention and
Memory show an explicit “still understanding” or saved-but-unavailable notice.
Provider details remain outside the user-facing copy.

### P1 — service-worker update behavior

The versioned `v7` shell, update check, waiting-worker message, controlled-page
reload, and network-first navigation path provide a deterministic update route
for installed PWA clients without caching dynamic state.

## Deterministic validation

The added regression uses a fresh Home, normal default `create_server()`
construction, a delayed fake provider, real HTTP V2 Capture/processing/state/
Ask calls, and no manual processing command. It verifies immediate durable
capture, visible processing, automatic completion, evidence-backed Attention
and Memory, typed pending Ask, Host/Product queue agreement, the authoritative
database path, and an empty legacy V1 queue.

The focused Product V2/UI/provider suite passed after the harness cleanup
correction. The full results and command inventory are in the coding summary
and `eval/results/product-v2-human-dogfood-lifecycle.json`. The existing
visible Product V2 integrated acceptance suite was also rerun with its
historical result kept unchanged; it remains a deterministic fixture result,
not live-provider evidence.

## Decision

**KEEP** the deterministic store, lifecycle, retry, provider-diagnostic, typed
UX, and service-worker fixes. **REVISE** the live Codex adapter before calling
the human-dogfood gate PASS: the remaining CLI exit-code-1 condition needs an
explicitly authorized follow-up diagnosis and a new bounded live run.

## Authorized provider-fix follow-up — 2026-08-30

The preceding **PARTIAL** result is preserved as historical evidence. This
follow-up used the exact source HEAD
`b9478c6a15752b22c0bee8843381c1bf56bebd45` and the isolated
`product/v2-provider-fix` branch. The sanitized control matrix and invocation
record are in
`trajectories/coding/036-product-v2-live-provider-fix/provider-diagnostics.json`.

### Actual provider root cause

The fatal condition was not the PowerShell shell-snapshot warning. The Product
V2 adapter's output schema was incompatible with the installed Codex
structured-output contract: its root object allowed additional properties,
its arrays did not declare `items`, and its nested objects were not strict.
Codex emitted a terminal `turn.failed` event containing
`invalid_request_error` / `invalid_json_schema` with status 400 and exited with
code 1 before generating a model message. The earlier bounded diagnostic chose
stderr warning lines first, which obscured that terminal error.

Controls A and B completed with `OK` while emitting the shell-snapshot warning.
Control D added `--disable shell_snapshot`; the warning disappeared, but the
same schema failure and exit code 1 remained. The final adapter therefore does
not disable shell snapshots merely to silence the warning.

The adapter now generates a strict schema with typed array items, closed object
properties, required fields, and nullable representations for optional semantic
values. It also preserves the terminal JSON failure event, a bounded sanitized
stdout/stderr tail, return code, and timeout state. Non-zero exits remain
retryable failures.

### Final invocation boundary

The final Product V2 call shape is:

```text
codex exec --ephemeral --json --model gpt-5.6-luna
  -c model_reasoning_effort=high
  -s read-only --ignore-rules --skip-git-repo-check
  -C <temporary-isolated-workspace>
  --add-dir <BLACKHOLE_HOME>
  --output-schema <temporary-strict-schema>
  [-i <stored-image>]
  -o <temporary-last-message-file> -
```

The subprocess inherits the environment without modification, sends UTF-8
prompt bytes through a pipe, and uses the normal externally authenticated
Codex configuration. It does not use `--ignore-user-config`,
`--disable shell_snapshot`, or any workspace-write/dangerous sandbox flag.
There is no explicit approval flag; the sandbox is read-only. The default
timeout is 900 seconds. The exact resolved executable path, version, argv
placeholders, and all boundary fields are recorded in the sanitized diagnostic
artifact.

The installed CLI exposes local image support through `--image`; the adapter
forwards image attachments through that flag and leaves document/PDF
attachments as explicit metadata-only records. No OCR or unverified document
interpretation was added, so this limitation remains visible rather than being
presented as a successful read.

### Follow-up live smoke

`python -m app.host init` succeeded in a fresh temporary Home and reported the
normal ChatGPT login. The normal `python -m app.web_app` launch accepted both
authorized captures immediately: approximately 33.0 ms and 9.2 ms, each with
`processing: pending`. The managed worker then processed both on their first
attempt, with 2 processed, 0 pending, 0 processing, 0 failed, and zero retries.

Memory contained the known fact `Klucze do piwnicy / location / u mamy` with
source reference `provider-smoke-basement`. Attention contained the open
appointment `Odebrać dzieci`, due ten minutes after capture, with source
reference `provider-smoke-kids`.

The second prescribed Ask returned the useful children Attention item with
evidence. The first prescribed Ask, `Gdzie są klucze do piwnicy?`, was instead
routed to the unrelated Attention item by an existing deterministic Polish
router rule that treated the standalone preposition `do` as a task/time
marker. This is recorded as an unrelated product-routing issue; no semantic
router change is retained in this provider-only branch, and no additional live
Ask was made because the authorized two-Ask limit had been reached.

### Follow-up decision

The real provider adapter repair is **KEEP as a provider-boundary change**: the
authenticated normal worker now produces useful semantic Memory and Attention
state without retries. The overall prescribed live provider gate remains
**PARTIAL / REVISE** because the first live Ask was not useful; fixing that
unrelated router issue requires separate product-scope authorization and a
fresh bounded validation. No benchmark, baseline,
holdout, V1 oracle, G01/G02/G03 run, global Codex configuration, or protected
worktree was changed or accessed.

## Authorized Product V2 Ask-routing follow-up — 2026-08-30

The preceding provider-fix **PARTIAL** result remains preserved above. This
separate post-freeze product task used the exact base
`33185aaefac93882e898e9d47e7d9405daab7b84` in the isolated
`product/v2-ask-fix` worktree. The provider-fix source worktree and provider
adapter were left unchanged.

### Failure and general repair

The live failure was deterministic routing, not semantic extraction: the
Polish preposition `do` appeared as a standalone token in
`Gdzie są klucze do piwnicy?`, and the old Ask path treated it as a task/time
cue before using the matching Memory. That sent the question to unrelated
children-pickup Attention.

The repair adds a small language-aware Ask planner and plan-aware retrieval
boundary. Whole-word, accent-folded terms and conservative English/Polish
aliases support ordinary open-world questions without routing on short
substrings. Current facts are ranked first; history and relations are added
only when relevant or explicitly requested. Same-entity facts, tied
multi-object candidates, location-list observations, ambiguity, corrections,
retractions, and unknown values remain source-linked. High-confidence
Attention, cost, change, and last-mention paths remain deterministic; future
recommendation questions stay on generic Memory rather than becoming false
change history. Bounded synthesis receives only the selected context. Empty
processed state is `no_data`; processed state without a match is `no_match`;
pending and failed processing remain typed states.

### Reproducible validation

The dedicated suite contains 37 multilingual routing cases, mocked HTTP
end-to-end coverage, provider-context isolation checks, and distinct no-data,
no-match, unknown, and retraction assertions. The final application suite
passed 119 tests; evaluator tests passed 10; acceptance-harness tests passed 7;
compileall, JavaScript syntax, the 200-event/4-checkpoint benchmark structure
check, and the non-scored contract smoke passed. The visible integrated
acceptance rerun was 50/50 PASS with all seven reliability gates and its
latency probe PASS. Its historical result file was not rewritten.

The detailed machine-readable result is
`eval/results/product-v2-ask-routing.json`. The coding trajectory is
`trajectories/coding/037-product-v2-ask-routing/`, including the live record.

### Fresh live smoke

The authorized fresh temporary `BLACKHOLE_HOME` was initialized through the
normal Host CLI and served by the normal loopback `app.web_app` entry point.
Exactly four captures were submitted. All four returned `Saved.` with pending
status and then processed on attempt 1: 4 processed, 0 pending, 0 processing,
0 failed, and 0 retries. Exactly the six authorized Ask questions were then
submitted without changing the implementation. All six returned `ready` with
source references and no Ask-time provider call:

- `Gdzie są klucze do piwnicy?` and `Where are the basement keys?` returned the
  basement-key Memory from `live-keys`.
- `Co wiem o Kubie?` and `What do I know about Kuba?` returned Kuba's green
  pasta preference from `live-kuba`.
- `Co mówiłem o samochodzie?` returned the front-left knocking note from
  `live-car`.
- `Co mam niedługo do zrobienia?` returned the open children-pickup Attention
  item from `live-children`.

### Gate decision

**PASS / KEEP** for the explicitly authorized Product V2 Ask-routing scope.
This is post-freeze product evidence, not a benchmark optimization, not E006,
and not a new LQA/DSCR result. No V1 oracle/scoring worktree, holdout
material, G01/G02/G03 result, official baseline, or provider token was used.

## Final human dogfood repair — 2026-08-30

This final, bounded P0/P1 repair keeps the established Product V2 semantic
and persistence boundaries while tightening the path from capture to useful
state. The Product V2 provider uses the compact versioned instruction and
bounded structured prior memory; the installed Codex CLI was inspected with
`codex exec --help` and `codex features list`, and no unsupported fast or
priority flag was introduced. The bounded effort comparison made three
ordinary five-case extraction calls: high `48.859s`, medium `43.391s`, and
low `31.640s`. All parsed successfully and preserved simple facts, a
relative ten-minute action, uncertainty, correction, cross-language meaning,
and capture-time temporal normalization. Low was selected as the lowest-cost
effort preserving those checks. The conservative runtime batch size is `2`.

The browser repair makes Attention time and overdue state explicit, keeps
disclosure state by stable IDs, shows contextual history under its entity,
renders Ask as a compact conversation with collapsible supporting memories,
and guards all display fields against object or empty-value artifacts. Chrome
labels and generated presentation remain English, while raw evidence and
questions remain in their captured/current languages. The Capture composer is
centered and the active navigation underline is removed.

The final fresh-home live smoke used exactly six captures and four Ask
requests through the normal lifecycle. All six capture requests returned
HTTP 200 and were saved/processed without failure; observed polling reached a
usable state at `23.031s` for the first capture and `129.562s` for the
remaining burst. Capture #3's due timestamp was exactly ten minutes from its
persisted capture timestamp, including timezone. All four Ask requests were
HTTP 200, deterministic/provider-free, and completed in `15–16ms`. The live
run did not persist raw inputs, prompts, questions, provider output, or
credentials. The launcher shutdown stream did not capture final stop lines;
deterministic clean-stop coverage remains passing.

The two required viewport reviews were completed at 390×844 and 1280×900.
They verified Capture alignment/no underline, Attention time/overdue,
persistent disclosure state and chevrons, contextual Memory history, Ask
examples/chat/supporting-memory behavior, and artifact-free rendering. The
allowed screenshots are recorded at
`trajectories/coding/042-product-v2-final-human-dogfood-fixes/`.

Overall gate: **PARTIAL / REVISE**. The semantic and UI repairs are kept, but
the observed burst processing interval does not demonstrate the required
material end-to-end latency improvement, and the live launcher stream lacks
complete shutdown evidence. This is product evidence only; frozen benchmark,
baseline, evaluator, calibration, holdout, V1 oracle, and protected
worktrees remain outside scope.

## Fix-first review correction — 2026-08-31

The fresh review identified four narrow follow-ups, all completed without a
provider call or a change to the live measurements. Extraction context remains
bounded, but rows are now ranked by deterministic term relevance to the
captures being linked and then by sequence/capture time with canonical stable
tie-breaking. An over-limit correction test proves that an older matching
entity/current fact remains available and that rebuild preserves current and
historical truth.

Default human-readable learned summaries remain enabled as required for local
dogfooding. They now guard concept/key/value fields: private credential-like
concepts, access codes, generic notes/captures, nested payloads, long opaque
strings, and raw-like echoes become non-content placeholders, while benign
scalar location and cost summaries remain useful. Direct human-log sanitizing
also redacts labeled private values.

The UI contract tests now execute the production normalization/time helpers,
structured related-memory handling, contextual history filtering, disclosure
state restore, and Ask example visibility through an opt-in dependency-free
Node hook rather than relying on source-string assertions. Every versioned
shell reference in the HTML and service worker is aligned to `v8`, including
the manifest and Apple touch icon.

The correction focused suite is `105/105`; the full application suite is
rerun separately below. The overall live gate remains **PARTIAL / REVISE**:
the prior bounded smoke values are unchanged and no new provider/live smoke
was authorized.

## Configuration-boundary correction — 2026-08-31

A follow-up review found that the final Product V2 low-effort/two-item tuning
had been placed in shared runtime defaults. The correction restores the
legacy/frozen Host boundary to high reasoning and batch size ten, keeps its
max/high/medium supported-effort set, and adds independent Product V2
reasoning/batch fields with low/two defaults. Fresh Homes persist both sets;
older config JSON without the new fields retains its legacy values in memory
while Product V2 receives low/two. Host status and the legacy engine use the
legacy fields, while Product V2 lazy readiness, queue processing, and direct
runtime/provider defaults use the Product V2 fields. The config version and
legacy field names remain unchanged.

The historical first review correction remains recorded as `105/105` focused
Product V2/UI tests and `172/172` full application tests. The parent’s
post-correction provider-free acceptance remains `50/50`, with its latency
probe at `7.066 ms` capture return and `136.504 ms` processing completion.
Those historical values were not rewritten. This correction made no provider
or live calls. The new focused final-dogfood/PWA run is `16/16` in `2.002s`
wall time; the combined focused Product V2/config/UI regression is `120/120`
in `22.358s`, the full application suite is `176/176` in `26.528s`, the
acceptance harness is `7/7` in `0.428s`, and the evaluator suite is `10/10`
in `2.430s`. The provider-free integrated acceptance remains `50/50`, with
this run's fixture latency probe at `7.320 ms` capture return and `137.041 ms`
processing completion. The complete command/evidence record is in the
trajectory summary and machine-readable files.

The overall live gate remains **PARTIAL / REVISE**. The prior live first-use
value (`23.031s`), remaining burst (`129.562s`), and incomplete Windows
shutdown evidence remain unchanged.

## Final relative-day temporal correctness hotfix — 2026-08-31

The final Mac human dogfood after the Ask/Memory/UI hotfix exposed one narrow
temporal correctness failure. With a capture timestamp of
`2026-08-31T10:00:00+02:00` in `Europe/Warsaw`, the deterministic occurrence
Ask path reported a two-unit “yesterday” occurrence on Aug 29 instead of Aug
30. The observable trace was `mode=occurrence_totals`, `provider_used=false`,
so this was not a provider-latency or live-model failure. The provider shape
could include raw `expression: "yesterday"` together with an inconsistent
absolute `normalized: "2026-08-29"`.

The fix is at the generic temporal normalization boundary. English and Polish
today/yesterday/tomorrow forms, including the existing compact provider
temporal shapes, resolve from the capture-local calendar date; raw relative
expression evidence wins over an inconsistent absolute proposal. Occurrence
projections retain the capture timezone and the deterministic renderer compares
dates in that timezone. Local calendar arithmetic also covers the
Europe/Warsaw ZoneInfo DST boundary without subtracting a fixed UTC 24 hours.

The focused temporal reproduction is `12/12`; the targeted Product V2 suite
is `47/47`; the application suite is `200/200`; the evaluator is `10/10`; the
acceptance harness is `7/7`; the root suite is `217/217`; and integrated
Product V2 acceptance is `50/50 PASS` with all seven quality gates passing.
No live provider call was made. The machine-readable acceptance evidence is
`eval/results/product-v2-integrated-acceptance.json`, and the full coding
record is in
`trajectories/coding/047-relative-day-temporal-hotfix/summary.md`.
