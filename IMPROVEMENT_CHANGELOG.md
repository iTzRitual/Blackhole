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

## Entry template

Use one entry per meaningful improvement:

```text
## YYYY-MM-DD — Short title

- Problem or failure observed:
- Change made:
- Evidence or evaluation impact:
- Follow-up:
```
