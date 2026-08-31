# Agent trajectory index

This index is a judge-facing map of the completed agent-engineering evidence
present in this checkout. It preserves failed and superseded work instead of
presenting the history as a linear success story. `python
scripts/qualification_check.py --inventory` is the deterministic re-audit
command; the snapshot below was taken from the same tree.

The Host/PWA integration, submission hardening, reproduction refresh, and
frozen-runtime audit workstreams are included below. Their source branches and
worktrees remain preserved for auditability. Private or not-yet-submission-
visible generalization trajectories are intentionally not listed unless their
evidence is present in this checkout. The public Generalization V1R1 archive is
now listed below; the local oracle and scoring histories remain separate.

## Coding trajectories

| ID | Purpose | Result | Commit | Evidence |
| --- | --- | --- | --- | --- |
| 001-design-scaffold | Establish product, safety, evaluation, and reproducibility boundaries | Documentation scaffold; no implementation | `d9d7698` | [summary](trajectories/coding/001-design-scaffold/summary.md) |
| 002-benchmark-design | Draft the benchmark contract before implementation | Contract proposal paused for human review | `d5e9b40` | [summary](trajectories/coding/002-benchmark-design/summary.md) |
| 003-gate-a-benchmark-revision | Revise the Gate A contract for longitudinal evaluation | Gate A contract revision prepared | `f5a6405` | [summary](trajectories/coding/003-gate-a-benchmark-revision/summary.md) |
| 004-benchmark-size-calibration | Build non-scored 50/100/200/400 size calibration | Calibration dataset retained; Gate A still open at that point | `1992588` | [summary](trajectories/coding/004-benchmark-size-calibration/summary.md) |
| 005-gate-a-runtime-calibration | Prepare the fixed-prompt runtime calibration | Preparation blocked pending provider configuration | `45d49aa` | [summary](trajectories/coding/005-gate-a-runtime-calibration/summary.md) |
| 006-provider-harness-correction | Establish the subscription-first local CLI boundary | Codex CLI calibration completed; 200 primary / 400 stress selected | `9fc8534` | [summary](trajectories/coding/006-provider-harness-correction/summary.md) |
| 007-gate-a-freeze-and-baseline | Freeze the public benchmark and run the first baseline | Gate A frozen; v0 output preserved but invalid as semantic baseline | `64d4662` | [summary](trajectories/coding/007-gate-a-freeze-and-baseline/summary.md) |
| 008-gate-b-contract-repair | Repair the response contract and establish a valid baseline | Official `baseline-v1`: LQA-0M `0.3014914553`, DSCR `277` | `e3eff67` | [summary](trajectories/coding/008-gate-b-contract-repair/summary.md) |
| 010-stale-gate-a-recovery | Recover from the stale Gate A reassessment | Valid Gate B state restored; stale commit preserved in history | `8ec2b0d` | [summary](trajectories/coding/010-stale-gate-a-recovery/summary.md) |
| 011-experiment-001-state-projection | Test append-only state plus deterministic projection | KEEP; E001 replay LQA-0M `0.7492295899`, DSCR `72` | `10cec9e` | [summary](trajectories/coding/011-experiment-001-state-projection/summary.md) |
| 012-generic-state-projection | Remove benchmark-specific projector routing | KEEP; generic repair preserved E001 score and reduced coupling | `badc109` | [summary](trajectories/coding/012-generic-state-projection/summary.md) |
| 013-final-product-submission | Package the local demo and product-phase evidence | Historical product package based on E002; superseded by later E003–E005 | `44606a2` | [summary](trajectories/coding/013-final-product-submission/summary.md) |
| 014-experiment-003-relations | Add bounded retrieval-assisted relation reconciliation | KEEP; LQA-0M `0.8157180034`, DSCR `45` | `a58ad11` | [summary](trajectories/coding/014-experiment-003-relations/summary.md) |
| 015-experiment-004-selective-verification | Test deterministic selective completeness | KEEP; LQA-0M `0.8630770101`, DSCR `41` | `5e8ca97` | [summary](trajectories/coding/015-experiment-004-selective-verification/summary.md) |
| 016-experiment-005-duplicate-evidence | Consolidate evidence from true duplicate components | KEEP; current frozen-track reference LQA-0M `0.8695006212`, DSCR `40` | `46b6085` | [summary](trajectories/coding/016-experiment-005-duplicate-evidence/summary.md) |
| 017-deferred-ingestion | Separate synchronous capture from later semantic processing | Product-runtime milestone; explicitly not Experiment 006 | `0c60da9` | [summary](trajectories/coding/017-deferred-ingestion/summary.md) |
| 018-blackhole-host-foundation | Add the local Host foundation and safe CLI discovery | Product-runtime foundation; no new benchmark experiment | `11d8a04` | [summary](trajectories/coding/018-blackhole-host-foundation/summary.md) |
| 019-host-pwa-integration | Connect the approved PWA to the Host through same-origin HTTP | KEEP; integrated product-runtime milestone, not E006 | `284fb61` | [summary](trajectories/coding/019-host-pwa-integration/summary.md) |
| 019-global-skills-install | Install global coding/design skills for local agents | Global installation completed; no product/runtime change | `67e734e` | [summary](trajectories/coding/019-global-skills-install/summary.md) |
| 020-consolidation-freeze | Consolidate approved workstreams and freeze the integrated implementation | Documentation, validation, and freeze evidence; not a benchmark experiment | `171a6cc` | [summary](trajectories/coding/020-consolidation-freeze/summary.md) |
| 022-reproduction-refresh | Refresh judge-facing Host/PWA reproduction instructions | Documentation-only; no runtime, benchmark, evaluation, or metric changes | `abb8f80` | [summary](trajectories/coding/022-reproduction-refresh/summary.md) |
| 024-frozen-runtime-audit | Read-only adversarial audit of the frozen runtime | P0 `0`; P1 `10`; P2 `4`; findings preserved, no fixes | `59d1914` | [audit](docs/audits/FROZEN_RUNTIME_AUDIT.md), [summary](trajectories/coding/024-frozen-runtime-audit/summary.md) |
| 025-post-freeze-evidence-merge | Merge approved post-freeze documentation and independent audit evidence | Documentation/evidence merge; no runtime or benchmark change | `6bdb4ef` | [summary](trajectories/coding/025-post-freeze-evidence-merge/summary.md) |
| 026-generalization-v1r1-public-archive | Consolidate public-safe V1R1 evidence and remote history | Archive/remote-hygiene task; no runtime or benchmark change | `b29aa5a` | [summary](trajectories/coding/026-generalization-v1r1-public-archive/summary.md) |
| 027-generalization-public-v1r1-seal | Publish and seal the public V1R1 synthetic worlds and contracts | Public inputs sealed before blind runs | `6efbacc` | [summary](trajectories/coding/027-generalization-public-v1r1-seal/summary.md) |
| 028-generalization-v1r1-baseline-blind | Run and seal the stateless baseline candidates | Three candidates sealed before oracle/scoring access | `72294cd` | [summary](trajectories/coding/028-generalization-v1r1-baseline-blind/summary.md) |
| 029-generalization-v1r1-blackhole-blind | Run and seal the Blackhole candidates | Three candidates sealed before oracle/scoring access | `94e635f` | [summary](trajectories/coding/029-generalization-v1r1-blackhole-blind/summary.md) |
| 030-generalization-v1r1-scoring | Score sealed V1R1 candidates and analyze generalization | PASS; six deterministic results and public report; scoring history remains local | `47f1449` (local-only) | [report](docs/GENERALIZATION_V1R1_REPORT.md), [summary](trajectories/coding/030-generalization-v1r1-scoring/summary.md) |
| 031-product-v2-runtime-foundation | Build the isolated post-evaluation open-world runtime foundation | PASS; deterministic runtime/API foundation; no benchmark or holdout evaluation | `2ec991d` | [prompt](trajectories/coding/031-product-v2-runtime-foundation/prompt.md), [summary](trajectories/coding/031-product-v2-runtime-foundation/summary.md) |
| 032-product-v2-ui-redesign | Build the isolated mobile-first Product V2 PWA | KEEP; UI workstream preserved and integrated | `51e6810` | [summary](trajectories/coding/032-product-v2-ui-redesign/summary.md) |
| 033-product-v2-dogfood-acceptance | Define independent Product V2 dogfood acceptance | KEEP; 50 cases, deterministic mock gates, and human protocol | `90cb5ff` | [summary](trajectories/coding/033-product-v2-dogfood-acceptance/summary.md) |
| 034-product-v2-integration | Integrate the Product V2 runtime, PWA, and dogfood contract | KEEP; 50/50 visible acceptance cases and all quality gates passed | `43426e8` | [prompt](trajectories/coding/034-product-v2-integration/prompt.md), [summary](trajectories/coding/034-product-v2-integration/summary.md), [result](eval/results/product-v2-integrated-acceptance.json) |
| 035-product-v2-human-dogfood-p0-fixes | Repair the first human-dogfood Product V2 P0/P1 failures | KEEP; bounded lifecycle, provider, and UI repairs preserved | `41271c9` | [prompt](trajectories/coding/035-product-v2-human-dogfood-p0-fixes/prompt.md), [summary](trajectories/coding/035-product-v2-human-dogfood-p0-fixes/summary.md) |
| 036-product-v2-live-provider-fix | Repair provider-backed Product V2 processing diagnostics | PARTIAL; offline gates pass, live provider evidence remains bounded | `37e56d3` | [prompt](trajectories/coding/036-product-v2-live-provider-fix/prompt.md), [summary](trajectories/coding/036-product-v2-live-provider-fix/summary.md) |
| 037-product-v2-ask-routing | Generalize Product V2 Ask routing for grounded retrieval | KEEP; deterministic Ask routing and bounded context preserved | `046ffa8` | [prompt](trajectories/coding/037-product-v2-ask-routing/prompt.md), [summary](trajectories/coding/037-product-v2-ask-routing/summary.md) |
| 038-product-v2-language-invariance | Generalize Product V2 memory and Ask across capture/query languages | KEEP offline implementation; live gate PARTIAL pending provenance-focused validation | `16aad12` | [prompt](trajectories/coding/038-product-v2-language-invariance/prompt.md), [summary](trajectories/coding/038-product-v2-language-invariance/summary.md), [live](trajectories/coding/038-product-v2-language-invariance/live-validation.json), [result](eval/results/product-v2-language-invariance.json) |
| 039-product-v2-provenance-precision | Narrow Ask provenance to selected supporting evidence | KEEP; provenance precision and no-fabrication behavior preserved | `c73369b` | [prompt](trajectories/coding/039-product-v2-provenance-precision/prompt.md), [summary](trajectories/coding/039-product-v2-provenance-precision/summary.md) |
| 040-product-v2-semantic-truth | Preserve correction and temporal meaning in Product V2 projections | KEEP; semantic truth and deterministic occurrence aggregation preserved | `1047873` | [prompt](trajectories/coding/040-product-v2-semantic-truth/prompt.md), [summary](trajectories/coding/040-product-v2-semantic-truth/summary.md) |
| 041-product-v2-undo-and-ops-logs | Add permanent Product V2 Undo and operational logging boundaries | KEEP; explicit forget and safe operational evidence preserved | `a719e9a` | [prompt](trajectories/coding/041-product-v2-undo-and-ops-logs/prompt.md), [summary](trajectories/coding/041-product-v2-undo-and-ops-logs/summary.md) |
| 042-product-v2-final-human-dogfood-fixes | Apply the final bounded Product V2 P0/P1 human-dogfood repair | KEEP implementation; overall live gate PARTIAL/REVISE | `e5ca77f` | [prompt](trajectories/coding/042-product-v2-final-human-dogfood-fixes/prompt.md), [summary](trajectories/coding/042-product-v2-final-human-dogfood-fixes/summary.md), [live](trajectories/coding/042-product-v2-final-human-dogfood-fixes/live-validation.json), [result](eval/results/product-v2-final-human-dogfood-fixes.json) |
| 043-product-v2-last-dogfood-fixes | Consolidate Product V2 into master and apply the final generic dogfood corrections | KEEP; `184/184` app tests and `50/50` visible acceptance, no live provider | `7d695ec` | [prompt](trajectories/coding/043-product-v2-last-dogfood-fixes/prompt.md), [summary](trajectories/coding/043-product-v2-last-dogfood-fixes/summary.md), [result](eval/results/product-v2-final-dogfood-fixes.json) |
| 044-submission-finalization | Harden the final judge-facing package and demo path without changing Product V2 semantics | PASS; local deterministic submission gate green; no Product V2 semantic change | `0bd6810` | [prompt](trajectories/coding/044-submission-finalization/prompt.md), [summary](trajectories/coding/044-submission-finalization/summary.md), [result](eval/results/product-v2-integrated-acceptance.json) |
| 045-macos-timezone-portability-hotfix | Repair macOS fixed-offset timezone discovery and validate cross-platform fallback | KEEP; `192/192` app tests, `209/209` root tests, `50/50` acceptance; no live provider | `8eb8158` | [prompt](trajectories/coding/045-macos-timezone-portability-hotfix/prompt.md), [summary](trajectories/coding/045-macos-timezone-portability-hotfix/summary.md), [result](eval/results/product-v2-integrated-acceptance.json) |
| 046-final-live-ask-memory-ui-hotfix | Repair current-question Ask, generic occurrence Memory, and final live UX surfaces | KEEP; `196/196` app tests, `213/213` root tests, `50/50` acceptance, bounded live gate PASS | `93e497a` | [prompt](trajectories/coding/046-final-live-ask-memory-ui-hotfix/prompt.md), [summary](trajectories/coding/046-final-live-ask-memory-ui-hotfix/summary.md), [runtime](trajectories/runtime/046-final-live-ask-memory-ui-hotfix/summary.md), [result](eval/results/product-v2-final-live-ux-hotfix.json) |
| 047-relative-day-temporal-hotfix | Repair capture-time relative-day normalization and occurrence rendering | KEEP; `200/200` app tests, `217/217` root tests, `50/50` acceptance; no live provider | `c9aba33` | [prompt](trajectories/coding/047-relative-day-temporal-hotfix/prompt.md), [summary](trajectories/coding/047-relative-day-temporal-hotfix/summary.md), [result](eval/results/product-v2-integrated-acceptance.json) |
| 048-final-demo-presentation-polish | Polish final Ask, Capture, Attention, and Memory presentation within the freeze boundary | KEEP implementation; `206/206` app tests, `223/223` root tests, `50/50` acceptance, local visual PASS; live smoke PARTIAL because its result was not captured | `13af0d0` | [prompt](trajectories/coding/048-final-demo-presentation-polish/prompt.md), [summary](trajectories/coding/048-final-demo-presentation-polish/summary.md), [runtime](trajectories/runtime/048-final-demo-presentation-polish/trace.json), [result](eval/results/product-v2-integrated-acceptance.json) |
| ui-001-mobile-pwa | Build the dependency-light mobile-first PWA in an isolated worktree | KEEP; UI workstream preserved and integrated | `0cc6653` | [summary](trajectories/coding/ui-001-mobile-pwa/summary.md) |
| ui-002-reference-redesign | Correct the Capture surface against the approved mobile reference | KEEP; UI correction preserved and integrated | `0cc6653` | [summary](trajectories/coding/ui-002-reference-redesign/summary.md) |
| submission-001-hardening | Add offline qualification, CI, evidence index, and submission checklist | KEEP; three non-blocking stale-artifact warnings remain for finalization | `18b123f` | [summary](trajectories/coding/submission-001-hardening/summary.md) |

The short commit IDs above were resolved from local Git history. The historical
hardening implementation is in `18b123f`; the small follow-up metadata commit
records the final handoff state of that trajectory. The historical integrated
product merge is `20e4540`, and the hardening merge is `bc4ef78`. The Product V2
integration merge of the three source branches is `2ff1156`; the final
pre-submission integration commit is `43426e8`. The current submission
finalization row records the local submission-hardening commit. The final
remote master and tag identifiers are verified in the final handoff.

## Runtime trajectories

| ID | Purpose | Provider | Result | Evidence |
| --- | --- | --- | --- | --- |
| 001-codex-calibration | Fixed-prompt 50/100/200/400 size calibration | Codex CLI | Non-scored calibration; all four sizes completed and the 200-event primary was retained | [summary](trajectories/runtime/001-codex-calibration/summary.md) |
| 002-baseline-v0 | First fair long-chat baseline | Codex CLI | Invalid contract output preserved; LQA-0M `0.0000`, not an official semantic baseline | [summary](trajectories/runtime/002-baseline-v0/summary.md), [result](eval/results/baseline-v0-invalid-contract.json) |
| 003-baseline-v1 | Corrected checkpoint-isolated fair baseline | Codex CLI | Valid official baseline; LQA-0M `0.3014914553`, DSCR `277` | [summary](trajectories/runtime/003-baseline-v1/summary.md), [result](eval/results/baseline-v1.json) |
| 013–016 demo traces | Capture, longitudinal history, unknown, correction/reassignment | None; deterministic local demo | Representative product behavior with no provider calls | [demo traces](trajectories/runtime/013-demo-simple-capture/) |
| experiment-001-full-v1 | Fresh E001 semantic extraction over the public case | Codex CLI | Initial extraction run preserved for later deterministic projector replays | [summary](trajectories/runtime/experiment-001-full-v1/summary.md) |
| experiment-001-full-v4 | Replay the E001 extraction through the final deterministic projector | No new provider call | LQA-0M `0.7492295899`, DSCR `72` | [summary](trajectories/runtime/experiment-001-full-v4/summary.md), [result](eval/results/experiment-001-full-v4.json) |
| experiment-002-generic-full | Replay the generic projector | None; deterministic replay | LQA-0M `0.7492295899`, DSCR `72`; genericity repair evidence | [summary](trajectories/runtime/experiment-002-generic-full/summary.md), [result](eval/results/experiment-002-generic-full.json) |
| experiment-003-retrieval-full-v3 | Replay bounded relation retrieval/reconciliation | None; deterministic replay | LQA-0M `0.8157180034`, DSCR `45` | [summary](trajectories/runtime/experiment-003-retrieval-full-v3/summary.md), [result](eval/results/experiment-003-retrieval-full-v3.json) |
| experiment-004-deterministic-full | Replay selective deterministic completeness | None; deterministic replay | LQA-0M `0.8630770101`, DSCR `41` | [result](eval/results/experiment-004-deterministic-full.json), [runtime files](trajectories/runtime/experiment-004-deterministic-full/) |
| experiment-005-duplicate-evidence-full | Replay duplicate-aware evidence consolidation | None; deterministic replay | Current kept E005 reference; LQA-0M `0.8695006212`, DSCR `40` | [runtime files](trajectories/runtime/experiment-005-duplicate-evidence-full/), [result](eval/results/experiment-005-duplicate-evidence-full.json) |
| 017-final-advanced-replay | Historical product-phase final replay | None; deterministic replay | Superseded E002 artifact; LQA-0M `0.7492295899`, DSCR `72` | [summary](trajectories/runtime/017-final-advanced-replay/summary.md) |
| 017-deferred-ingestion-fake | Exercise deferred capture/processing with neutral fake provider | Injected fake provider | Deterministic integration behavior; no benchmark score | [summary](trajectories/runtime/017-deferred-ingestion-fake/summary.md) |
| 017-deferred-ingestion-e005-regression | Regression replay after deferred-ingestion refactor | None; deterministic replay | Matches E005 reference: LQA-0M `0.8695006212`, DSCR `40` | [runtime files](trajectories/runtime/017-deferred-ingestion-e005-regression/), [result](eval/results/deferred-ingestion-e005-regression.json) |
| 034-product-v2-integrated-acceptance | Exercise the integrated Product V2 Host contract and reliability gates | Deterministic local fixture; no live provider | 50/50 PASS; async latency and exact attachment evidence recorded | [summary](trajectories/runtime/034-product-v2-integrated-acceptance/summary.md), [result](eval/results/product-v2-integrated-acceptance.json) |
| 035-product-v2-human-dogfood-live-smoke | Exercise the first human-dogfood live Product V2 path | Authenticated local Codex CLI | Live latency/provider observations preserved; not a benchmark score | [trace](trajectories/runtime/035-product-v2-human-dogfood-live-smoke/trace.json) |
| 036-product-v2-live-provider-fix | Recheck the repaired live provider path and diagnostics | Authenticated local Codex CLI | Live gate remains bounded/partial; no benchmark or holdout material | [summary](trajectories/runtime/036-product-v2-live-provider-fix/summary.md) |
| 046-final-live-ask-memory-ui-hotfix | Bounded live validation of current-question Ask, occurrence Memory, and final UX | Authenticated local Codex CLI | PASS; 4 synthetic captures and 3 asks, all requests 200, 0 failures/retries, no private data | [trace](trajectories/runtime/046-final-live-ask-memory-ui-hotfix/trace.json), [summary](trajectories/runtime/046-final-live-ask-memory-ui-hotfix/summary.md) |
| 018-host-foundation-e005-regression | Regression replay after Host foundation | None; deterministic replay | Matches E005 reference: LQA-0M `0.8695006212`, DSCR `40` | [runtime files](trajectories/runtime/018-host-foundation-e005-regression/), [result](eval/results/host-foundation-e005-regression.json) |
| 019-host-pwa-real-neutral | Real neutral Host/PWA-equivalent smoke | Authenticated local Codex CLI | HTTP transport and deferred processing worked; novel-entity linking limitation recorded | [summary](trajectories/runtime/019-host-pwa-real-neutral/summary.md), [trace](trajectories/runtime/019-host-pwa-real-neutral/trace.json) |
| 020-consolidation-real-neutral | Post-consolidation neutral Host/PWA-equivalent smoke | Authenticated local Codex CLI | HTTP transport and deferred processing worked; known novel-entity linking limitation reproduced | [summary](trajectories/runtime/020-consolidation-real-neutral/summary.md), [trace](trajectories/runtime/020-consolidation-real-neutral/trace.json) |
| generalization-v1r1-baseline-g01/g02/g03 | Sealed stateless baseline executions over three fresh worlds | Codex CLI | Candidates sealed before oracle/scoring; retries and checkpoint evidence preserved | [g01](trajectories/runtime/generalization-v1r1-baseline-g01/), [g02](trajectories/runtime/generalization-v1r1-baseline-g02/), [g03](trajectories/runtime/generalization-v1r1-baseline-g03/) |
| generalization-v1r1-blackhole-g01/g02/g03 | Sealed Blackhole executions over three fresh worlds | Codex CLI plus deterministic processing | Candidates sealed before oracle/scoring; provider traces and derived-state evidence preserved | [g01](trajectories/runtime/generalization-v1r1-blackhole-g01/), [g02](trajectories/runtime/generalization-v1r1-blackhole-g02/), [g03](trajectories/runtime/generalization-v1r1-blackhole-g03/) |
| generalization-v1r1 scoring | Deterministic scoring and descriptive analysis of the sealed V1R1 set | None; frozen evaluator | Public result; no post-result tuning | [report](docs/GENERALIZATION_V1R1_REPORT.md), [machine result](eval/results/generalization/v1/GENERALIZATION_V1R1_RESULT.json) |
| other recorded fast/replay directories | Intermediate extraction, projector, retry, and diagnostic runs | Mixed; recorded per directory | Preserved as historical evidence, including failed/invalid attempts | [runtime root](trajectories/runtime/) |

The current filesystem inventory contains 49 coding trajectories and 53 runtime
trajectories. The index does not require every runtime directory to have a root `summary.md`:
the runtime inventory records whether a summary, prompt-like call file, raw
trace, and other artifacts are present. No transcript is fabricated for a
trajectory that has only the artifacts actually observed.

## Completeness inventory snapshot

`yes`/`no` values are filesystem observations. `n/a` means the field does not
apply to that trajectory type. For runtime trajectories, “Prompt” means a root
prompt or a recorded `*.prompt.txt` call file; “Raw trace” means a trace file,
transcript, or recorded `*.raw.txt` provider output.

### Coding trajectories

| ID | Type | Prompt | Summary | Runtime artifacts | Raw trace | Files |
| --- | --- | --- | --- | --- | --- | --- |
| 001-design-scaffold | coding | yes | yes | n/a | no | 2 |
| 002-benchmark-design | coding | yes | yes | n/a | no | 2 |
| 003-gate-a-benchmark-revision | coding | yes | yes | n/a | no | 2 |
| 004-benchmark-size-calibration | coding | yes | yes | n/a | no | 2 |
| 005-gate-a-runtime-calibration | coding | yes | yes | n/a | no | 2 |
| 006-provider-harness-correction | coding | yes | yes | n/a | no | 2 |
| 007-gate-a-freeze-and-baseline | coding | yes | yes | n/a | no | 2 |
| 008-gate-b-contract-repair | coding | yes | yes | n/a | no | 2 |
| 010-stale-gate-a-recovery | coding | yes | yes | n/a | no | 2 |
| 011-experiment-001-state-projection | coding | yes | yes | n/a | no | 2 |
| 012-generic-state-projection | coding | yes | yes | n/a | no | 2 |
| 013-final-product-submission | coding | yes | yes | n/a | no | 2 |
| 014-experiment-003-relations | coding | yes | yes | n/a | no | 2 |
| 015-experiment-004-selective-verification | coding | yes | yes | n/a | no | 2 |
| 016-experiment-005-duplicate-evidence | coding | yes | yes | n/a | no | 2 |
| 017-deferred-ingestion | coding | yes | yes | n/a | no | 2 |
| 018-blackhole-host-foundation | coding | yes | yes | n/a | no | 2 |
| 019-host-pwa-integration | coding | yes | yes | n/a | no | 2 |
| 019-global-skills-install | coding | yes | yes | n/a | no | 2 |
| 020-consolidation-freeze | coding | yes | yes | n/a | no | 2 |
| 022-reproduction-refresh | coding | yes | yes | n/a | no | 2 |
| 024-frozen-runtime-audit | coding | yes | yes | n/a | no | 3 |
| 025-post-freeze-evidence-merge | coding | yes | yes | n/a | no | 2 |
| 026-generalization-v1r1-public-archive | coding | yes | yes | n/a | no | 2 |
| 027-generalization-public-v1r1-seal | coding | yes | yes | n/a | no | 2 |
| 028-generalization-v1r1-baseline-blind | coding | yes | yes | n/a | no | 3 |
| 029-generalization-v1r1-blackhole-blind | coding | yes | yes | n/a | no | 2 |
| 030-generalization-v1r1-scoring | coding | yes | yes | n/a | no | 3 |
| 031-product-v2-runtime-foundation | coding | yes | yes | n/a | no | 2 |
| 032-product-v2-ui-redesign | coding | yes | yes | n/a | no | 2 |
| 033-product-v2-dogfood-acceptance | coding | yes | yes | n/a | no | 2 |
| 034-product-v2-integration | coding | yes | yes | n/a | no | 2 |
| 035-product-v2-human-dogfood-p0-fixes | coding | yes | yes | n/a | no | 3 |
| 036-product-v2-live-provider-fix | coding | yes | yes | n/a | no | 3 |
| 037-product-v2-ask-routing | coding | yes | yes | n/a | no | 3 |
| 038-product-v2-language-invariance | coding | yes | yes | n/a | no | 3 |
| 039-product-v2-provenance-precision | coding | yes | yes | n/a | no | 3 |
| 040-product-v2-semantic-truth | coding | yes | yes | n/a | no | 3 |
| 041-product-v2-undo-and-ops-logs | coding | yes | yes | n/a | no | 3 |
| 042-product-v2-final-human-dogfood-fixes | coding | yes | yes | n/a | no | 5 |
| 043-product-v2-last-dogfood-fixes | coding | yes | yes | n/a | no | 2 |
| 044-submission-finalization | coding | yes | yes | n/a | no | 2 |
| 045-macos-timezone-portability-hotfix | coding | yes | yes | n/a | no | 2 |
| 046-final-live-ask-memory-ui-hotfix | coding | yes | yes | n/a | no | 2 |
| 047-relative-day-temporal-hotfix | coding | yes | yes | n/a | no | 2 |
| 048-final-demo-presentation-polish | coding | yes | yes | n/a | no | 2 |
| ui-001-mobile-pwa | coding | yes | yes | n/a | no | 2 |
| ui-002-reference-redesign | coding | yes | yes | n/a | no | 2 |
| submission-001-hardening | coding | yes | yes | n/a | no | 2 |
| ui-001-mobile-pwa | coding | yes | yes | n/a | no | 2 |
| ui-002-reference-redesign | coding | yes | yes | n/a | no | 2 |
| submission-001-hardening | coding | yes | yes | n/a | no | 2 |

### Runtime trajectories

| ID | Type | Prompt | Summary | Runtime artifacts | Raw trace | Files |
| --- | --- | --- | --- | --- | --- | --- |
| 001-codex-calibration | runtime | no | yes | yes | no | 11 |
| 002-baseline-v0 | runtime | no | yes | yes | no | 5 |
| 003-baseline-v1 | runtime | no | yes | yes | no | 5 |
| 013-demo-simple-capture | runtime | no | yes | yes | yes | 2 |
| 014-demo-longitudinal-change | runtime | no | yes | yes | yes | 2 |
| 015-demo-unknown | runtime | no | yes | yes | yes | 2 |
| 016-demo-correction-reassignment | runtime | no | yes | yes | yes | 2 |
| 017-deferred-ingestion-e005-regression | runtime | yes | no | yes | yes | 29 |
| 017-deferred-ingestion-fake | runtime | no | yes | yes | no | 1 |
| 017-final-advanced-replay | runtime | yes | yes | yes | yes | 22 |
| 018-host-foundation-e005-regression | runtime | yes | no | yes | yes | 29 |
| 019-host-pwa-real-neutral | runtime | no | yes | yes | yes | 2 |
| 020-consolidation-real-neutral | runtime | no | yes | yes | yes | 2 |
| 034-product-v2-integrated-acceptance | runtime | no | yes | yes | no | 1 |
| 035-product-v2-human-dogfood-live-smoke | runtime | no | no | yes | yes | 1 |
| 036-product-v2-live-provider-fix | runtime | yes | no | yes | yes | 3 |
| 046-final-live-ask-memory-ui-hotfix | runtime | no | yes | yes | yes | 2 |
| 048-final-demo-presentation-polish | runtime | no | no | yes | yes | 1 |
| generalization-v1r1-baseline-g01 | runtime | no | no | yes | no | 4 |
| generalization-v1r1-baseline-g02 | runtime | no | no | yes | no | 10 |
| generalization-v1r1-baseline-g03 | runtime | no | no | yes | no | 6 |
| generalization-v1r1-blackhole-g01 | runtime | yes | no | yes | yes | 29 |
| generalization-v1r1-blackhole-g02 | runtime | yes | no | yes | yes | 29 |
| generalization-v1r1-blackhole-g03 | runtime | yes | no | yes | yes | 29 |
| experiment-001-fast-dev | runtime | yes | yes | yes | yes | 3 |
| experiment-001-fast-dev-deterministic | runtime | yes | yes | yes | yes | 7 |
| experiment-001-fast-dev-deterministic-v2 | runtime | yes | yes | yes | yes | 7 |
| experiment-001-fast-dev-live-high | runtime | yes | yes | yes | yes | 7 |
| experiment-001-fast-dev-replay | runtime | yes | yes | yes | yes | 5 |
| experiment-001-fast-dev-replay2 | runtime | yes | yes | yes | yes | 7 |
| experiment-001-fast-dev-retry2 | runtime | yes | yes | yes | yes | 3 |
| experiment-001-fast-dev-v4 | runtime | yes | yes | yes | yes | 7 |
| experiment-001-full-v1 | runtime | yes | yes | yes | yes | 22 |
| experiment-001-full-v2 | runtime | yes | yes | yes | yes | 22 |
| experiment-001-full-v3 | runtime | yes | yes | yes | yes | 22 |
| experiment-001-full-v4 | runtime | yes | yes | yes | yes | 22 |
| experiment-002-generic-fast | runtime | yes | yes | yes | yes | 7 |
| experiment-002-generic-full | runtime | yes | yes | yes | yes | 22 |
| experiment-003-deterministic-fast | runtime | yes | no | yes | yes | 6 |
| experiment-003-deterministic-relation-fast | runtime | yes | no | yes | yes | 6 |
| experiment-003-retrieval-fast | runtime | yes | no | yes | yes | 7 |
| experiment-003-retrieval-full | runtime | yes | no | yes | yes | 25 |
| experiment-003-retrieval-full-v2 | runtime | yes | no | yes | yes | 25 |
| experiment-003-retrieval-full-v3 | runtime | yes | no | yes | yes | 25 |
| experiment-003-retrieval-relation-fast | runtime | yes | no | yes | yes | 7 |
| experiment-003-retrieval-relation-fast-v3 | runtime | yes | no | yes | yes | 7 |
| experiment-004-deterministic-fast | runtime | yes | no | yes | yes | 8 |
| experiment-004-deterministic-full | runtime | yes | no | yes | yes | 29 |
| experiment-005-duplicate-evidence-fast | runtime | yes | no | yes | yes | 8 |
| experiment-005-duplicate-evidence-full | runtime | yes | no | yes | yes | 29 |
| fast-dev-050 | runtime | no | no | yes | no | 1 |
| fast-dev-050-rerun | runtime | no | no | yes | no | 1 |
| fast-dev-050-retry2 | runtime | no | yes | yes | no | 2 |
