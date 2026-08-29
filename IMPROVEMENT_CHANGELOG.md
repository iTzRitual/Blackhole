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

## Entry template

Use one entry per meaningful improvement:

```text
## YYYY-MM-DD — Short title

- Problem or failure observed:
- Change made:
- Evidence or evaluation impact:
- Follow-up:
```
