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
