# Architecture and product decisions

This is a lightweight decision record. Each entry captures the current design direction, why it exists, and what would justify revisiting it.

## Decision format

- **Status:** Proposed, accepted for design, or superseded
- **Context:** The problem or constraint
- **Decision:** The chosen direction
- **Consequences:** Benefits, costs, and risks
- **Revisit when:** Evidence that should trigger reconsideration

## D-001 — Zero-organization capture

- **Status:** Accepted for design
- **Context:** Classification at capture time creates cognitive friction and causes information loss.
- **Decision:** Provide a single capture path for supported source types. Classification is deferred to later processing.
- **Consequences:** The system must invest in extraction, linking, uncertainty handling, and review. Capture remains fast and inclusive.
- **Revisit when:** Evidence shows that a narrowly scoped capture choice materially improves trust or accuracy without adding meaningful friction.

## D-002 — Immutable raw sources

- **Status:** Accepted for design
- **Context:** Users and evaluators need to distinguish what was originally captured from what the system later inferred or corrected.
- **Decision:** Raw source records are append-only and immutable. Corrections and derived interpretations are separate records.
- **Consequences:** Storage and provenance are more important. Destructive cleanup cannot be the default.
- **Revisit when:** A formally versioned replacement mechanism can preserve complete evidence and auditability without mutating history.

## D-003 — Rebuildable derived state

- **Status:** Accepted for design
- **Context:** Prompts, models, extraction rules, and schemas will evolve.
- **Decision:** Derived state must be reproducible from immutable sources plus versioned transformations.
- **Consequences:** Every transformation needs identifiable inputs and versions. Ad hoc manual state changes require explicit provenance.
- **Revisit when:** A specific state category can be proven to require an irreducible manual component, while retaining a clear audit trail.

## D-004 — Explicit known, inferred, and unknown semantics

- **Status:** Accepted for design
- **Context:** Silent assumptions make personal and financial information unsafe.
- **Decision:** Represent direct evidence, inference, and unresolved absence as distinct semantic states.
- **Consequences:** Interfaces and metrics must avoid collapsing uncertainty into binary fields or numeric defaults.
- **Revisit when:** A narrower domain-specific representation improves clarity without losing the distinction.

## D-005 — Deterministic calculations outside the LLM

- **Status:** Accepted for design
- **Context:** Arithmetic, date math, comparisons, and aggregation must be repeatable and auditable.
- **Decision:** Code or SQL is the source of truth for deterministic calculations. The LLM may extract inputs, explain results, or propose classifications.
- **Consequences:** Calculation inputs need validation and provenance. Evaluation can separate extraction errors from calculation errors.
- **Revisit when:** Never for authoritative calculations; model assistance may expand only for non-authoritative explanation or hypothesis generation.

## D-006 — Explicit approval for consequential actions

- **Status:** Accepted for design
- **Context:** A wrong inference about a contract, payment, cancellation, or message can cause harm.
- **Decision:** The system may prepare a proposed action, but a user must explicitly approve a consequential external effect.
- **Consequences:** Approval state, preview, and audit records become first-class concerns.
- **Revisit when:** A narrowly scoped action has a documented safety case and an explicit product decision authorizes automation.

## D-007 — Evaluator-owned holdout ground truth

- **Status:** Accepted for design
- **Context:** An implementation agent that can read expected holdout outputs can optimize against or leak the benchmark.
- **Decision:** Holdout cases and expected outputs are evaluator-controlled. The implementation-facing repository contains placeholders only; real holdout material should be mounted or queried through an isolated evaluation boundary.
- **Consequences:** Evaluation tooling must separate candidate outputs from scoring data and must audit access.
- **Revisit when:** A different evaluation protocol provides equal or stronger protection against contamination.

## D-008 — Attention is a derived projection, not the source of truth

- **Status:** Accepted for design
- **Context:** Users need focus, but an attention list can become stale or hide its evidence.
- **Decision:** Attention items are rebuildable projections over facts, uncertainty, obligations, deadlines, conflicts, and approvals.
- **Consequences:** An item leaving the attention view does not delete the underlying evidence or state.
- **Revisit when:** User research demonstrates a durable need for a manually managed attention state, with provenance preserved.

## D-009 — Calibrate benchmark length before freezing Gate A

- **Status:** Historical proposal; superseded by D-019 after Gate A approval
- **Context:** A short timeline may fail to expose longitudinal state-maintenance errors in a strong long-context model, while an oversized timeline can measure context exhaustion rather than state quality.
- **Decision:** Before freezing the final benchmark length, run a separate non-scored calibration with 50-, 100-, 200-, and 400-event prefixes. Keep ten evolving storylines and prioritize state churn—updates, corrections, contradictions, supersession, cancellations, missing periods, duplicates, and ambiguity—over raw event count. Prefer the smallest approximately 150–200-event primary that shows repeatable degradation while remaining within usable context and the hackathon budget; keep a larger track secondary.
- **Consequences:** Calibration artifacts and a visible calibration-only oracle may be stored under `benchmark/calibration/`, but they are not final ground truth and cannot tune the baseline prompt. The selected model, tokenizer, context limit, correctness readout, runtime, and cost must be recorded before Gate A freeze.
- **Revisit when:** The fixed-prompt calibration shows no meaningful degradation through 400 events, the selected model/context changes, or the human owner approves a different primary/stress policy.

## D-010 — Blackhole framing and low-friction interaction

- **Status:** Accepted for design
- **Context:** Traditional productivity tools can turn capture into a second organizational task, especially for people with high executive-function friction, attention overload, forgetfulness, or low tolerance for setup.
- **Decision:** Use the product name **Blackhole** with the descriptor **“A zero-organization life inbox.”** The product principle is **CAPTURE NOW. ORGANIZE LATER.** Normal capture should be silent by default; interruption is reserved for useful attention items; observations should be factual and non-judgmental. ADHD may be referenced as an example of user need, without medical claims or treatment/diagnosis language.
- **Consequences:** The capture path should minimize classification questions and properties. Attention ranking, reminders, and advice must be evaluated for usefulness and tone rather than volume. Existing repository paths are not renamed for branding.
- **Revisit when:** User research shows that a different framing reduces capture friction without adding organizational overhead or making unsupported medical claims.

## D-011 — Isolate state maintenance from OCR in the primary benchmark

- **Status:** Proposed for Gate A review
- **Context:** The main hypothesis concerns longitudinal state maintenance, not the quality of an OCR or vision subsystem.
- **Decision:** Represent receipt, document, and image-derived modalities with synthetic text or normalized extracted content in the primary benchmark. Real uploads may be demonstrated separately; OCR/vision errors are not a primary benchmark confound.
- **Consequences:** Benchmark failures are more attributable to state changes, provenance, uncertainty, linking, temporal reconciliation, and projections. A separate modality slice can be added later without changing the primary metric.
- **Revisit when:** A validated modality pipeline becomes part of the product hypothesis and can be evaluated without masking state-maintenance behavior.

## D-012 — Use unweighted per-query LQA-0M with false-positive penalties

- **Status:** Proposed for Gate A review
- **Context:** Weighting critical assertions inside the primary average can make the headline score depend on arbitrary category weights, while unsupported assertions need an explicit penalty.
- **Decision:** For each fixed query, compute `TP`, `FP`, and `FN` over canonical assertions and use `TP / (TP + FP + FN)`. If both expected and produced assertion sets are empty, the query score is `1.0`; if only one is empty, the non-empty side creates false positives or false negatives and the score is `0.0`. LQA-0M is the unweighted arithmetic mean of all fixed query scores across primary checkpoints. Critical categories and safety violations are reported separately.
- **Consequences:** Hallucinated or unsupported claims lower the primary score. Precision, recall, and F1 remain useful diagnostics, but arbitrary 2:1 primary weights are removed.
- **Revisit when:** Human review identifies a deterministic, non-arbitrary aggregation rule that better reflects user risk without hiding false assertions.

## D-013 — Use DSCR for zero-maintenance correction burden

- **Status:** Proposed for Gate A review
- **Context:** A minimum-repair optimization such as MIR-90 is too expensive for the hackathon and can overstate repeated query failures caused by one root defect.
- **Decision:** Use **Distinct State Corrections Required (DSCR)**: after the zero-maintenance run, count distinct underlying state defects a human would need to correct. Multiple query failures caused by one defect count once. Report total DSCR, DSCR per 100 captured events, and correction categories. Do not equate DSCR with human minutes.
- **Consequences:** The secondary metric focuses on persistent state quality and is feasible to adjudicate. Exploratory wall-clock maintenance time may be reported separately but is not the contract metric.
- **Revisit when:** A later evaluation can measure actual maintenance effort reproducibly without replacing root-defect accounting.

## D-014 — Freeze a fair exact-model long-chat baseline

- **Status:** Proposed for Gate A review
- **Context:** The advanced system's structured state, deterministic tools, and retrieval are intentional experimental treatments; weakening the comparison baseline would invalidate the comparison.
- **Decision:** The baseline is one continuous general-purpose AI conversation receiving the same chronological captures and fixed checkpoint questions, with complete history whenever it fits and one frozen reasonable personal-life-admin prompt. Use the same exact semantic runtime model for baseline and advanced calls where practical, not merely the same model family. The baseline receives no hidden state, database, summary, retrieval, or specialized reconciliation tool.
- **Consequences:** Resource, token, latency, and cost differences must be reported transparently. The baseline prompt is frozen before calibration and cannot be tuned against individual calibration failures.
- **Revisit when:** The exact model is technically unavailable to both systems or a human-approved fairness protocol changes the treatment comparison.

## D-015 — Generate final benchmark state from a deterministic synthetic world

- **Status:** Proposed for Gate A review
- **Context:** Manually authoring and checking hundreds of final assertions is error-prone and burdens the human owner.
- **Decision:** Author final cases from explicit storyline/state-machine rules: canonical hidden world state → chronological user-facing events → deterministic checkpoint ground truth. Human review focuses on storyline semantics, transition rules, query definitions, subjective inference rules, critical transitions, and explicit unknown/contradiction cases. The implementation agent must not access protected holdout ground truth.
- **Consequences:** Final case generation is reproducible and easier to audit. Subjective expectations still require human adjudication, and generated development data must remain separate from evaluator-owned holdout material.
- **Revisit when:** A hand-authored case demonstrates a material behavior that cannot be represented transparently by the synthetic-world rules.

## D-016 — Subscription-first local CLI providers

- **Status:** Proposed for Gate A review
- **Context:** The hackathon MVP should let a user reuse an existing AI subscription without requiring Blackhole to receive a direct OpenAI or Anthropic API credential.
- **Decision:** Make an already-installed, already-authenticated local agent CLI the primary runtime path. The CLI owns authentication; Blackhole never requests, reads, copies, exports, or persists provider auth tokens. Use a small provider-neutral boundary with Codex CLI as the MVP provider and a minimal Claude Code adapter target.
- **Consequences:** Setup depends on provider detection and safe status reporting. Provider capability detection is authoritative, and unsupported model/reasoning combinations must fail visibly rather than silently falling back. Direct API integrations remain a future option, not an MVP dependency.
- **Revisit when:** A human-approved product scope requires a direct API provider or a supported CLI cannot provide the needed capability.

## D-017 — Persistent CLI session for the fair baseline

- **Status:** Proposed for Gate A review
- **Context:** The baseline should represent a person maintaining one long AI conversation, while the advanced system must demonstrate Blackhole-owned memory rather than provider-native memory.
- **Decision:** Use a real persistent Codex CLI session with resume when reliable. Supply the complete chronological history and fixed queries, with no Blackhole database, hidden summary, retrieval layer, or specialized reconciliation tool. Run it from an isolated temporary workspace with no expected outputs or calibration oracle.
- **Consequences:** Provider session behavior, token usage, latency, compaction, and resume semantics become part of the baseline record. The advanced design must use fresh or deliberately scoped provider calls around Blackhole-owned durable state instead of treating one long session as its primary memory.
- **Revisit when:** The provider cannot reliably resume, the exact runtime configuration changes, or the human owner approves a different fairness protocol.

## D-018 — Codex CLI runtime calibration and provisional length recommendation

- **Status:** Historical calibration decision; superseded by D-019 after Gate A approval
- **Context:** Gate A requires evidence about state churn while the history remains available, not a benchmark inflated to force context exhaustion.
- **Decision:** Run the frozen `baseline-v1` prompt and fixed calibration query bundle through Codex CLI `0.150.0-alpha.12.2` using `gpt-5.6-luna` with `max` reasoning at 50, 100, 200, and 400 events. All four sessions completed with no context-warning signal. The provisional recommendation is a 200-event realistic primary and a 400-event secondary stress track; do not run the optional 800-event extension because 400 was not practically comfortable and showed additional state errors.
- **Consequences:** The result is non-scored calibration evidence, not final benchmark approval. The fixed configuration and outputs are recorded in the runtime trajectory and calibration report. The local CLI did not expose a documented context limit, so fit is reported empirically as accepted-without-warning rather than as a claimed percentage. A single run per size does not establish repeatability.
- **Revisit when:** Human review changes the provider/model, repeated calibration changes the degradation conclusion, or a provider exposes a reliable documented context and cost model.

## D-019 — Freeze the 200-event Gate A development track

- **Status:** Accepted for Gate A benchmark execution
- **Context:** Calibration showed non-monotonic correctness across 50, 100, 200, and 400 events, while 400-event execution was materially slower. The goal is state churn while history remains usable, not context exhaustion.
- **Decision:** Freeze one realistic 200-event development scenario with checkpoints at 50, 100, 150, and 200. Use ten interleaved evolving storylines with repeated changes, corrections, contradictions, supersession, cancellations, missing periods, duplicates, and ambiguity. Keep 400 events as an optional secondary stress track; do not run or design an 800-event track in Gate A.
- **Consequences:** The primary run is practical enough for repeated hackathon evaluation and still exercises longitudinal state maintenance. A single synthetic scenario has limited statistical power, so results must not be generalized beyond the benchmark.
- **Revisit when:** Human review identifies a contract defect or a later authorized calibration materially changes the runtime/cost evidence.

## D-020 — Freeze checkpoint query isolation

- **Status:** Accepted for Gate A benchmark execution
- **Context:** Asking a query in the continuing ingestion conversation can leak an answer into later state maintenance and make checkpoint scores incomparable.
- **Decision:** Maintain one canonical persistent ingestion session. At each checkpoint, fork the canonical session, ask the fixed query bundle only in that fork, capture the result, and never resume the fork. The current Codex harness uses the atomic native `fork <parent> <prompt>` operation. Capture transport uses one chronological batch per checkpoint segment; batching is not a summary or retrieval layer.
- **Consequences:** Checkpoint answers are isolated read-only probes, while the parent retains only the chronological captures. Provider fork/resume behavior, fork IDs, usage, and discarded-child status are recorded in the runtime trajectory.
- **Revisit when:** The provider loses native fork support or a human-approved equivalent isolation mechanism is required.

## D-021 — Freeze the development response and scoring contract

- **Status:** Accepted for Gate A benchmark execution
- **Context:** A reproducible benchmark needs deterministic comparison of state, provenance, uncertainty, relations, and safety behavior.
- **Decision:** Use contract `1.0-gate-a-dev` with 12 fixed query IDs, typed assertions containing `state_key`, optional `value`, `knowledge_status`, `source_refs`, and optional `unknown_reason`/`confirmation_ref`. Score exact canonical assertion sets with unweighted per-query LQA-0M, explicit empty-set rules, secondary category/status metrics, DSCR, schema diagnostics, and a hard safety gate. Define `duplicate_event_count` as duplicate captures excluding originals; keep `duplicate_group_count` separate.
- **Consequences:** Results are deterministic and auditable, but a candidate that invents a different assertion vocabulary is penalized rather than semantically remapped. Development expected output is visible for local scorer work; holdout expected output remains evaluator-owned.
- **Revisit when:** Human review finds a contract ambiguity before holdout construction. Do not change expected outputs merely because an implementation disagrees.

## D-022 — Record the Codex baseline as a benchmark treatment (historical)

- **Status:** Historical Gate A execution; invalidated as an official semantic baseline measure
- **Context:** The benchmark needs a fair, reproducible comparator before advanced application work begins.
- **Decision:** Use Codex CLI `0.150.0-alpha.12.2`, model `gpt-5.6-luna`, reasoning effort `max`, existing subscription authentication, a fresh empty workspace, read-only execution, the frozen `baseline-v1` prompt, one canonical session, and isolated checkpoint forks. The baseline receives no Blackhole state, database, expected output, evaluator internals, or special tools.
- **Consequences:** The recorded run completed all four checkpoints but produced a deterministic LQA-0M of 0.0000 because its assertion keys/shapes did not match the frozen contract. It incurred approximately 2,513 seconds of query-fork runtime and reported no safety or source-integrity failure. The result is preserved as invalid-contract evidence and is a Gate B analysis item, not a reason to rewrite ground truth.
- **Revisit when:** A future human-approved baseline protocol changes the public response contract or provider configuration. Any rerun must be versioned and must not overwrite this result silently.

## D-023 — Repair the public baseline response boundary

- **Status:** Validated for Gate B execution; supersedes the candidate-facing response boundary in D-021
- **Context:** The Gate A v0 run used grouped semantic summaries and evaluator-oriented dotted `state_key` values, while the scorer required a different assertion identity. The resulting `LQA-0M=0.0000` had no true positives and also contained malformed `unknown` assertions with values, so it was not a valid semantic baseline.
- **Decision:** Preserve v0 as invalid-contract evidence and freeze `response-contract-v2`. Candidate assertions use public `subject`, `predicate`, `knowledge_status`, `source_refs`, and value/unknown fields. The deterministic scorer canonicalizes only public ontology aliases and declared value formats; it rejects candidate `state_key` fields. Source references remain required and validated, but provenance is reported separately from primary semantic matching so extra valid evidence does not mask state quality. Duplicate-event wording explicitly excludes each original event.
- **Consequences:** A reasonable general-purpose baseline can be scored without access to evaluator-internal IDs or expected values. Development expected output may retain internal keys solely for DSCR clustering. A non-scored smoke fixture tests raw parsing through canonicalization and evaluation. The substantive `baseline-v1` prompt remains unchanged; only the runner/schema instruction is versioned. The corrected 200-event run is recorded separately and is schema-valid.
- **Revisit when:** A human review finds a public ontology or normalization ambiguity, a future benchmark needs a new assertion type, or the provider configuration changes. Never repair a semantic disagreement by changing expected ground truth without human review.

## D-024 — Authorize advanced Blackhole experimentation after valid Gate B

- **Status:** Accepted for the next project phase
- **Context:** Gate A is frozen and the Gate B response-contract repair has produced a valid official `baseline-v1` result. The project needs to move from benchmark/baseline work to product experimentation without reopening completed gates.
- **Decision:** Begin scoped advanced Blackhole application experimentation. Keep the 200-event Gate A benchmark, 50 / 100 / 150 / 200 checkpoints, `response-contract-v2`, deterministic evaluator, official `baseline-v1` result, and calibration evidence frozen. Do not expose holdout ground truth or add production infrastructure or a Claude adapter under this decision.
- **Consequences:** Advanced experiments can test Blackhole-owned state, reconciliation, retrieval, and deterministic projections against the frozen public contract. Each meaningful experiment must follow the trajectory and experiment protocols and preserve the fair baseline comparison.
- **Revisit when:** Human review changes the benchmark contract, baseline protocol, holdout boundary, or the authorized application scope.

## D-025 — Keep Experiment 001's append-only state projection slice

- **Status:** Accepted for the Experiment 001 milestone; remains foundational to D-030
- **Context:** After Gate B, the first authorized application experiment needed to test whether Blackhole-owned durable state improves the frozen public benchmark without changing benchmark facts, the response contract, or the fair baseline.
- **Decision:** Keep the smallest tested slice: SQLite-backed immutable raw captures; structured observations and relationships with known/inferred/unknown status; explicit provenance and history; deterministic rebuildable current-state projection; and deterministic, query-scoped public response projections. Use fresh scoped Codex CLI extraction calls only to propose structured interpretations. Keep financial arithmetic, date windows, duplicate grouping, and response shaping in code. Preserve replayable semantic outputs so projection revisions are comparable without new provider calls.
- **Consequences:** Experiment 001's final public development replay scored `LQA-0M=0.7492295899` with `DSCR=72`, while the official baseline remains unchanged at `0.3014914553` / `277`. The approach preserves raw evidence and makes state rebuildable, but fresh semantic extraction remains costly and relation-detail recall is incomplete. This is an experimental application slice, not a production architecture or a new benchmark treatment.
- **Revisit when:** A new human-authorized experiment tests relation reconciliation, provider runtime, or a broader application boundary. Any change must preserve Gate A, `response-contract-v2`, official `baseline-v1`, calibration evidence, and holdout isolation.

## D-026 — Keep ontology-kind-driven response projections

- **Status:** Accepted for the current advanced experiment slice
- **Context:** An audit of Experiment 001 found literal benchmark subject IDs and brand-name query branches in the deterministic response projector. The implementation therefore did not yet meet the requirement that its state-maintenance mechanism be generic across Blackhole entities and state transitions.
- **Decision:** Select subjects by the kind declared in the public response contract and route queries by generic query-family vocabulary. Use generic observation predicates and capture structure for relation filtering; exclude entity-link-only endpoints from duplicate/change capture projections. Do not encode benchmark entity identifiers, expected values, or named storylines in application logic.
- **Consequences:** The repaired projector supports multiple subjects per public kind and preserves the E001 full replay exactly: `LQA-0M=0.7492295899`, `DSCR=72`, with the same checkpoint scores and totals. A first overly broad relation rule was rejected after it counted entity-link chains as duplicates. The official baseline, benchmark contract, expected output, and evaluator remain unchanged.
- **Revisit when:** A human-authorized relation-reconciliation experiment, new public ontology, or broader application boundary requires different generic projection semantics. Any revision must preserve Gate A, `response-contract-v2`, official `baseline-v1`, calibration evidence, and holdout isolation.

## D-027 — Defer relation-detail extraction work

- **Status:** Superseded by D-029 for the current advanced experiment phase
- **Context:** A read-only audit compared the recorded E001 semantic extraction and SQLite relationship state with the public development relation expectations. The state contains substantial relation evidence, but several missing duplicate/change details are absent or have different target edges; they cannot all be recovered by deterministic projection alone.
- **Decision:** Relation detail requires richer semantic extraction and is deferred. Do not launch another expensive provider extraction run for score pursuit. Continue with product/demo, reproducibility, and submission work using the validated generic projector.
- **Consequences:** At the time of this decision, no Experiment 003 was launched, and no benchmark, expected output, response contract, evaluator, baseline, or calibration artifact changed. Relation-detail recall remained a documented limitation until a separately authorized experiment was defined.
- **Revisit when:** A separately authorized extraction-quality experiment can define a new hypothesis, preserve the frozen benchmark and baseline, and fit the remaining submission schedule.

## D-028 — Keep the hackathon demo local and deterministic

- **Status:** Accepted for the final product/submission phase
- **Context:** The validated SQLite state slice needed a user-visible demonstration without introducing production infrastructure, a second persistence boundary, or hidden provider behavior.
- **Decision:** Build a small stdlib local web demo over the existing SQLite state boundary. Use committed synthetic captures and structured observations for the seeded demonstration, expose capture/state/query/reset routes, and keep newly captured text raw-only with pending semantic status. Provider availability is discovery-only in the UI; semantic extraction remains a separately invoked subscription-first CLI workflow.
- **Consequences:** Judges can run the product locally with a reset/seed command and inspect attention, memory, uncertainty, history, duplicate, and approval projections. The demo is not a production service, does not classify captures synchronously, and performs no consequential action.
- **Revisit when:** Production deployment, multi-user isolation, document/OCR ingestion, or live semantic processing is explicitly authorized as a separate scope.

## D-029 — Keep bounded raw-capture relation reconciliation

- **Status:** Accepted for the Experiment 003 milestone; superseded as the current reference by D-030
- **Context:** Experiment 002's kept projector still had a measured relation-reconciliation weakness. The public audit showed that explicit supersession rows were mostly present, but receipt lineage, duplicate/change detail, and some target choices required earlier raw capture content that was not included in the structured extraction context.
- **Decision:** Keep a generic, deterministic relation-recovery pass followed by bounded raw-capture candidate retrieval. Use only append-only SQLite inputs, the first stable source identifier, at most four earlier candidates, and a conservative lineage rule. Replace only the derived relationship rows for a source when the candidate set is unambiguous; preserve raw events and observations unchanged. Do not add a provider resolver when the deterministic retrieval treatment already meets the experiment threshold.
- **Consequences:** The final public replay improved from `LQA-0M=0.7492295899` / `DSCR=72` to `LQA-0M=0.8157180034` / `DSCR=45`; relation reconciliation improved from `0.3169014085` to `0.6696428571`. No benchmark, expected output, response contract, evaluator, official baseline, or calibration artifact changed. Retrieval evidence is recorded per checkpoint with raw candidate content and metadata; no provider calls or tokens were used. This remains an application experiment, not a production ingestion or holdout result.
- **Revisit when:** A genericity regression appears, a future experiment needs richer cross-entity resolution, a provider-assisted resolver is explicitly authorized, or the human owner changes the frozen benchmark or holdout boundary.

## D-030 — Keep selective raw-source completeness treatment

- **Status:** Accepted for the current advanced experiment milestone
- **Context:** Experiment 003 left a small set of defects where the raw capture explicitly contained a structural fact or lifecycle cue that was absent from same-capture observations. Other remaining defects were relation, semantic-role, projection, or non-recoverable-value errors and were outside this experiment.
- **Decision:** Add a generic structural evidence scanner and conservative same-capture coverage detector. Apply deterministic derived completions only for unambiguous dates, identifiers, value-shape fields, and lifecycle states. Keep a versioned one-capture semantic verifier available for residual gaps, but do not invoke it when the deterministic treatment already meets the experiment threshold.
- **Consequences:** The full public replay improved from `LQA-0M=0.8157180034` / `DSCR=45` to `LQA-0M=0.8630770101` / `DSCR=41`; temporal-history and current-state metrics improved, with no material relation, financial, duplicate/change, entity-resolution, schema, safety, or source-integrity regression. Six captures were repaired, eight observations were added including one correction, and provider usage was zero. Raw sources, the frozen benchmark, response contract, evaluator, official baseline, calibration evidence, and holdout boundary remain unchanged.
- **Revisit when:** A later human-authorized experiment needs broader semantic completion, provider verification, or a different extraction/state boundary. Do not use the verifier or this treatment to infer holdout performance.

## D-031 — Keep duplicate-aware evidence components at the projection boundary

- **Status:** Accepted for the current advanced experiment milestone
- **Context:** The E004 projection discarded observations from true duplicate-source captures before current-state reconciliation. A cutoff-aware public audit identified three meaningful losses: a subscription renewal date, a contract expiry date, and an approval state. Treating every duplicate capture as a new occurrence would instead risk double-counting and provenance noise.
- **Decision:** Build deterministic, undirected components only from `exact_duplicate`, `normalized_duplicate`, and `duplicate` relationships. Select the earliest event by sequence as canonical and persist every component member ID in rebuildable derived metadata. Consolidate observations by subject and predicate: merge identical semantic evidence without increasing occurrence counts, retain additional predicates, preserve unresolved value conflicts as unknown, follow only unambiguous terminal correction/supersession chains, and never implicitly upgrade unknown or inferred evidence. Keep similar captures, meaningful changes, contradictions, and task reassignment outside duplicate-component construction.
- **Consequences:** The opt-in `experiment-005-duplicate-evidence-projection-v1` mode recovers valid evidence without mutating raw events or changing the frozen benchmark. The public replay formed 24 components across 72 events, recovered 51 observations from duplicate-source captures, and consolidated 36 identical observations. It improved LQA-0M from `0.8630770101` to `0.8695006212` and DSCR from `41` to `40`; financial, entity, duplicate/change, relation, unknown-state, schema, safety, and source-integrity guards did not regress. No provider call was required.
- **Revisit when:** Post-freeze generalization exposes a false duplicate component, a domain requires a different occurrence/count policy, or a human-approved benchmark or state-boundary change is proposed. Experiment 005 is the last benchmark-optimization experiment for this frozen development track; do not infer holdout performance from this result.

## D-032 — Separate cheap capture from deferred semantic ingestion

- **Status:** Accepted for the backend/product-runtime milestone
- **Context:** Blackhole's product promise is to reduce capture-time cognitive friction. The kept semantic extraction, completeness, relation-recovery, duplicate-evidence, and projection components were first coordinated inside benchmark/replay flows, while the local demo only provided a raw capture helper.
- **Decision:** Introduce one generic `IngestionEngine` boundary. `capture()` validates and appends immutable raw input plus a separate derived `processing_state=pending` row, then returns without provider work or semantic projection. `process_pending()` handles bounded chronological batches through the existing public-contract normalization, E004 deterministic completeness, E003 relation recovery, E005 duplicate-aware projection, and rebuildable `StateStore`. Expose `retry_failed()`, `processing_status()`, and `ensure_state_fresh()` for later callers, plus a UI-independent `python -m app.process_pending` command.
- **Consequences:** The user-facing loop is `CAPTURE NOW. UNDERSTAND LATER.` Provider authentication remains external and a missing provider does not block capture. Processing failures are explicit and retryable; later events do not bypass earlier failures. Stable event-scoped fingerprints and processed status make repeated processing idempotent. The deterministic fake-provider integration suite covers correction, unknown, duplicate, safety, failure/retry, and no-provider capture. No benchmark cases, expected output, evaluator, official baseline, response contract, UI assets, background scheduler, or Claude adapter changed.
- **Revisit when:** A human-authorized product scope adds scheduling, multi-user execution, additional source transports, provider capability changes, or selective Ask-time processing. Any revision must preserve the raw/derived boundary, approval boundary, and frozen benchmark evidence.

## D-033 — Make Blackhole Host the local ownership boundary

- **Status:** Accepted for the backend/product-runtime milestone
- **Context:** Deferred ingestion provided the reusable capture and processing pipeline, but future PWA, mobile, and desktop clients need a single trusted local owner for durable state, runtime configuration, provider access, and processing lifecycle. Treating Codex CLI as the host would couple product state to provider sessions and would make future transport security ambiguous.
- **Decision:** Add a small `HostRuntime` facade that owns Blackhole Home, validated non-sensitive runtime configuration, `StateStore`, the existing `IngestionEngine`, safe provider readiness, and processing operations. Codex CLI remains an optional subscription-first semantic provider; it is never durable Blackhole memory. Use `BLACKHOLE_HOME` with a `~/.blackhole/` default, initialize SQLite without a provider, and expose only domain operations. The host may be wrapped by a future transport, but it must not expose generic shell/process execution or perform consequential actions without approval.
- **Consequences:** Capture works offline and before provider setup. Provider absence or failure is visible as retryable derived processing status while raw evidence remains intact. Status/doctor can use cheap PATH/version/login-status checks without semantic inference or credential-file access. Product model/reasoning preferences are versioned separately from frozen benchmark constants. The main test suite uses temporary homes and fake providers.
- **Revisit when:** The PWA worktree is ready for a separately authorized transport milestone, a new provider requires a capability contract, or multi-user/remote deployment changes the trust boundary. HTTP, pairing, networking, and production infrastructure are intentionally outside this decision.

## D-034 — Integrate the PWA through a narrow Host-owned local transport

- **Status:** Accepted for the product-runtime integration milestone
- **Context:** The approved mobile PWA needed a real local owner for Capture, Memory, Attention, and Ask. The earlier web surface was a seeded demo transport that read a separate database and never represented deferred semantic processing.
- **Decision:** Serve the PWA and a small same-origin domain API from `app/web_app.py`, but keep all persistence, provider selection, freshness, normalization, deterministic projection, and retry behavior inside `HostRuntime`. Capture is raw-only and immediate. Ask calls `ensure_state_fresh()` and then a database-free deterministic QueryService over the Host snapshot. Use a generic runtime contract separate from frozen benchmark `response-contract-v2`, so ordinary product entities are not benchmark-coupled. Open a request-scoped HostRuntime and serialize operations at the server boundary for SQLite safety.
- **Consequences:** The visible product flow is `capture -> Saved. -> pending -> Ask -> process -> rebuild -> answer`. A missing provider cannot block capture and produces a safe `state_not_fresh` response when pending work exists; existing state remains queryable with no pending work. The PWA does not expose provider reasoning or wait for a provider during capture. The old HTTP demo reset/auto-seed behavior is not part of normal Host mode, and the PWA no longer offers a destructive demo reset action.
- **Security boundary:** Bind loopback by default. Require explicit `--trusted-lan-demo` for non-loopback use and warn that it has no device authentication and is only for a trusted private network. Do not add shell routes, arbitrary Codex execution, credentials, pairing, tokens, mDNS, TLS, tunnels, cloud relay, or public-Internet support. The service worker never caches dynamic API responses.
- **Revisit when:** A human-approved product scope adds a different transport, multi-user access, device authentication, or remote deployment. Any such change must preserve the Host ownership, immutable raw source, rebuildable derived state, approval, and benchmark-access boundaries.

## D-035 — Freeze the consolidated implementation boundary

- **Status:** Accepted for the implementation-freeze milestone
- **Context:** The approved Host/PWA integration and submission-hardening evidence were reviewed in their isolated worktrees and consolidated on `master`. Gate A, Gate B's corrected response contract, the official baseline, calibration evidence, and the kept E005 replay were already frozen and must not be reopened by final packaging work.
- **Decision:** Freeze the consolidated application/runtime boundary and its validation evidence at the recorded implementation-freeze reference. Preserve the source branches and worktrees for auditability. Allow only reproducible submission preparation and separately authorized post-freeze generalization; do not use post-freeze generalization results to tune the frozen runtime.
- **Consequences:** The implementation-freeze record, tag, protected artifact hashes, deterministic checks, and one bounded neutral real smoke are the authoritative consolidation evidence. No new benchmark case, evaluator behavior, baseline run, benchmark optimization, E006 experiment, production infrastructure, pairing system, or UI redesign is part of this milestone.
- **Revisit when:** The project owner explicitly authorizes a new product scope, benchmark/evaluator revision, or post-freeze experiment with a new trajectory and reproducible evidence. Any revision must preserve the immutable raw-source boundary, rebuildable derived state, unknown semantics, approval boundary, and holdout isolation.

## D-036 — Build Product V2 as an isolated open-world runtime

- **Status:** Accepted for the explicitly authorized post-evaluation Product V2 foundation
- **Context:** The evaluated V1 application boundary is frozen, while the product still needs a capture-first runtime that can operate on ordinary open-world personal evidence, durable attachments, background semantic processing, deterministic Attention, and natural Ask retrieval.
- **Decision:** Implement Product V2 in the isolated `product/v2-runtime` worktree and branch with a separate `blackhole-v2.db`. Keep immutable source events and content-addressed attachment blobs separate from rebuildable processing state, memory facts, relations, Attention candidates, projections, and append-only retractions. Use a chronological lease/retry worker with atomic semantic commit, explicit known/inferred/unknown values, generic entities and concepts, deterministic time/arithmetic paths, bounded retrieval, and a POST-only semantic Ask route. Use the already-installed local Codex CLI through an ephemeral, read-only provider adapter when bounded synthesis is needed; never access provider tokens or make consequential actions.
- **Consequences:** Text-only, attachment-only, and combined capture return immediately and remain durable if the provider is missing. Stale workers can be recovered, failures can be retried, raw evidence remains available, and migration from the legacy V1 Home is read-only. Product V2 can evolve without changing the frozen V1 database, benchmark, evaluator, baseline evidence, calibration evidence, or frozen runtime behavior. The initial scope is backend/API and deterministic tests; it does not claim a V2 UI, production hosting, OCR, a Claude adapter, remote access, or holdout evaluation.
- **Revisit when:** A separately authorized product scope changes storage, provider, transport, multi-user, attachment interpretation, or action-approval requirements. Any revision must preserve the frozen V1 boundary, raw/derived separation, provenance, unknown semantics, and holdout isolation.

## D-037 — Keep Product V2 UI integration behind a thin frontend contract

- **Status:** Accepted for the isolated post-evaluation Product V2 UI scope
- **Context:** The mobile-first redesign needs human-oriented Capture, Attention, Memory, and Ask views, while the current Host API remains a text-first compatibility surface and does not yet expose binary attachment transport or capture retraction. The implementation-freeze runtime and frozen V1 benchmark must remain untouched.
- **Decision:** Keep the V2 web client behind a small adapter with `getState()`, `capture({text?, attachment?})`, `retractCapture(captureId)`, and `ask(question)` operations. Normalize legacy or future Host responses at the adapter boundary into human-facing projections; do not render raw assertion fields as the primary product surface. Treat attachment-only capture and retraction as explicit Host capabilities: the UI may exercise them through deterministic fixtures, while the current Host compatibility path must report its limits truthfully. Retraction represents a derived-state action and must not imply physical deletion of immutable evidence.
- **Consequences:** The UI can be tested without a live provider and can evolve toward the Host contract without coupling presentation to storage or ontology internals. The isolated branch contains no backend, runtime, evaluator, benchmark, holdout, or baseline changes. Until the Host supports the contract, real attachment-only save and Undo require integration work described in `docs/PRODUCT_V2_UI_CONTRACT.md`.
- **Revisit when:** The project owner authorizes the Host transport capability work, a new source transport is approved, or the post-freeze product boundary changes. Any revision must preserve raw evidence, rebuildable derived state, unknown semantics, approval, provenance, and frozen benchmark boundaries.

## D-038 — Keep Product V2 dogfood acceptance independent and black-box

- **Status:** Accepted for the Product V2 dogfood acceptance milestone
- **Context:** The frozen V1 development benchmark improved the scoped runtime, while real dogfooding exposed product usability and trust risks that benchmark-shaped cases could miss. A second set of concurrent Product V2 runtime and UI worktrees is being developed separately, so acceptance criteria must not be reverse-engineered from their in-progress implementation.
- **Decision:** Maintain a visible Product V2 dogfood acceptance suite under `product_acceptance/` with realistic English and Polish ordinary-life cases, small safe attachment fixtures, a user-visible case schema, a logical black-box Host adapter, a deterministic provider-free mock, product-level quality gates, and a 15–25 minute human protocol. Judge outcomes by durable capture, useful evidence-backed retrieval, correct attention, explicit uncertainty, correction/Undo behavior, attachment integrity, and restart/retry reliability. Mark absent adapter surfaces `NOT TESTED`; never invent a hidden oracle, tune a prompt against these cases, or collapse trust gates into historical V1 LQA.
- **Consequences:** The suite can be committed and run independently before the integrated Product V2 Host exposes every route. Current-base compatibility gaps remain visible as `PARTIAL`/`NOT TESTED`, while transport and reliability regressions can fail deterministically without live provider calls. The cases are development acceptance tests and cannot support an unseen generalization claim. The app, runtime/UI worktrees, V1 benchmark artifacts, evaluator formulas, and holdout material remain outside this milestone.
- **Revisit when:** The integrated Product V2 Host publishes its stable black-box contract, a separate unseen validation freeze is authorized, or the project owner changes the acceptance boundary. Any revision must preserve source immutability, rebuildable derived state, unknown semantics, approval boundaries, and holdout isolation.

## D-039 — Reconcile the Product V2 PWA with the Host contract

- **Status:** Accepted for the explicitly authorized Product V2 integration milestone
- **Context:** The runtime, UI, and dogfood branches were developed independently and exposed a mismatch around V2 routes, binary attachment transport, asynchronous processing feedback, Attention lifecycle state, and semantic Undo. The PWA needed a real Host-owned path without reopening the frozen V1 surface.
- **Decision:** Use the V2 same-origin routes as the PWA's only normal client contract. Send attachment bytes as bounded base64 with filename/MIME metadata, return a durable capture before semantic processing completes, poll explicit V2 processing state, render lifecycle-aware Attention and open-world Memory projections, use POST-only Ask, and represent Undo as an append-only semantic retraction. Retain the historical V1-compatible routes for compatibility, but do not use them from the current PWA.
- **Consequences:** Text, attachment-only, and combined capture work through one Host-owned contract; provider failure remains visible and retryable; exact attachment bytes and provenance remain auditable; deterministic date/arithmetic paths remain authoritative; and fixture mode can support UI checks without becoming benchmark data. The isolated integration acceptance run passed all 50 public product cases and all reliability gates. No V1 benchmark, official baseline, evaluator, holdout material, or provider token was changed or accessed.
- **Revisit when:** A human-approved transport, multi-user, remote-access, attachment-interpretation, or post-freeze generalization scope changes the contract. Any revision must preserve raw evidence, rebuildable derived state, unknown semantics, approval boundaries, provenance, and holdout isolation.

## D-040 — Make normal Product V2 dogfood state single-owner and bounded

- **Status:** Accepted for the explicitly authorized human-dogfood repair; live-provider completion remains unresolved.
- **Context:** Human dogfooding exposed three trust failures that deterministic fixture acceptance did not cover: Host status could report the legacy queue before Product V2 was opened, the normal web entry point did not guarantee a managed Product V2 worker, and provider failures could be retried indefinitely. The installed Codex CLI also rejected a flag used by the Product V2 adapter.
- **Decision:** Resolve Product V2 storage through one Home-scoped helper, have normal `HostServer` construction start one managed Product V2 worker, cap automatic retries at five attempts with durable 1/2/4/8-second delays, require explicit retry after the cap, and retain only bounded sanitized provider diagnostics. Return typed pending/failed Ask results and visible saved-but-processing UI state. Version the PWA shell and update controlled service-worker clients without caching dynamic API responses. Keep explicit fixture and worker-disabled integration modes available for deterministic acceptance.
- **Consequences:** Normal Host and Product status agree on `<BLACKHOLE_HOME>/blackhole-v2.db`; raw capture remains immediate and durable; a failed provider cannot masquerade as empty memory or spin a hot retry loop; and the browser can converge from an older shell. The deterministic normal-launch regression passes. The authorized live smoke still returns CLI exit code 1 with sanitized warning output, so the overall human-dogfood gate is PARTIAL and the provider adapter requires a separately authorized follow-up. No V1 benchmark/evaluator/baseline or holdout material changed.
- **Revisit when:** The remaining live CLI exit-code-1 condition is diagnosed with a new bounded smoke authorization, or a human-approved provider/runtime change alters the execution contract. Preserve the raw/derived boundary, approval boundary, provider-token prohibition, and frozen benchmark evidence.

## D-041 — Keep Product V2 Codex structured output strict and diagnosable

- **Status:** Accepted for the explicitly authorized Product V2 provider-fix follow-up; overall live dogfood validation remains partial because of an unrelated Ask-routing finding.
- **Context:** The normal Product V2 worker used `codex exec --json --output-schema`, but the generated schema was permissive and incomplete for the installed Codex structured-output contract. The CLI returned exit code 1 with a terminal `turn.failed` / `invalid_json_schema` event while stderr also contained a known Windows PowerShell shell-snapshot warning. The warning was present in successful controls and was not causal.
- **Decision:** Keep the subscription-first local Codex boundary with standard external ChatGPT authentication, `--ephemeral`, JSONL output, a read-only sandbox, no `--ignore-user-config`, no global configuration change, and no shell-snapshot suppression. Generate a strict schema with typed array items, closed object properties, required fields, and nullable optional values. Parse and retain a bounded sanitized terminal JSON event, stdout/stderr tails, return code, and timeout state; never treat a non-zero exit as success.
- **Consequences:** The real normal worker processed both authorized text captures on the first attempt, producing source-linked Memory and Attention state without retry spin. The adapter remains a semantic interpreter boundary and does not receive workspace-write or dangerous sandbox access. Deterministic regressions cover argv construction, authentication-related flags, strict schema shape, warning-vs-fatal distinction, terminal error parsing, structured output, timeout behavior, and redaction. The unrelated Ask-routing finding remains outside this provider-only change.
- **Revisit when:** A future installed CLI changes its structured-output contract or a separately authorized provider capability adds a safer attachment/document boundary. Preserve external credential ownership, non-zero failure semantics, raw/derived separation, and frozen benchmark boundaries.

## D-042 — Route Product V2 Ask through an inspectable plan and scoped retrieval

- **Status:** Accepted for the explicitly authorized post-freeze Product V2 Ask-routing scope
- **Context:** Normal live dogfooding showed that a Polish basement-key question could be diverted to unrelated Attention because the standalone preposition `do` was treated as a task/time marker before matching Memory was considered. Generic retrieval also needed to handle ordinary English/Polish inflections, multiple facts about one entity, ambiguity, corrections, unknowns, and empty/no-match states without coupling to the frozen V1 query bundle.
- **Decision:** Add a small deterministic `AskPlan` boundary with whole-word tokenization, accent folding, conservative cross-language aliases, and high-confidence intents for Attention, costs, changes, and last mentions. Use that plan to rank current facts first, expand only winning entities, retain tied candidates for ambiguity, and add matching history, relations, Attention, and source metadata only when relevant. Keep future recommendation questions on generic Memory, invoke bounded provider synthesis only when justified, and return distinct `no_data`, `no_match`, `processing`, and `processing_failed` states. Never route on a standalone short substring or a product-specific phrase.
- **Consequences:** `POST /api/v2/ask` can answer open-world questions such as locations, preferences, conditions, documents, and ordinary observations while preserving provenance, current-versus-history semantics, unknown values, and retractions. Deterministic arithmetic/date/Attention behavior remains authoritative. The provider sees selected context rather than raw capture history or unrelated Attention. The visible 50-case acceptance remains `50/50 PASS`, the dedicated routing corpus has 37 cases, and the authorized live smoke passed all four captures and six Ask requests. This is product generalization evidence, not a benchmark result or E006.
- **Revisit when:** A human-approved semantic retrieval boundary, provider capability, transport contract, or unseen validation freeze changes the product scope. Any revision must preserve immutable raw sources, rebuildable derived state, explicit unknowns, approval boundaries, and holdout isolation.

## D-043 — Make Product V2 memory language-invariant at the semantic boundary

- **Status:** Accepted for the explicitly authorized post-freeze Product V2 language-invariance scope
- **Context:** The D-042 lexical Ask fast paths correctly protected the Polish `do` collision and ordinary English/Polish retrieval, but an unfamiliar-language question could still become `no_match` before a semantic provider saw any structured memory. Provider-selected entity labels also needed an explicit cross-language identity contract.
- **Decision:** Treat language as presentation, not as a memory capability gate. Require the Product V2 semantic prompt to prefer reusable language-neutral entity keys and concepts while preserving source labels, raw evidence, Unicode, names, numbers, currencies, dates, times, units, filenames, uncertainty, and provenance. Keep lexical aliases and presentation templates as optional bounded fast paths only. When a question is unknown, mixed, or has a lexical gap, pass a bounded structured candidate set—not raw capture history—to the general semantic Ask path, and instruct the provider to answer in the current question's language with supplied source references only. Use unique-entity relaxation only when a genuine lexical gap exists; preserve strict ambiguity and retraction behavior for fully recognized queries.
- **Consequences:** Captures in Polish, English, Spanish, German, French, mixed language, Japanese, and Ukrainian can be exercised against the same structured memory without creating a per-language production ontology. The dedicated matrix contains 54 cases across locations, people/preferences, tasks, costs, current/previous values, corrections, uncertainty, documents, and non-Latin questions. The bounded fallback has explicit fact/history/relation/Attention limits and does not expose raw payload text. This is post-freeze product evidence, not a benchmark result, E006 optimization, holdout evaluation, or universal language-quality claim.
- **Revisit when:** A separately authorized provider capability, unseen product validation freeze, or transport/schema change alters the semantic response boundary. Preserve immutable raw sources, rebuildable derived state, explicit unknowns, approval boundaries, provider-token ownership, and holdout isolation.

## D-044 — Separate Product V2 Ask candidates from answer evidence

- **Status:** Accepted for the explicitly authorized post-freeze Product V2 provenance-precision scope; live semantic validation remains partial for an independent provider-extraction limitation.
- **Context:** D-043 correctly widened unknown and mixed-language Ask to a bounded structured candidate set, but the Ask projection still treated the provider's broad `source_refs` list as an answer selection. A correct answer could therefore expose unrelated references from valid retrieval candidates.
- **Decision:** Tag every provider-facing fact, history, relationship, Attention, and source-metadata candidate with a typed internal `evidence_id`. Require the provider's strict response to return explicit `evidence_ids`; validate them against the exact bounded context, ignore top-level provider `source_refs` for Ask, derive public references and items only from selected candidates, and strip internal IDs from the public response. Preserve deterministic provenance for rendered facts and Attention, allow multiple selected sources for history/corrections/conflicts, and fail closed when a non-empty selection contains no valid ID. Keep the local Codex CLI subscription-first, ephemeral, read-only, and token-free from Blackhole's perspective.
- **Consequences:** Retrieval can remain broad enough for language-invariant semantic selection while final citations stay narrow and materially tied to rendered support. Invalid provider IDs cannot fabricate provenance, and unrelated candidates do not leak into `source_refs`. The dedicated provenance suite is 11/11, focused coverage is 43/43, the full application suite is 137/137, and the visible integrated acceptance remains 50/50 in a new provenance result artifact. The authorized live smoke had 4/4 captures processed once and 4/4 asks with narrow relevant citations; one provider answer conservatively failed to recover a meeting time, so the overall live gate is PARTIAL rather than a universal semantic-quality claim.
- **Revisit when:** A separately authorized provider contract, UI provenance presentation, unseen validation freeze, or post-freeze generalization changes the evidence boundary. Preserve immutable raw sources, rebuildable derived state, explicit unknowns, approval boundaries, provider-token ownership, and holdout isolation.

## D-045 — Keep Product V2 semantic truth as an evidence-led projection

- **Status:** Accepted for the explicitly authorized post-freeze Product V2 semantic-truth scope; it is not a benchmark optimization or E006.
- **Context:** The integrated Product V2 runtime preserved raw evidence and provenance but still needed a general semantic-state contract for corrections, ordinary effective-time changes, uncertainty, attribution, contradiction, negation, temporal meaning, and Attention lifecycle. The mixed-language meeting failure showed that temporal interpretation could not be left to an unstructured display string.
- **Decision:** Preserve immutable source evidence and make derived truth rebuildable. Treat correction as targeted supersession rather than deletion, distinguish ordinary change from correction, retain duplicate support, keep conflicting claims conflicting, preserve reported attribution and negation, and prevent a newer speculative claim from becoming certain by recency alone. Use structured temporal primitives (`valid_from`/`effective_at`, occurrence normalization, relative values, weekday index/local time, precision/interval) with deterministic capture-reference normalization. Use stable Attention lifecycle keys and related-event links for reschedule, correction, completion, and cancellation. Keep Ask provenance as candidate selection plus validated supporting evidence. The semantic provider remains the language-neutral interpretation boundary; no exact phrase or per-language correction capability is added.
- **Consequences:** Current, historical, uncertain, conflicting, attributed, negated, and retracted states can be rendered distinctly while raw evidence remains auditable. Future occurrence timestamps do not hide current assertions, effective dates select the appropriate state version, ambiguous times remain coarse, and ghost Attention timelines are removed. The dedicated semantic-truth suite covers 64 sequence cases and rebuild equivalence; existing Product V2, provenance, language-invariance, and routing tests remain required regressions. This evidence is product generalization evidence only and must not be used to change V1 benchmark, baseline, evaluator, calibration, or holdout artifacts.
- **Revisit when:** A human-approved provider/schema, transport, UI, or product-generalization scope changes the semantic-state boundary. Preserve source immutability, rebuildability, unknown semantics, approval boundaries, provider-token ownership, and holdout isolation.
