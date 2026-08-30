# Improvement changelog

This file records material improvements to the product design, agent workflow, evaluation protocol, and repository safeguards. It is not a runtime event log.

## 2026-08-28 — Initial documentation scaffold

- Established the zero-organization personal inbox concept and its core constraints.
- Added product, architecture, decision, evaluation, and reproduction documentation.
- Reserved separate locations for prompts, application work, baselines, data, evaluations, scripts, and trajectories.
- Added explicit rules for immutable raw sources, rebuildable derived state, unknown values, deterministic calculations, user approval, and benchmark isolation.
- Added no application code, benchmark cases, expected outputs, or ground truth.

## 2026-08-29 — Gate A provider and size calibration

- **Stage / experiment identifier:** Gate A runtime calibration, Codex CLI subscription path.
- **Problem observed:** The assumed direct-API runtime was inconsistent with the subscription-first MVP, and the final event count could not be chosen responsibly without measuring state churn at several realistic lengths.
- **Hypothesis:** An installed authenticated Codex CLI can provide a reproducible persistent-session baseline, and state quality can be compared at 50, 100, 200, and 400 events without forcing context overflow.
- **What changed:** Documented the provider-neutral CLI boundary, verified Codex CLI `0.150.0-alpha.12.2` with `gpt-5.6-luna` / `max`, and ran the frozen prompt/query bundle in fresh isolated persistent sessions at all four sizes. No baseline or application implementation was added.
- **Evaluation method:** Deterministic comparison of four fixed assertion groups against the visible non-scored calibration oracle; no LLM judge and no prompt tuning after official runs.
- **Metric before:** No provider runtime or correctness measurement existed.
- **Metric after:** LQA-style readouts were 0.8167 / 0.9000 / 0.8545 / 0.8091 at 50 / 100 / 200 / 400 events; state-only means were 0.8889 / 1.0000 / 0.9394 / 0.8788.
- **Regressions:** Duplicate counts were overestimated at every size; the 400-event run added current/previous-state defects and took about 576 seconds. The 50/100/200/400 state curve was non-monotonic and was run once per size.
- **Runtime/cost impact:** Provider-reported input/query tokens were 24,696 / 31,347 / 44,653 / 71,334 respectively for the query turns; subscription pricing was not exposed.
- **Decision:** **KEEP** the subscription-first provider boundary and calibration protocol; **REVISE/hold** final length until human Gate A review, provisionally 200 primary and 400 stress.
- **Learning:** 400 events were empirically accepted without a context warning, but fit is not the same as practical repeatability. The benchmark should prioritize state churn and realistic 150–200-event histories, with larger histories clearly secondary.

## 2026-08-29 — Gate A development benchmark and fair baseline

- **Stage / experiment identifier:** Gate A freeze, evaluator LQA-0M-v1, and Codex baseline-v0.
- **Problem observed:** The approved benchmark needed a reproducible 200-event state-churn case, deterministic scoring, and a fair comparator before any advanced application work could begin.
- **Hypothesis:** A deterministic ten-storyline generator plus isolated checkpoint forks can measure longitudinal state quality without exposing holdout ground truth or adding Blackhole memory to the baseline.
- **What changed:** Added the frozen public development contract, 200-event case, visible development oracle, human review artifact, stdlib evaluator/tests, and Codex CLI runner. The runner uses one canonical ingestion session, four chronological batches, and an atomic read-only fork at each checkpoint.
- **Evaluation method:** Generator determinism check, seven evaluator unit tests, and one official Codex CLI run at checkpoints 50/100/150/200 using `gpt-5.6-luna` with reasoning `max`. The evaluator used exact canonical assertion sets, explicit unknown semantics, source hashes, DSCR, and a hard safety gate.
- **Metric before:** No frozen development case, executable scorer, or scored baseline existed.
- **Metric after:** Generator check passed; all 7 tests passed; baseline-v0 completed all checkpoints with LQA-0M `0.0000`, checkpoint scores `0.0000/0.0000/0.0000/0.0000`, `TP=0`, `FP=266`, `FN=375`, DSCR `336`, no safety violation, and no source-integrity failure.
- **Regressions:** The baseline selected a semantically different state-key/assertion vocabulary, so the exact contract produced no true-positive matches. The official query forks took approximately 2,513 seconds; no context limit or dollar pricing was exposed.
- **Runtime/cost impact:** Canonical capture turns took approximately 20 seconds. Query-fork input/output tokens were 24,582/35,031, 30,662/32,201, 38,463/37,523, and 44,556/34,037 at checkpoints 50/100/150/200. Subscription cost is not reported because it was not exposed.
- **Decision:** **KEEP** the benchmark, evaluator, isolation protocol, and baseline evidence. **REVISE** only the baseline response-vocabulary issue during Gate B review; do not alter expected outputs to improve this score.
- **Learning:** Checkpoint isolation is operationally reliable with the atomic fork form, but an exact typed assertion contract must be clearly distinguished from a model's free-form semantic summary. Runtime cost and vocabulary alignment are now explicit Gate B concerns.

## 2026-08-29 — Gate B response-contract repair and corrected baseline

- **Stage / experiment identifier:** Gate B contract repair, `response-contract-v2`, and official `baseline-v1`.
- **Problem observed:** The preserved v0 run's `LQA-0M=0.0000` was invalid as a semantic baseline: it had zero true positives, grouped/dotted records, evaluator-internal key mismatch, and malformed `unknown` assertions with values.
- **Hypothesis:** A public subject/predicate assertion boundary, deterministic normalization, explicit unknown/value rules, and exact duplicate-count wording will separate interface failures from genuine longitudinal state errors without changing benchmark facts or the substantive baseline prompt.
- **What changed:** Preserved v0 under invalid-contract names; added the frozen v2 response contract, query bundle, schema, deterministic public canonicalizer/evaluator, independent non-scored smoke test, runner recovery/path fixes, and labeled 50-event fast slice. Added one official 200-event corrected baseline using the same Codex CLI/model/reasoning configuration.
- **Evaluation method:** Generator determinism check, 9 evaluator tests, independent 6-assertion smoke fixture, one 50-event diagnostic slice, and one four-checkpoint official run against unchanged public development expected values. No LLM judge, holdout data, or prompt tuning was used.
- **Metric before:** v0 `LQA-0M=0.0000`, `TP=0`, `FP=266`, `FN=375`, but invalid as a semantic measurement.
- **Metric after:** v2 official `LQA-0M=0.3014914553`; checkpoint means `0.2894 / 0.2669 / 0.3127 / 0.3369`; `TP=146`, `FP=239`, `FN=229`; schema-valid, source-integrity-valid, safety-pass; `DSCR=277`.
- **Regressions:** Relation reconciliation and entity resolution remained at 0.0000 category score; current-state and temporal scores remained low. The single run did not show monotonic degradation with history length. Query forks took approximately 2,473.735 seconds and reported 149,768 query input / 204,982 query output tokens; dollar subscription cost was unavailable.
- **Runtime/cost impact:** Including canonical turns, the official run took approximately 2,490.516 seconds and reported 280,425 input / 205,068 output tokens. The 50-event non-official slice took approximately 398.234 seconds including canonical capture.
- **Decision:** **KEEP** v2 contract, deterministic scorer, isolation protocol, and corrected baseline evidence; **REVISE/REMOVE** v0 only as an official measure while preserving its files as invalid historical evidence.
- **Learning:** A nonzero, schema-valid result makes the remaining errors interpretable as semantic/recall/state failures. Public contract design must define both identifier vocabulary and deterministic value normalization before an official run.

## 2026-08-29 — Experiment 001: append-only state projection

- **Stage / experiment identifier:** Experiment 001, minimal Blackhole-owned durable state and deterministic projection.
- **Problem observed:** The valid stateless baseline scored `LQA-0M=0.3014914553` with `DSCR=277`; current-state, temporal-history, and relation reconciliation errors suggested that a long provider conversation was not maintaining a reliable rebuildable state.
- **Hypothesis:** Immutable raw captures plus structured observations/relationships and a deterministic rebuildable projection can improve longitudinal state quality without giving the model evaluator knowledge or relying on LLM arithmetic and date logic.
- **What changed:** Added a scoped SQLite state store with immutable raw-event triggers, provenance/history, knowledge-status handling, contradiction/supersession logic, a subscription-first Codex extraction boundary, and a deterministic public response projector. Added replay support so projection revisions could be compared against the same recorded semantic extraction. Unsupported query families no longer fall back to a state dump.
- **Evaluation method:** FAST DEV first, followed by the frozen public 200-event milestone. Fresh semantic extraction was performed only against public development captures; query and projection revisions were replayed deterministically. The unchanged `response-contract-v2` evaluator and public expected output produced the reported scores. No holdout data, evaluator changes, benchmark changes, or baseline prompt tuning were used.
- **Metric before:** Official `baseline-v1`: LQA-0M `0.3014914553`, DSCR `277`. The four-query 50-event diagnostic slice was LQA-0M `0.2217948718`, DSCR `41`.
- **Metric after:** FAST final deterministic replay: LQA-0M `0.7222222222`, DSCR `10`. Full v4 deterministic replay: LQA-0M `0.7492295899`, checkpoint scores `0.7962962963 / 0.7523071836 / 0.7064078283 / 0.7419070513`, DSCR `72`, and totals `TP=279, FP=69, FN=96`. Schema validity, safety, and source integrity all passed.
- **Regressions:** The first full projector revision scored `0.1589548193` because a catch-all state dump created 1,900 false positives; it was removed. A fresh model-query replay scored `0.0990021008` and was not kept. The remaining full-v4 relation-reconciliation score is `0.3169014085`; duplicate/change relationship detail, contract-date recall, and some task/recent-change assertions remain weak. Fresh extraction used reasoning `high`, not `max`, because the latter was not practically usable for the 200-event run.
- **Runtime/cost impact:** Four fresh semantic calls took `887.453` seconds and reported `132,514` input, `72,711` output, and `53,751` reasoning tokens. The 50-event live FAST run took about 220 seconds and reported `27,831` input, `19,151` output, and `15,020` reasoning tokens. Full-v4 projection replay made no provider calls. Subscription pricing was unavailable.
- **Decision:** **KEEP** the Experiment 001 architecture as the current experimental slice. Do not change the frozen benchmark or official baseline, and do not start Experiment 002 in this task.
- **Learning:** Durable state plus deterministic projection materially improved the public current/history/financial result and reduced defects. Relationship detail is now the clearest evidence-backed next target; the result should not be generalized to holdout performance or production readiness.

## 2026-08-29 — Experiment 002: generic state-projection repair

- **Stage / experiment identifier:** Experiment 002, genericity repair for the E001 deterministic response projector.
- **Problem observed:** An audit found that the committed projector selected several projections and query branches using literal public benchmark subject IDs and brand names. That violated the requirement that the state-maintenance mechanism represent generic Blackhole entities and state transitions.
- **Hypothesis:** Selecting subjects by their public ontology kind, routing by query-family vocabulary, and using observation semantics for high-precision event relations will preserve E001's state-quality result without encoding one synthetic storyline.
- **What changed:** Replaced named-subject routing with kind-driven subscription, service, merchant, insurance, observation, contract, and aggregate projections. Service and merchant aggregation now handles multiple subjects. Duplicate/change filtering uses capture structure and excludes entity-link-only endpoints. Added generic unit fixtures for subscription and change projections. No benchmark, expected output, response contract, evaluator, baseline, calibration, or holdout material changed.
- **Evaluation method:** Fifteen application/evaluator unit tests, a labeled 50-event FAST replay, and a four-checkpoint public 200-event replay from the already-recorded E001 semantic extraction. The unchanged `response-contract-v2` evaluator scored both replays. No provider calls or prompt tuning were used.
- **Metric before:** E001 final public replay `LQA-0M=0.7492295899`, `DSCR=72`; the projector had no independent genericity measurement.
- **Metric after:** FAST diagnostic `LQA-0M=0.8888888889`, `DSCR=4`; full replay `LQA-0M=0.7492295899`, checkpoint scores `0.7962962963 / 0.7523071836 / 0.7064078283 / 0.7419070513`, `DSCR=72`, and `TP=279, FP=69, FN=96`. Schema validity, safety, and source-integrity checks passed. The full score is numerically identical to E001 and is not an official baseline result.
- **Regressions:** The first generic duplicate rule counted entity-link-only similarity chains as capture duplicates, reducing the full replay to `LQA-0M=0.7472666121` and increasing DSCR to `82`. That revision was tightened using the generic `entity_link` predicate rule and replayed successfully. No unresolved regression remains from this repair.
- **Runtime/cost impact:** Both final replays used zero provider input/output/reasoning tokens and completed as local deterministic replays in approximately two seconds per command invocation. The repair added no subscription cost or model calls.
- **Decision:** **KEEP** the genericity repair. Preserve E001's prior artifacts and result unchanged; treat the new full artifact as reproducible repair evidence, not as a new official baseline.
- **Learning:** Public ontology kinds and observation semantics are sufficient to remove benchmark-specific projector coupling while retaining the validated score. Relation-detail recall remains the next evidence-backed weakness, and any follow-up must use a new trajectory.

## 2026-08-29 — Final phase relation-detail audit

- **Stage / experiment identifier:** Phase 1 bounded audit; Experiment 003 not launched.
- **Problem observed:** Relation-detail recall was the weakest measured area. The recorded E001 extraction/state contained many relationships, but several missing expected duplicate/change edges were absent or represented with different targets.
- **Hypothesis:** If the missing expected relation details were already present in the recorded structured state, a deterministic projection repair could improve them without new model calls.
- **What changed:** Performed a read-only comparison of all recorded public extraction relationships, the SQLite relationship state, and the public development relation expectations. No application, benchmark, evaluator, prompt, or provider change was made.
- **Evaluation method:** Deterministic relationship-row and expected-assertion audit over the recorded E001 public artifacts; no new provider extraction and no score rerun.
- **Metric before:** Preserved E001 full replay `LQA-0M=0.7492295899`, `DSCR=72`, with relation-detail weakness documented.
- **Metric after:** No implementation change and therefore no new metric. The audit established that deterministic-only recovery cannot supply all missing target edges.
- **Regressions:** None; the frozen benchmark, baseline, and prior result remain unchanged.
- **Runtime/cost impact:** Read-only local inspection; zero provider calls and no additional subscription cost.
- **Decision:** **REVISE** the plan by deferring relation-detail extraction work. Do not launch Experiment 003; proceed to product/demo and submission work.
- **Learning:** Relation detail requires richer semantic extraction and is deferred. Existing structured evidence is sufficient for the validated core but not for complete relation recall.

## 2026-08-29 — Final product demo and submission scaffold

- **Stage / experiment identifier:** Final product phase; deterministic local demo and submission evidence.
- **Problem observed:** The validated state-projection core had no small user-facing surface that demonstrated universal capture, attention, persistent memory, uncertainty, and approval boundaries to a hackathon judge.
- **Hypothesis:** A local stdlib web demo backed by the existing SQLite state boundary can make the core product behavior inspectable without adding production infrastructure or hidden provider behavior.
- **What changed:** Added a committed synthetic 14-event demo seed, reset/seed command, append-only raw capture endpoint, deterministic state/query endpoints, and a mobile-first static UI. Added demo tests, reproduction notes, representative runtime evidence, and video/submission documentation.
- **Evaluation method:** Automated demo unit/HTTP tests plus a rendered browser smoke check covering page load, Attention, Memory, Ask, and `Saved.` feedback. The demo was not scored against the frozen benchmark.
- **Metric before:** No browser-facing demo; only the app state/projection experiment surface.
- **Metric after:** Seed rebuilds 14 events, 27 observations, and four relationships; all demo tests passed; browser smoke check rendered the required views and capture feedback. No provider calls were made by the demo capture path.
- **Regressions:** The demo intentionally leaves newly captured text semantically pending and supports only small text-file import; it is not a production ingestion or OCR system. Existing relation-detail recall remains deferred.
- **Runtime/cost impact:** Local standard-library server and deterministic SQLite operations; no additional provider calls or subscription cost.
- **Decision:** **KEEP** the local demo as a scoped product surface; do not infer production readiness from it.
- **Learning:** A narrow capture-to-state surface makes the raw/derived/attention boundary legible while preserving the benchmark and baseline as separate evidence.

## 2026-08-29 — Experiment 003: bounded raw-capture relation reconciliation

- **Stage / experiment identifier:** Experiment 003, deterministic recovery plus bounded raw-capture candidate retrieval.
- **Problem observed:** The kept Experiment 002 replay scored `LQA-0M=0.7492295899` with `DSCR=72`; relation reconciliation was `0.3169014085`, and 39 of 72 DSCR defects were in that category. Recorded structured observations did not retain enough receipt identifiers and lineage to resolve several duplicate/change targets.
- **Hypothesis:** A generic candidate-retrieval layer that supplies a small number of relevant earlier raw captures to deterministic reconciliation can improve relation targets, duplicate groups, and changed-field detail without retrieving complete history or invoking a provider resolver.
- **What changed:** Added `app/relation_recovery.py` with conservative explicit-supersession and duplicate-marked raw-hash fallback plus a bounded primary-identifier retrieval pass. Added derived-only relationship replacement in `StateStore`, runner selection/trajectory records, and generic unit fixtures. The public projector omits empty duplicate relation fields, does not count standalone changes as duplicate groups, and keeps narrative meaningful-change notes out of public duplicate detail. No benchmark, expected output, contract, evaluator, official baseline, calibration, or holdout artifact changed.
- **Evaluation method:** Read-only failure audit; neutral relation-recovery fixtures; full repository tests; generator `--check`; contract smoke; relation-focused 50-event FAST replay; final four-checkpoint 200-event replay using the unchanged recorded E001 semantic extraction; unchanged deterministic evaluator; hash audit of protected artifacts. No provider call or prompt tuning was used.
- **Metric before:** Kept Experiment 002 full replay: LQA-0M `0.7492295899`, DSCR `72`, relation reconciliation `0.3169014085` (`TP=45, FP=52, FN=45`), checkpoint-200 duplicate/change score `0.0666666667`.
- **Metric after:** Final v3 full replay: LQA-0M `0.8157180034`, checkpoints `0.8518518519 / 0.8189738502 / 0.7821654040 / 0.8098809075`, `TP=311, FP=37, FN=64`, DSCR `45`, relation reconciliation `0.6696428571` (`TP=75, FP=22, FN=15`), duplicate/change `1.0`, schema-valid, safety-pass, and source-integrity-valid. Relation-focused FAST was `LQA-0M=0.962963`, `DSCR=1`.
- **Regressions:** The first full retrieval replay had an interaction where deterministic fallback relations blocked some replacements; it scored `LQA-0M=0.7718854063`, `DSCR=64` and is preserved as an intermediate artifact. The corrected v2 replay scored `0.7937642219` / `52`; the final v3 correction removed the residual standalone-group and public-note mismatches. One expected similar-receipt narrative note remains intentionally unasserted because the raw text does not explicitly establish it. No category, safety, schema, or source-integrity regression remained.
- **Runtime/cost impact:** All runs were local deterministic replays of recorded public extraction. Provider calls and provider tokens added: `0`; final runner invocation completed in under one second of local wall time, excluding the separate evaluator invocation. Candidate retrieval is capped at four earlier captures per considered relation and records the raw candidate content/metadata in the runtime trajectory. Subscription cost is unavailable and unchanged.
- **Decision:** **KEEP** the bounded retrieval treatment. It exceeds the predeclared keep threshold through LQA improvement of `+0.0664884135` and DSCR reduction of `27`, without material regression. Do not start a provider resolver or Experiment 004 in this task.
- **Learning:** A small, auditable retrieval window can repair longitudinal relation lineage when structured extraction loses stable identifiers; it should remain bounded and deterministic, and unresolved evidence should stay unresolved rather than being fabricated.

## 2026-08-29 — Experiment 004: selective semantic completeness verification

- **Stage / experiment identifier:** Experiment 004, generic raw-source evidence scanning and selective completeness treatment.
- **Problem observed:** The kept Experiment 003 replay scored `LQA-0M=0.8157180034` with `DSCR=45`. A read-only audit estimated approximately 7 DSCR defect IDs could plausibly reflect facts explicitly present in raw captures but omitted from same-capture observations; most remaining defects were not extraction-completeness problems.
- **Hypothesis:** Structural anchors for dates, amounts/currencies, identifiers, and lifecycle cues can expose a small number of high-confidence semantic omissions. Deterministic completion should repair those omissions without reprocessing every capture, changing raw sources, or redesigning relation reconciliation.
- **What changed:** Added generic `app/completeness.py` scanner, same-capture coverage detector, conservative deterministic completion, a versioned one-capture verifier prompt/boundary, runner metrics and trajectory records, and neutral unit fixtures. The verifier was not invoked because deterministic FAST already justified the full replay. No benchmark, expected output, query bundle, response contract, evaluator, official baseline, calibration, holdout, or prior result artifact changed.
- **Evaluation method:** Read-only E003 failure audit; neutral scanner/gap/completion/verifier-boundary tests; full repository tests; generator `--check`; contract smoke; completeness-focused 50-event FAST slice; unchanged public four-checkpoint 200-event evaluator replay using the recorded E001 extraction and unchanged E003 retrieval treatment; protected-artifact hash audit. No baseline rerun, prompt tuning, holdout access, or provider call was used.
- **Metric before:** Kept Experiment 003 full replay: LQA-0M `0.8157180034`, checkpoints `0.8518518519 / 0.8189738502 / 0.7821654040 / 0.8098809075`, DSCR `45`, relation reconciliation `0.6696428571`.
- **Metric after:** Completeness-focused FAST improved from LQA-0M `0.6444444444` / DSCR `16` to `0.7333333333` / `12` over five public query families. The full replay scored LQA-0M `0.8630770101`, checkpoints `0.8888888889 / 0.8713728401 / 0.8321654040 / 0.8598809075`, totals `TP=327, FP=35, FN=48`, DSCR `41`, relation reconciliation unchanged at `0.6696428571`, schema-valid, safety-pass, and source-integrity-valid. The runner scanned 200 captures, flagged 10, repaired 6 captures, added 8 observations including one correction, and made zero provider/verifier calls or tokens.
- **Regressions:** The safety category gained one false-positive assertion while its score improved; the deterministic safety scan still reported no consequential execution. Financial, relation reconciliation, duplicate/change, entity resolution, obligation/deadline, and contradiction metrics were unchanged. Four conservative lifecycle flags remained residual and were not escalated to a verifier. No protected artifact changed.
- **Runtime/cost impact:** Deterministic FAST completed locally in about `0.17` seconds and the full replay in about `0.61` seconds according to runner metadata, excluding evaluator invocations. Provider calls, input/output/reasoning tokens, and provider runtime were all `0`; no subscription cost was incurred.
- **Decision:** **KEEP** deterministic selective completeness. It exceeds the predeclared threshold through LQA improvement of `+0.0473590067` and DSCR reduction of `4`. Keep the verifier available as a scoped future option, but do not start another experiment in this task.
- **Learning:** A small structural-evidence pass can recover explicit omissions while preserving unknowns and the raw/derived boundary. The strongest remaining failures are semantic role/projection losses and relation reconciliation, not generic anchor discovery; future work must not broaden this pass by encoding benchmark storylines.

## 2026-08-29 — Experiment 005: duplicate-aware evidence consolidation

- **Stage / experiment identifier:** Experiment 005, projection-boundary consolidation of evidence from true duplicate components.
- **Problem observed:** The E004 projection excluded observations from duplicate-source captures before current-state reconciliation. A checkpoint-aware public audit found three meaningful losses: Streamly's next renewal, GymFlex's expiry date, and the bank standing-order approval state.
- **Hypothesis:** True duplicate captures should remain one occurrence for counting, while their predicate-level evidence can be consolidated deterministically. This should recover valid state without double-counting financial/task/duplicate facts or changing non-duplicate relations.
- **What changed:** Added an opt-in, versioned duplicate-component layer in `app/state_store.py`. It builds undirected components only from `exact_duplicate`, `normalized_duplicate`, and `duplicate` edges; chooses the earliest capture as canonical; records all member IDs in rebuildable SQLite metadata; consolidates identical subject/predicate observations; preserves unresolved conflicts as unknown; and follows only unambiguous terminal correction/supersession chains. Added neutral tests, runner metadata, public replay artifacts, and reproduction documentation. No benchmark, expected output, query bundle, response contract, evaluator, baseline, calibration, or holdout artifact changed.
- **Evaluation method:** Phase 0 read-only audit; eight neutral state-store tests; full application and evaluator test suites; generator `--check`; contract smoke; standard 50-event FAST replay; final four-checkpoint 200-event replay using the recorded public extraction; unchanged `eval/score.py`; protected-artifact and raw-source hash/content checks. No provider calls, prompt tuning, holdout access, or E004 verifier calls.
- **Metric before:** Kept E004 full replay: LQA-0M `0.8630770101`, checkpoints `0.8888888889 / 0.8713728401 / 0.8321654040 / 0.8598809075`, totals `TP=327, FP=35, FN=48`, DSCR `41`.
- **Metric after:** FAST remained LQA-0M `0.8888888889`, DSCR `4`. Full E005 replay: LQA-0M `0.8695006212`, checkpoints `0.8888888889 / 0.8713728401 / 0.8321654040 / 0.8855753519`, totals `TP=330, FP=35, FN=45`, DSCR `40`. Current-state improved from `0.7222222222` to `0.7407407407`, temporal-history from `0.8730158730` to `0.8888888889`, and safety from `0.75` to `0.7708333333`.
- **Diagnostics:** The final projection formed 24 components containing 72 events, including 48 non-canonical members; recovered 51 observations from duplicate-source captures and consolidated 36 identical observations. The count audit recorded 200 raw events, 48 duplicate relation edges, 24 single-occurrence component units, and 287 input observations versus 251 projected observation groups; projected groups did not increase. Financial, duplicate/change, entity-resolution, relation-reconciliation, and unknown-state metrics did not regress. Schema validity, source integrity, and safety passed.
- **Regressions:** An initial replay exposed a false conflict for a supersession chain within one duplicate component; terminal-chain resolution fixed it and restored the 150-event checkpoint. An initial provenance variant attached all component members to every predicate and added DSCR noise; provenance was narrowed to supporting observations while the component table retained all members. No unresolved regression remains in the final replay.
- **Runtime/cost impact:** Both E005 replays used recorded public semantic extraction and zero provider calls/tokens; each completed as a local deterministic replay in approximately two seconds or less per runner invocation, excluding scorer startup. Subscription cost is unavailable and unchanged.
- **Decision:** **KEEP** duplicate-aware evidence consolidation. It recovered all three audited projection losses, reduced DSCR by `1`, improved LQA-0M by `+0.0064236111`, and passed the predeclared financial, duplicate/change, entity, relation, unknown-state, schema, safety, and source-integrity guards. This is the last benchmark-optimization experiment for the frozen development track; no E006 was started.
- **Learning:** Duplicate identity and evidence contribution are separate concepts. A duplicate component can provide additional predicate support, but provenance must stay predicate-scoped and unresolved disagreement must remain explicit uncertainty.

## 2026-08-30 — Product V2 Host/PWA integration

- **Stage / experiment identifier:** Post-freeze Product V2 integration milestone; this is not a benchmark-optimization experiment and is not E006.
- **Problem observed:** The separately developed runtime, PWA, and dogfood harness had incompatible assumptions about V2 routes, attachment bytes, deferred processing, Attention lifecycle state, semantic Undo, and visible acceptance reporting.
- **Hypothesis:** A narrow Host-owned V2 transport reconciliation can make Capture, Attention, Memory, Ask, attachments, retry, restart, and Undo one coherent product contract while preserving the frozen V1 boundary.
- **What changed:** Merged the authorized runtime, UI, and dogfood branches into an isolated integration worktree. Connected the PWA to the real `/api/v2/*` routes, added bounded base64 attachment transport, asynchronous processing feedback and retry, lifecycle-aware Attention projection, deterministic Ask/change handling, and a reproducible 50-case integrated acceptance runner with quality gates and latency evidence.
- **Evaluation method:** Full application tests, evaluator tests, dogfood harness tests, JavaScript syntax/compile checks, live local Host browser review at `390x844` and `1280x900`, and the visible deterministic integrated acceptance run. No live provider credentials, benchmark expected output, holdout material, or official baseline rerun was used.
- **Metric before:** Not applicable as a single product metric; the three source branches were separate and their pre-integration capability gaps were recorded by the dogfood harness.
- **Metric after:** `50/50 PASS` in `eval/results/product-v2-integrated-acceptance.json`; all product quality gates passed. The normal-worker latency probe returned capture in `110.706 ms` and completed processing in `239.226 ms` with a `120 ms` fixture-provider delay.
- **Regressions:** No application or benchmark regression remains in the final test pass. Deliberate limitations are that the acceptance provider is deterministic and local, the runner explicitly drains processing for semantic determinism, no human usability study was performed, and production infrastructure/OCR/remote providers remain out of scope.
- **Runtime/cost impact:** The visible acceptance suite uses no provider tokens or subscription calls. The normal-worker probe records the asynchronous boundary separately; no credential handling was added.
- **Decision:** **KEEP** the integrated Product V2 contract and implementation for the explicitly authorized post-freeze product scope. Do not treat this as a new benchmark result or start a follow-up optimization experiment.
- **Learning:** Integration evidence must test the product's trust boundary—durability, exact bytes, retryability, provenance, lifecycle state, and approval semantics—as well as route compatibility. A clean merge is not sufficient without a black-box acceptance and visual pass.

## 2026-08-30 — Product V2 human-dogfood P0/P1 repair

- **Stage / experiment identifier:** Authorized post-freeze Product V2 human-dogfood repair; not a benchmark-optimization experiment and not E006.
- **Problem observed:** The first real dogfood Home exposed a split between the legacy Host queue and the Product V2 queue, a normal-launch worker lifecycle gap, a stale PWA shell risk, an unsupported Codex CLI flag, unbounded automatic retries, and UI copy that could make pending/failed processing look like empty memory. The existing deterministic integrated acceptance and fixture-based latency check did not exercise the full normal app entrypoint with the installed provider.
- **Hypothesis:** A single Home-scoped V2 store path, eager managed worker startup, bounded retry policy, supported/diagnosable CLI invocation, typed degraded responses, and versioned service-worker updates will make normal Product V2 dogfooding durable and truthful without changing the frozen V1 boundary.
- **What changed:** Added `product_database_path()`, Host/Product status agreement, normal `app.web_app` worker startup, five-attempt 1/2/4/8-second retry backoff, safe provider diagnostics, pending/failed Ask and Attention/Memory UX, PWA shell `v7` update behavior, and deterministic regression/provider/retry/UI tests. No benchmark prompt, expected output, evaluator, baseline, calibration, holdout, or protected Home was changed.
- **Evaluation method:** Existing focused baseline before the change was 37 passing tests. After the change: 110 application tests, 10 evaluator tests, and 7 Product V2 harness tests passed; qualification had no hard failures and four pre-existing warnings; the existing integrated acceptance rerun remained `50/50 PASS` with latency evidence `8.841 ms` capture return / `134.743 ms` processing completion and its historical result hash unchanged. The new normal delayed-provider HTTP regression passed. Two authorized fresh-Home live normal-launch captures both returned immediately but both provider attempts failed before semantic state; no live Ask was issued and no semantic success was claimed.
- **Metric before:** Deterministic product integration was `50/50 PASS`, but normal live provider completion was not evidenced. The forensic Home showed Product V2 failed rows with automatic attempts observed up to 22 and Host status could omit V2 rows before lazy opening.
- **Metric after:** Deterministic normal-launch gate **PASS**; live normal-launch gate **PARTIAL**. The installed CLI is detected/authenticated as `codex-cli 0.150.0-alpha.12.2`; after removing the confirmed unsupported flag, the remaining live failure is a sanitized exit-code-1 warning-only result recorded in the runtime trajectory.
- **Regressions:** No V1, evaluator, frozen benchmark, integrated acceptance, deterministic Product V2, or UI regression remains. The live provider exit-code-1 condition is unresolved; the authorized two-capture limit was reached, so no further live retry was made.
- **Runtime/cost impact:** Deterministic checks used local fake providers and no provider tokens. Live smoke used two neutral captures, zero Ask calls, and no manual `product_process` processing. Credential values were never read, copied, exported, or persisted.
- **Decision:** **KEEP** the deterministic fixes. **REVISE** the provider adapter in a separately authorized follow-up before claiming the human-dogfood gate PASS.
- **Learning:** A high-scoring fixture acceptance can still miss normal-entrypoint/provider compatibility. The capture boundary, queue observability, and degraded UX need independent real-launch checks; operational failure must remain explicit when semantic state is absent.

## 2026-08-30 — Product V2 live provider adapter follow-up

- **Stage / experiment identifier:** Authorized post-freeze Product V2 provider integration follow-up; not a benchmark optimization and not E006.
- **Problem observed:** The prior normal-launch smoke returned two immediate captures, but both semantic provider attempts exited with code 1 while the visible diagnostic retained only Windows shell-snapshot and skill warnings.
- **Hypothesis:** The terminal JSONL failure event, rather than the incidental PowerShell warning, will identify an incompatible adapter flag or structured-output contract; correcting only the proven incompatibility should make authenticated semantic processing succeed.
- **What changed:** Inspected the real `codex exec` invocation and CLI help/features; confirmed standard ChatGPT login; ran six bounded disposable-directory controls; replaced the permissive Product V2 output schema with a strict typed schema; added terminal JSON failure parsing, sanitized tails, timeout status, and invocation-boundary diagnostics; added deterministic provider regressions. A mandated live Ask also exposed a standalone Polish `do` routing collision, so the smallest deterministic task/time-marker correction and regression were added without changing provider semantics.
- **Evaluation method:** Six provider-diagnostic tests, 115 application tests, 10 evaluator tests, 7 acceptance-harness tests, compileall, JavaScript syntax, 50-case visible Product V2 acceptance, benchmark structure check, contract smoke, qualification, and one fresh normal-launch live smoke with two captures and two Ask queries. No holdout material or benchmark optimization was used.
- **Metric before:** Live semantic processing `0/2` captures completed in the preceding dogfood smoke; the prior documented gate was PARTIAL. The first prescribed live keys Ask was not previously run.
- **Metric after:** Live semantic processing `2/2` captures completed on attempt 1 with zero retries; Memory and Attention contained the required evidence. The first live keys Ask was misrouted, while the second task Ask passed. The deterministic post-smoke router regression passes for both exact questions; no post-fix live Ask was authorized.
- **Regressions:** The final live gate remains PARTIAL pending a future bounded validation of the corrected keys Ask. The visible deterministic acceptance remains `50/50 PASS`; no frozen V1 or benchmark result changed.
- **Runtime/cost impact:** Six diagnostic model calls, two live Product V2 provider calls, and no token or dollar-cost access beyond the subscription CLI's normal operation. No retry spin occurred.
- **Decision:** **KEEP** the provider adapter/schema/diagnostic repair; **REVISE** the overall live gate after a separately authorized normal-launch Ask validation. Do not call this E006 or infer holdout performance.
- **Learning:** A warning-only stderr view can hide a terminal JSONL failure. Strict structured-output schemas must be validated against the installed CLI, and a successful provider path still needs a black-box language-routing check.

## 2026-08-30 — Product V2 provider follow-up scope correction

- **Stage / experiment identifier:** Scope correction for the authorized Product V2 provider integration follow-up; not a benchmark optimization and not E006.
- **Problem observed:** The live smoke exposed an unrelated deterministic Polish Ask-routing collision. A post-smoke router edit would have been too close to the task's explicit prohibition on semantic tuning from the prescribed wording.
- **Hypothesis:** Removing that unrelated edit and its exact-query regression will leave the provider-boundary evidence intact while keeping this branch within the authorized adapter scope.
- **What changed:** Removed the post-smoke deterministic Ask-router change and its application test. Retained the strict provider schema, terminal diagnostics, attachment boundary, live evidence, and honest PARTIAL gate.
- **Evaluation method:** Re-ran the provider suite, full application suite, evaluator suite, acceptance harness, compileall, JavaScript syntax, qualification, and benchmark structure checks. No additional live provider call, capture, or Ask was issued.
- **Metric before:** The provider follow-up commit contained 115 application tests, including the out-of-scope router regression; the real live keys Ask remained unsuccessful.
- **Metric after:** The provider follow-up contains 114 application tests, with the live result unchanged: 2/2 semantic captures succeeded, the task Ask passed, and the keys Ask remained unresolved.
- **Regressions:** The overall live gate remains PARTIAL; the unrelated Polish routing issue now requires separate product-scope authorization and validation.
- **Runtime/cost impact:** No live calls were added; provider and diagnostic call counts remain six diagnostic calls and two Product V2 provider calls.
- **Decision:** **KEEP** the provider-boundary repair; **REVISE** the overall gate and do not retain semantic routing tuning in this branch.
- **Learning:** Passing an offline regression for a prescribed query is not sufficient authorization to change unrelated product semantics during an adapter investigation.

## 2026-08-30 — Product V2 Ask routing generalization

- **Stage / experiment identifier:** Authorized post-freeze Product V2 Ask-routing generalization; not a benchmark-optimization experiment and not E006.
- **Problem observed:** The live Polish question `Gdzie są klucze do piwnicy?` was routed to unrelated children-pickup Attention because the old deterministic router treated the standalone preposition `do` as a task/time marker before generic Memory retrieval. Ordinary open-world questions also needed bounded multilingual retrieval without accidental substring matches.
- **Hypothesis:** An inspectable whole-word Ask plan, conservative cross-language term normalization, and scoped retrieval with current-state priority will remove the collision while preserving justified deterministic Attention/cost/change paths and enabling ordinary multi-fact questions.
- **What changed:** Added `app/ask_planner.py`; integrated plan-aware Product V2 retrieval and deterministic response handling; added inflection/alias normalization, same-entity expansion, ambiguity and location-list handling, current/history/relation scoping, and distinct `no_data`/`no_match` responses. Added the PWA no-data state and a 37-case multilingual routing suite with mocked HTTP E2E and provider-context isolation. The provider adapter was not modified.
- **Evaluation method:** Baseline focused Product V2 coverage was 16 passing tests and reproduced the live misroute. Final focused Ask/Product/UI coverage passed 32 tests; the dedicated routing suite passed 5 test methods over 37 cases; the full application suite passed 119 tests; evaluator tests passed 10; Product V2 acceptance-harness tests passed 7; compileall, JavaScript syntax, benchmark structure (`200` events / `4` checkpoints), and non-scored contract smoke passed. The visible integrated acceptance was run in a disposable directory and passed `50/50`, all seven reliability gates, and its latency probe.
- **Metric before:** No LQA/DSCR metric is applicable: this is explicitly post-freeze product generalization evidence. The observed live Ask result was an unrelated Attention answer with the wrong source reference.
- **Metric after:** Live normal-launch processing completed `4/4` captures on attempt 1 with `0` retries and `0` failures. All `6/6` authorized Ask requests returned useful `ready` results with correct source references and `0` Ask-time provider calls. The final integrated fixture latency was `8.493 ms` capture return / `134.276 ms` completion with a `120 ms` provider delay.
- **Regressions:** The first disposable integrated rerun exposed 20 Ask regressions from over-strict multi-term matching and future-advice classification; the general ranking/alias/planner corrections removed them and the final rerun was `50/50 PASS`. No application, evaluator, visible acceptance, provider-boundary, benchmark-structure, official baseline, or frozen V1 regression remains. No new visual browser review was performed.
- **Runtime/cost impact:** The deterministic Ask paths made the six live Ask calls provider-free. The four live captures used four normal local provider calls, one attempt each; no credential values were read, copied, exported, or persisted.
- **Decision:** **KEEP** for the explicitly authorized post-freeze Product V2 product scope. Do not use this result to tune the frozen baseline, claim holdout performance, or start an E006 optimization.
- **Learning:** Short lexical cues are unsafe intent selectors. Planning must be whole-word and confidence-bounded, while retrieval must preserve the winning entity and its relevant facts without leaking weaker collisions or unrelated Attention.

## Entry template

Use one entry per meaningful improvement:

```text
## YYYY-MM-DD — Short title

- Problem or failure observed:
- Change made:
- Evidence or evaluation impact:
- Follow-up:
```
