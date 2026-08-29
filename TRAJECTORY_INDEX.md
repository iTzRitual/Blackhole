# Agent trajectory index

This index is a judge-facing map of the completed agent-engineering evidence
present in this checkout. It preserves failed and superseded work instead of
presenting the history as a linear success story. `python
scripts/qualification_check.py --inventory` is the deterministic re-audit
command; the snapshot below was taken from the same tree.

The Host/PWA integration workstream in the separate integration worktree is
not listed as a completed trajectory here.

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
| 019-global-skills-install | Install global coding/design skills for local agents | Global installation completed; no product/runtime change | `67e734e` | [summary](trajectories/coding/019-global-skills-install/summary.md) |
| submission-001-hardening | Add offline qualification, CI, evidence index, and submission checklist | KEEP; five non-blocking warnings remain for finalization | `18b123f` | [summary](trajectories/coding/submission-001-hardening/summary.md) |

The short commit IDs above were resolved from local Git history. The hardening
implementation is in `18b123f`; the small follow-up metadata commit records
the final handoff state of this trajectory.

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
| 018-host-foundation-e005-regression | Regression replay after Host foundation | None; deterministic replay | Matches E005 reference: LQA-0M `0.8695006212`, DSCR `40` | [runtime files](trajectories/runtime/018-host-foundation-e005-regression/), [result](eval/results/host-foundation-e005-regression.json) |
| other recorded fast/replay directories | Intermediate extraction, projector, retry, and diagnostic runs | Mixed; recorded per directory | Preserved as historical evidence, including failed/invalid attempts | [runtime root](trajectories/runtime/) |

The index does not require every runtime directory to have a root `summary.md`:
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
| 019-global-skills-install | coding | yes | yes | n/a | no | 2 |
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
