# Frozen Blackhole Runtime Adversarial Engineering Audit

## Executive summary

This read-only pre-submission audit reviewed the frozen runtime at commit
`8d3b4ff7a1979540f2e65dd9b493f0731e006f72`, the commit peeled from the
annotated `implementation-freeze-v1` tag. The audit ran in
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-audit` on branch
`audit/frozen-runtime-v1`. The primary `master` worktree was not modified.

The frozen public development response contract and query bundle were reviewed.
No generalization path, generalization worktree content, holdout content, or
expected output outside historically present public development evidence was
opened. No model inference, provider call, baseline execution, scoring run, or
metric optimization was performed.

The core architectural claims are partly strong and partly overstated. Raw
capture is genuinely provider-free and immutable at the SQLite application
boundary. Consequential external actions are not implemented. Runtime code
contains no DEV entity, brand, event, or scenario identifiers and does not
import expected outputs or the evaluator. The deterministic test suite passes
85/85.

However, ten confirmed P1 findings should be addressed before a final video or
submission. The most important are: crash-claimed rows can remain permanently
`processing`; semantic processing is not transactionally atomic and a retry can
double-count one capture; a failure barrier does not survive the next processing
request; Ask can return HTTP 200 with stale state after failures; and the
loopback API accepts cross-origin writes and arbitrary Host headers while a GET
query can trigger provider work. Provider calls also omit Codex CLI's
`--ephemeral` and `--ignore-user-config` controls, so private capture/session
artifacts may be retained by the CLI and runtime behavior is machine-dependent.

There is no P0 finding that invalidates the frozen public benchmark result or
requires opening the generalization oracle with knowledge of new answers. The
frozen reference should remain intact through the separately scoped
generalization run. The product/runtime should be revised on a subsequent
authorized hardening branch before submission.

### Severity totals

| Severity | Count |
| --- | ---: |
| P0 | 0 |
| P1 | 10 |
| P2 | 4 |
| P3 | 1 |

## Submission blockers

There are no P0 submission/evaluation invalidators. The following P1 issues are
pre-submission blockers for unqualified product claims:

1. Automatic recovery from an interrupted `processing` claim does not exist.
2. A partially committed semantic attempt can survive failure and be counted
   again after retry.
3. Chronological failure ordering is enforced only within one call, not across
   calls.
4. Ask can present stale state as an ordinary successful answer after a failed
   or stuck event.
5. Loopback HTTP lacks Origin/Host/CSRF defenses and exposes side-effecting GET
   behavior.
6. Codex CLI semantic calls are not ephemeral and do not isolate user config.
7. Camera/photo/file UI implies more persistence than the backend provides.
8. Trusted-LAN HTTP cannot deliver the advertised service-worker PWA behavior
   on another device.
9. The top-level quickstart and older reproduction section target an obsolete
   seeded demo/database and removed routes.
10. Exact semantic derived state cannot be reconstructed from the durable
    product database alone.

These are not reasons to mutate the frozen benchmark or rerun it. They are
reasons to qualify the demo and schedule post-generalization runtime hardening
before final submission.

## Confirmed strengths

- **Capture is provider-free.** The exact HTTP call graph is
  `POST /api/capture` (`app/web_app.py:273-307`) → `HostRuntime.capture()`
  (`app/host.py:267-271`) → `IngestionEngine.capture()`
  (`app/ingestion_engine.py:188-239`) → `StateStore.insert_raw_events()`
  (`app/state_store.py:185-238`). It creates the raw row and derived pending row,
  then returns. Provider discovery, provider construction, semantic extraction,
  completeness, relation recovery, and projection rebuild are unreachable.
  Runtime construction itself performs no discovery. A capture exception can
  prevent `Saved.`, but no hidden exception path invokes a provider.
- **Raw events are protected.** `raw_events` has aborting update/delete triggers,
  payload hashes, unique event IDs and sequences, and conflict detection for
  replayed IDs. Corrections remain new observations/events.
- **Unknown is represented explicitly.** Storage and normalization require one
  of `known`, `inferred`, or `unknown`; unknown values omit `value` and retain a
  reason. Contradictions project to unknown until resolved.
- **Consequential actions are proposal-only.** There is no send/pay/cancel/sign/
  delete executor, generic shell endpoint, remote-action adapter, scheduler, or
  arbitrary command API. The only subprocess surface is the fixed Codex CLI
  semantic-provider command, passed as an argument list with `shell=False`.
- **Credential handling is narrow.** Runtime config rejects secret-like keys,
  discovery uses only PATH, `codex --version`, and `codex login status`, and Host
  errors redact provider text. No code reads or copies auth files or tokens.
- **Static and cache boundaries are good.** Static paths are decoded, reject
  traversal and backslashes, resolved under the fixed web root, and restricted
  to allowed suffixes. Every HTTP response is `Cache-Control: no-store`; the
  service worker caches only listed shell assets and bypasses `/api/`.
- **PWA local data is narrow.** Local storage contains only a local capture count
  and celebrated milestone numbers. Draft text, answers, state, filenames, and
  binary contents are not written to localStorage or IndexedDB. Image preview
  object URLs are process-memory-only and revoked when cleared.
- **Benchmark answer coupling was not found.** Product/runtime files contain no
  `Streamly`, `Orange Mobile`, `MarketOne`, `RoadSure`, `GymFlex`, `HomeFix`,
  `blackhole-dev-001`, `evt-191`, scenario-specific IDs, expected-output import,
  or evaluator import. Named occurrences are confined to the public DEV
  contract/query bundle, tests, benchmark harness defaults, and historical
  documentation.
- **Evaluation isolation is credible.** The baseline receives the same public
  chronological captures, maintains one canonical chat, forks each checkpoint
  query atomically, and never resumes a query fork. It imports neither expected
  output nor scorer. The advanced runner receives public scenario/contract/query
  inputs and deterministic replay artifacts, not expected answers. The scorer
  alone reads expected output after candidate production.

## Findings table

| ID | Severity | Status | Finding | Disposition |
| --- | --- | --- | --- | --- |
| F-01 | P1 | CONFIRMED | Interrupted claims remain `processing` indefinitely | Fix before submission |
| F-02 | P1 | CONFIRMED | Multi-commit semantic attempt can double-count after retry | Fix before submission |
| F-03 | P1 | CONFIRMED | Later pending events bypass an earlier failed event on the next call | Fix before submission |
| F-04 | P1 | CONFIRMED | Ask returns stale HTTP 200 when failed/processing rows remain but pending is zero | Fix before submission |
| F-05 | P1 | CONFIRMED | Loopback/LAN API accepts cross-origin writes, arbitrary Host, and side-effecting GET Ask | Fix before submission |
| F-06 | P1 | CONFIRMED | Codex calls persist sessions and load user config by default | Fix or disclose before submission |
| F-07 | P1 | CONFIRMED | Attachment preview plus `Saved.` is misleading about binary persistence | Fix copy/flow before video |
| F-08 | P1 | CONFIRMED | Plain-HTTP trusted-LAN mode is not an installable/service-worker PWA on another device | Fix claim or transport before video |
| F-09 | P1 | CONFIRMED | README and reproduction quickstart seed an unused database and document removed behavior | Fix before judge reproduction |
| F-10 | P1 | CONFIRMED | Semantic derived state is not exactly reconstructible from durable product evidence | Narrow claim or add replay evidence |
| F-11 | P2 | CONFIRMED | Query routing and ontology support are bounded domain heuristics | Honest prototype limitation |
| F-12 | P2 | CONFIRMED | Product provider imports command helpers from benchmark baseline code | Decouple after generalization |
| F-13 | P2 | CONFIRMED | Corrupt config has no recovery path and health can stay green | Add startup validation/recovery |
| F-14 | P2 | CONFIRMED | Python, Codex CLI, and model capability assumptions are not pinned | Document/pin environment |
| F-15 | P3 | CONFIRMED | Escaped unpaired Unicode reaches a generic 500 rather than validation error | Harden input validation |

## Detailed findings

### F-01 — crash-claimed rows never recover

`claim_processing()` commits the transition to `processing` before the provider
call (`app/state_store.py:327-353`). Normal processing and retry select only
`pending` or `failed`; neither startup nor `ensure_state_fresh()` reclaims stale
`processing` rows. A temporary-database probe claimed one row, closed the
process, reopened it, and observed:

```text
status=processing
ensure_state_fresh: processed=0, processing_count=1, fresh=false
provider calls=0
```

There is no public operation capable of moving the row to failed or pending.
Severity is P1 because a crash or forced stop in the long provider window can
permanently strand private evidence and silently block freshness after restart.

### F-02 — partial commits can double-count one capture

One semantic batch is not a transaction. Claim, observations, relationships,
reconciliation replacement, projection rebuild, completeness, a possible
second rebuild, and final status each commit independently
(`app/state_store.py:353,470,517,549,1029` and
`app/ingestion_engine.py:332-421`). The exception handler marks the entire
claimed batch failed but does not roll back already committed derived rows.

A deterministic probe injected an exception immediately after the observation
commit. Retry returned a different, equally valid semantic value for the same
capture. Both observations remained in history. Merchant consumption projection
then reported quantity `3` and observation count `2` from one capture whose two
attempt values were `1` and `2`. This is a confirmed double-count path and a
direct violation of idempotent/rebuildable derived-state expectations.

`replace_relationships_for_sources()` has the same atomicity smell: it commits
the delete before inserting replacements (`app/state_store.py:520-550`).

### F-03 — chronological failure barrier is request-local

`process_pending()` reads only pending rows (`app/ingestion_engine.py:521-542`).
It stops after a failed batch in that call, but a later call selects the later
pending rows without checking for an earlier failed or processing row. A
three-event, batch-size-one probe produced:

```text
first call:  e1=processed, e2=failed, e3=pending
second call: e1=processed, e2=failed, e3=processed
provider call order: e1, e2, e3
```

Retrying e2 later can also receive non-prefix context. `extraction_context()`
applies `max_sequence` only to `event_index`, while returning all current facts
and relationships (`app/state_store.py:1163-1180`). Once e3 is processed, an e2
retry can therefore see future derived state. This weakens chronological
semantics and can produce order-dependent reconciliation.

### F-04 — Ask can present stale state as successful

The HTTP query handler rejects stale state only when `before_pending > 0` and
freshness is false (`app/web_app.py:195-218`). Once a failed attempt converts
the last pending row to `failed`, or a crash leaves only `processing`, the next
Ask has `before_pending == 0`; it returns HTTP 200 and a normal answer even
though `fresh` is false. The PWA ignores the response's processing object and
renders the answer.

The existing test explicitly locks in the failed-event behavior: first Ask is
409, second Ask is 200. That supports the documented ability to query existing
state but contradicts the stronger claim that the client does not present stale
state as fresh. A successful answer needs an explicit stale/degraded contract,
or failed/processing rows must block it consistently.

### F-05 — loopback HTTP lacks browser-origin defenses

The server validates bind address and serializes domain work, but it does not
validate `Origin`, `Referer`, `Host`, or request `Content-Type`, and it emits no
CSRF token. A temporary server accepted a POST to `/api/capture` with
`Origin: https://attacker.example` and `Content-Type: text/plain`, returning 200
and creating a pending row. That is a browser "simple request" shape, so the
absence of CORS response headers prevents response reading but does not prevent
the write.

The compatibility `GET /api/query` then processed the injected pending capture
through a fake provider. A separate probe sent `Host: attacker.example` and
received `/api/state` with HTTP 200. The latter is the server-side prerequisite
for DNS-rebinding attacks against loopback services. On trusted LAN the same
unauthenticated read/write/provider surface is directly reachable by every host
that can connect.

Default loopback binding is a real strength, but not a complete browser
security boundary. GET should be side-effect-free, and state-changing/provider
routes need origin/host validation or an explicit local authorization token.

### F-06 — provider sessions are not ephemeral or configuration-isolated

`app/provider.py` imports `base_command()` and `run_cli()` from the baseline
runner. The command uses a fixed argument list, read-only sandbox, empty
temporary workspace, model, and reasoning effort, which prevents shell
injection. It does not pass `--ephemeral` or `--ignore-user-config`
(`baseline/run_baseline.py:225-240`).

The installed `codex exec --help` states that `--ephemeral` runs without
persisting session files to disk and `--ignore-user-config` avoids loading
`$CODEX_HOME/config.toml` while retaining auth. The frozen provider supplies
neither. Blackhole therefore causes a CLI session containing private raw
captures and extracted state to be persisted outside its temporary directory,
and user-specific config can affect behavior. Deleting the temporary workspace
does not establish the documented privacy/reproducibility boundary.

No credentials are read or copied by Blackhole, stderr is safely bounded at the
Host boundary, and no shell injection exists. The finding concerns private
session data and machine-dependent behavior, not token theft.

### F-07 — attachment flow implies binary persistence

Camera and Photo show the selected image via an object-URL thumbnail; File
shows filename and size. The submit flow requires a note, then sends only the
note, source type, and filename (`app/web/app.js:273-304,373-401`). The server
stores text plus optional filename metadata. Text-like files up to 256 KiB are
copied into the text box and therefore stored as text; image, PDF, and other
binary bytes are never uploaded.

The UI never tells the user that the previewed binary will not be saved. After
the note is accepted it says `Saved.` and removes the preview. Documentation is
accurately limited, but the user-facing flow is misleading. Camera/Photo/File
should be presented as metadata-only, or hidden until actual byte persistence
exists.

### F-08 — trusted-LAN HTTP is not a full PWA transport

Trusted-LAN mode advertises the same PWA shell over `http://<LAN-IP>:8080` and
the client silently attempts service-worker registration. Service workers are
secure-context-only. Loopback/localhost has a development trust exception, but
an ordinary private-LAN IP over HTTP does not. The W3C Secure Contexts
specification states that service workers are always secure contexts and only
secure clients can register them: <https://www.w3.org/TR/secure-contexts/>.

Consequently a phone reaching the Host by LAN IP can use the web UI, but should
not be described as getting the installable/offline-shell PWA behavior. The
existing no-auth/no-TLS warning is accurate; the PWA capability limitation is
not documented and registration errors are swallowed.

### F-09 — primary reproduction instructions target obsolete behavior

README's primary quickstart and `docs/REPRODUCTION.md` section 12 run
`scripts/seed_demo.py --reset` and then `python -m app.web_app`. The seed writes
`data/demo/state.sqlite`; current `app.web_app` opens
`~/.blackhole/blackhole.db` (or `BLACKHOLE_HOME`) and explicitly does not open
the demo database. The current transport neither auto-seeds nor implements
`POST /api/reset`, despite section 12 saying it does. README also describes a
provider pill that is not in the current PWA.

Later reproduction sections describe the current Host flow correctly, but the
top-level "Try the local demo" is the path a judge is most likely to run. It
will start an empty product database instead of the described 14-event demo.

### F-10 — exact semantic state is not fully rebuildable

`current_facts` and duplicate components are deterministically rebuildable from
stored observations and relationships. Raw events are durable. But the product
does not durably store the provider request/response, model/reasoning/config
used for each event, or an immutable accepted extraction artifact. Observation
rows retain an extractor version only; the current runtime config can change.

If derived observations/relationships are lost or need a clean rebuild, rerun
requires a live nondeterministic provider and cannot reproduce the exact
accepted semantic state. There is also no product command to reset and rebuild
all derived tables from raw evidence. The narrow projection-rebuild claim is
true; the README invariant that all derived state is rebuildable from raw inputs
and versioned rules is not yet true for semantic extraction.

### F-11 — genericity and query routing are bounded

ResponseProjector contains no named DEV entity routing and operates by public
kind/predicate. That supports novel entity names within the known families.
However, QueryService infers only eight hard-coded kinds from fixed predicate
sets, and ResponseProjector implements fixed subscription, task, service,
merchant, action, insurance, contract, observation, duplicate, and aggregate
views. Entirely new ontology kinds fall through to no result.

Question routing is substring-based. `need` routes to attention even in a
negated or unrelated question; `cost`/`paying` selects three recurring-cost
sections; unsupported questions return an empty bounded result. This is an
honest prototype limitation, not hidden DEV-answer coupling, provided the
submission says "bounded local views" rather than arbitrary personal-memory QA.

### F-12 — product code depends on baseline harness code

`app/provider.py:10-15` imports command construction, parsing, execution, and
reasoning defaults from `baseline/run_baseline.py`. No expected answers or DEV
identifiers enter the provider through this dependency, so it is not semantic
benchmark coupling. It is nevertheless a packaging and trust-boundary coupling:
the product runtime cannot be distributed independently of the benchmark
baseline module, and future baseline-only changes could alter product calls.

### F-13 — corrupted configuration is not recoverable

An invalid `config.json` raises `JSONDecodeError`. CLI Host catches this and
returns an error, but the web server starts, `/api/health` remains green without
opening HostRuntime, and dynamic GET handlers do not uniformly convert runtime
open failures into JSON. There is no quarantine, fallback-to-safe-defaults, or
repair command. A single interrupted/manual config edit can therefore make the
PWA shell appear healthy while state is unusable.

### F-14 — clean-machine assumptions are underspecified

The repository has no Python version file, package metadata, or requirements
manifest. It passed on Python 3.12.3, Codex CLI 0.150.0-alpha.12.2, Git 2.50.0
for Windows, and Windows NT 10.0.26200. The code requires modern Python syntax
but documentation says only `python`. Discovery parses a CLI version but does
not enforce a minimum or confirm that configured model/reasoning is available;
the first real processing request is the capability probe. The configured
model is also a mutable service dependency.

### F-15 — escaped invalid Unicode becomes a transport failure

Malformed UTF-8 and malformed JSON are correctly rejected. But valid JSON can
contain an escaped unpaired surrogate. Canonical payload hashing uses UTF-8 and
raises `UnicodeEncodeError`; a temporary engine probe confirmed no raw row was
inserted, while the HTTP layer would return generic 500. This is low-frequency
input hardening, not silent source corruption.

## Durable memory review

Raw event immutability and raw/derived separation are well implemented.
Duplicate components use only true duplicate relation types and preserve raw
members. Current facts and history are distinct. Fingerprints make identical
replays idempotent.

The effective transactional unit is too small. Independent commits make the
processing status an unreliable indicator of whether all derived effects for
the attempt landed. Recovery is incomplete for both stale `processing` and
partial derived rows. SQLite's default transaction mode is sufficient for
individual methods but not for the semantic batch invariant. F-01 through F-03
are the actual severity of the documented processing-row limitation: P1, not a
cosmetic known issue.

## Capture-now / understand-later review

Verdict: **PASS** for provider independence. `Saved.` depends on request
validation, config/database open, sequence allocation, and one SQLite commit;
it does not depend on Codex availability, authentication, discovery, model
availability, semantic parsing, or projection. The server lock prevents two
Host requests from racing sequence allocation in the integrated HTTP process.
Direct multi-process writers are not coordinated beyond SQLite constraints and
may receive a uniqueness/busy failure, but cannot trigger semantic work.

## Ask-time freshness and query-routing review

The intended graph is present:

```text
POST/GET query
  -> HostRuntime.ensure_state_fresh()
  -> provider selection only when pending exists
  -> chronological batch processing
  -> projection rebuild
  -> Host snapshot
  -> deterministic QueryService/ResponseProjector
```

With no pending work, no provider is constructed. With provider failure, the
current batch becomes failed and the first Ask returns 409. Repeating a query
does not rerun provider work unless pending rows remain. Unfortunately, F-03
and F-04 mean retries can process later work out of order and then return stale
answers as ordinary success. GET Ask is also both expensive and side-effecting.

## Genericity / benchmark-coupling verdict

**No hidden DEV-answer or identifier coupling was found in product/runtime
behavior.** Occurrences classify as follows:

- Public DEV names: frozen public response contract and query bundle.
- DEV scenario defaults: baseline and advanced benchmark runners only.
- DEV names/event IDs/state keys: tests and historical/evaluation docs only.
- `state_key` checks in runtime prompts/completeness: defensive rejection, not
  answer production.
- Expected/evaluator imports: scorer and scorer tests only; none in runtime,
  provider, QueryService, or ResponseProjector.

The projector is generic across entities that fit its known kind/predicate
families, not across arbitrary new ontologies. That limitation is F-11, not a
benchmark leak.

## Security review

### Provider and credentials

Verdict: **MIXED**. There are no token reads, auth-file copies, credential
fields, shell command strings, or arbitrary command injection. `subprocess.run`
receives an argument list and a read-only isolated working directory. Version
and auth discovery reduce output to safe summaries. Host failures redact raw
stderr and provider exception text.

F-06 prevents a clean privacy/reproducibility pass: raw private captures are
sent to a non-ephemeral CLI session and user config is not isolated. Temporary
output cleanup is therefore not the whole persistence story.

### Host network

Verdict: **MIXED / P1 before broader demonstration**. Default loopback bind,
explicit non-loopback opt-in, serialized Host requests, traversal defense,
bounded bodies, method-specific domain endpoints, no-store headers, and lack
of shell routes are good. F-05 means loopback browser-origin attacks and DNS
rebinding are not addressed. Trusted-LAN warnings accurately admit no auth,
TLS, pairing, or public-network safety.

### PWA privacy

Verdict: **PASS with disclosed metadata limitations**. API responses are not
service-worker cached. No draft, answer, or personal state is deliberately
stored client-side. Filename metadata and any imported text become immutable
server-side evidence; local milestone counters reveal only use volume to the
browser profile. F-07 is a truth-in-UI issue, and F-08 limits LAN PWA behavior.

### Consequential actions

Verdict: **PASS**. No path sends, pays, cancels, signs, deletes external data,
changes an account, or exposes arbitrary shell access. State may record an
`executed` observation if source evidence says so, but it does not execute it.

## Evaluation fairness review

Verdict: **PASS for the frozen public comparison**.

- Both treatments receive the same chronological public captures and query
  bundle.
- The baseline is one canonical ingestion chat; checkpoint queries use atomic
  native forks and are discarded, so answers do not contaminate later capture
  history.
- The baseline has no Blackhole state store, evaluator, expected output, or
  hidden summary.
- The advanced runner's extra SQLite memory, scoped semantic batches,
  deterministic arithmetic/date/relation/projection code, and duplicate
  consolidation are documented treatment differences.
- Candidate production occurs before `eval/score.py` reads expected output.
  The scorer's expected-only legacy `state_key` handling does not flow back to
  candidate production.
- Recorded zero-provider replays reuse frozen extraction artifacts and are
  accurately described as replays, not fresh independent model evidence.

The structural import in F-12 should be removed eventually, but it does not
currently pass expected answers or DEV identities into product inference. No
official baseline or score was rerun during this audit.

## Reproducibility review

Verdict: **REVISE before judge handoff**. The standard-library runtime and
temporary-home tests are portable in principle, and the full deterministic
suite passed. The main blockers are the stale primary quickstart (F-09),
unrecoverable corrupted config (F-13), unpinned Python/CLI/model assumptions
(F-14), and user-config/session dependence (F-06). Windows path behavior passed
locally. `BLACKHOLE_HOME` is explicit and database escape is rejected.

## Failure-injection observations

All probes used fake providers and temporary directories; none made a network
or model call and none created tracked runtime files.

| Probe | Observation |
| --- | --- |
| Duplicate replay | Existing tests confirm identical event replay is idempotent and conflicting same-ID replay is rejected |
| Failure during second one-event batch | First event processed, second failed, third remained pending in that call |
| Second processing request after failure | Third event processed despite earlier failed second event (F-03) |
| Restart after committed claim | Row stayed `processing`; no reclaim or retry path (F-01) |
| Partial observation commit then retry | Two values for one capture remained and projected consumption summed both (F-02) |
| Malformed JSON/UTF-8 | HTTP validation rejects malformed input |
| Escaped unpaired Unicode | `UnicodeEncodeError`, no raw row, generic HTTP failure (F-15) |
| Huge text | HTTP limits are 1,000,000 body bytes and 100,000 capture characters; PWA textarea limits to 20,000 |
| Repeated query | No provider call when state is fresh; failed-only state returns a stale successful answer (F-04) |
| Provider unavailable | Raw evidence retained; first Ask 409, explicit retry available after auth repair |
| Corrupted config | `JSONDecodeError`; no automatic repair and health route remains independent (F-13) |
| Cross-origin write | `text/plain` JSON POST with hostile Origin was accepted (F-05) |
| Host-header probe | `/api/state` accepted arbitrary Host and returned 200 (F-05) |
| Concurrent Host access | Integrated HTTP operations are serialized by a server-level reentrant lock |

## Known limitations that are honest/non-blocking

- This is local hackathon infrastructure, not a production service.
- No OCR or arbitrary binary attachment persistence exists.
- No pairing, TLS, cloud relay, account system, scheduler, or public hosting
  exists.
- QueryService intentionally supports bounded deterministic views rather than
  general open-ended QA.
- Novel entity linking is imperfect and already disclosed.
- Provider/model availability is external and Ask may take a full semantic
  processing interval.
- One public DEV scenario does not establish independent generalization.

These are non-blocking when stated plainly. They become blocking only when the
UI, video, or submission implies broader behavior.

## Recommended AFTER-GENERALIZATION backlog

1. Introduce one transaction/savepoint per claimed semantic batch; make
   observations, relationships, projection, completion, and status atomic.
   Define attempt identity and remove/replace attempt-scoped derived rows on
   retry.
2. Add startup recovery for stale `processing` rows using a lease/heartbeat or
   deterministic reclaim-to-failed policy; test process death at every commit
   boundary.
3. Enforce a durable chronological barrier across pending, failed, and
   processing rows. Make extraction context truly prefix-scoped.
4. Define an explicit degraded/stale Ask response. Never render ordinary 200
   freshness when any failed or processing row affects the requested state.
5. Remove GET query processing. Enforce accepted Host values, same-origin
   Origin/Fetch-Metadata, JSON content type, and a local authorization/CSRF
   token. Pair/authenticate before any LAN use.
6. Run product semantic calls with `--ephemeral` and an intentionally isolated
   config surface while preserving external CLI authentication. Keep provider
   utilities out of the baseline package.
7. Decide whether binary attachments are a feature. Until then, say clearly in
   the picker and success UI that only the note, filename, and eligible imported
   text are saved.
8. Either add HTTPS/pairing for LAN devices or describe LAN mode as a plain web
   demo without install/offline PWA guarantees.
9. Replace the obsolete seeded-demo quickstart with one canonical current Host
   flow; add a clean-machine smoke that uses a temporary `BLACKHOLE_HOME`.
10. Narrow "rebuildable" to deterministic projection rebuild, or persist an
    immutable accepted extraction artifact plus complete provider/prompt/model
    provenance and add a clean rebuild command.
11. Pin and document a tested Python floor, Codex CLI range, model availability
    behavior, and Windows/POSIX commands. Add config quarantine/recovery.
12. Add neutral tests for new ontology kinds and route negation/false positives;
    preserve the bounded-query claim unless broader routing is implemented.

## Freeze recommendation

### Special decision

**Is there any finding severe enough that we should ABANDON the current
implementation freeze before opening the generalization oracle? NO.**

Rationale: no P0 was found, the frozen benchmark/evaluator/baseline evidence is
intact, runtime product code does not consume DEV expected answers, and the
capture-path and consequential-action claims remain valid. Opening the isolated
generalization oracle under its existing authorization does not require fixing
these runtime findings and must not be used to tune the frozen runtime.

This is not a recommendation to submit the current Host/PWA unmodified. Keep
the frozen reference for the generalization gate, then **REVISE** the product on
an explicitly authorized post-generalization hardening branch before the final
video/submission. Do not merge this audit branch into the frozen implementation.

## Methodology and evidence

- Reviewed the requested application, provider, store, semantic,
  completeness, relation, projection, query, Host, web/PWA, baseline, prompt,
  scorer, public contract/query bundle, tests, architecture, evaluation, freeze,
  README, and reproduction surfaces.
- Classified exact identifier occurrences with repository search restricted to
  allowed paths.
- Ran `python -m unittest discover -s . -p "test_*.py" -v`: 85 passed in
  13.191 seconds.
- Ran deterministic temporary SQLite/fake-provider failure probes described
  above.
- Ran local non-inference discovery/help commands only: Python version, Git
  version, `codex --version`, and `codex exec --help`.
- Consulted the W3C Secure Contexts specification only for the current
  service-worker/LAN claim.
- Did not execute baseline, advanced runner, scorer, benchmark generator,
  provider inference, or any generalization path.
- No evaluation artifact was created because runtime behavior did not change
  and the audit instruction prohibited new scoring.
