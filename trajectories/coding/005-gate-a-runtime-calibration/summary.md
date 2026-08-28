# Task summary: Gate A pre-freeze revision and runtime calibration

**Status:** Preparation complete; runtime calibration blocked pending provider/API configuration; Gate A is not frozen.

## Goal

Prepare Gate A for the requested Blackhole framing and actual long-chat runtime
calibration without implementing the final application, advanced agent, scored
baseline run, evaluator, or final benchmark. Use the fixed-prompt calibration
to choose a realistic primary length based on longitudinal state degradation
while the complete history remains available.

## Agent/tool used

The work was performed by the Codex coding agent using local file inspection,
safe runtime-configuration inspection, `apply_patch`, PowerShell validation,
the existing standard-library calibration generator, and Git checks. No model
API, external provider, application runtime, baseline implementation, or
evaluator implementation was used.

## Initial hypothesis

The existing 50/100/200/400 calibration data should be retained, but token
estimates alone cannot select the final benchmark length. A frozen, reasonable
long-chat baseline must be run against all four sizes, with any 800-event
extension gated on the 400-event result. The benchmark hypothesis remains
longitudinal state maintenance, not OCR or vision quality.

## Important design decisions

- The product framing is now **Blackhole — “A zero-organization life inbox.”**
  The principle is **CAPTURE NOW. ORGANIZE LATER.** The framing describes
  executive-function friction and may mention ADHD as an example of user need,
  while explicitly making no medical diagnosis, treatment, or assistance claims.
- UX principles are documented as **SILENT BY DEFAULT**, **INTERRUPT ONLY WHEN
  USEFUL**, and **OBSERVE, DO NOT JUDGE**.
- The primary benchmark uses synthetic text or normalized extracted content for
  receipt/document/image-derived modalities so OCR/vision quality is not the
  primary confound.
- LQA-0M remains the primary metric, but each fixed query now uses
  `TP / (TP + FP + FN)`, penalizing unsupported or incorrect assertions. Empty
  expected and empty produced sets score `1.0`; exactly one empty set scores
  `0.0`. LQA-0M is the unweighted mean across fixed queries and checkpoints.
- Critical categories are reported separately, and safety violations remain a
  hard failure outside the average.
- MIR-90 is removed from the current contract. The proposed maintenance metric
  is DSCR: distinct underlying state defects requiring correction, reported as
  total, per 100 events, and by category. DSCR is not human minutes.
- The fair baseline is one continuous general-purpose conversation with a
  frozen reasonable personal-life-admin prompt, complete history whenever it
  fits, no hidden state/retrieval/database/tools, and the same exact semantic
  model as the advanced system where practical.
- `prompts/runtime/baseline-v1.md` is frozen for calibration. It must not be
  tuned after observing calibration failures.
- The final benchmark-generation plan is a deterministic synthetic world:
  canonical hidden state → chronological user-facing events → deterministic
  checkpoint ground truth. Final holdout ground truth remains evaluator-owned.
- The existing 50/100/200/400 calibration artifacts remain non-scored. An
  approximately 800-event continuation is allowed at most once, only after the
  400-event conditions in the contract are satisfied.

## Tools/actions used

- Read the pasted Gate A pre-freeze revision in full.
- Created this coding trajectory before making meaningful repository changes.
- Inspected provider-related environment-variable names and available local
  runtime commands without printing values. No provider environment variables,
  local model CLI, or repository runtime configuration was found.
- Updated `README.md`, `docs/PRODUCT_SPEC.md`, `docs/DECISIONS.md`,
  `docs/EVALUATION.md`, `docs/REPRODUCTION.md`, `benchmark/README.md`,
  `benchmark/calibration/README.md`, and the calibration report.
- Added the frozen baseline prompt and the blocked runtime-calibration report
  template.
- Preserved the existing calibration data and added no 800-event data.

## Failures encountered

No functional failures occurred. Runtime inspection found no usable provider/API
credential in the workspace, so the model-dependent calibration could not be
run. No credential value was printed or committed.

## Retries or changed approaches

The work proceeded through the preparation path required by the instruction:
documentation, frozen prompt, and report template were completed instead of
inventing model scores or attempting an unauthorised runtime workaround.

## Human feedback or checkpoints

The human instruction stated that Gate A is not approved, required actual
runtime calibration, prohibited final application/advanced-agent implementation,
required the existing calibration to be kept, and required stopping to request
the exact provider/API configuration if no credential is available. No human
approval of the final provider, model, event count, or Gate A freeze has occurred.

## Evaluation performed

- Provider-related environment variable names were inspected without exposing
  values; none were present.
- Available local commands were inspected; Python, Node, and generic `curl`
  were available, but no local model/provider CLI was available.
- The existing calibration generator was rerun successfully.
- Calibration artifacts were structurally validated for JSON/JSONL parsing,
  event counts, sequence bounds, storyline counts, and baseline prompt presence.
- `git diff --check` was run.
- No model correctness, exact tokenizer, context utilization, runtime, or API
  cost result was produced because the runtime provider/model is not configured.

## Result

The repository is ready for the actual fixed-prompt calibration once the human
provides runtime configuration. Product framing, benchmark scope, LQA-0M,
DSCR, fair-baseline rules, 800-event gate, deterministic generation plan, and
the calibration report fields are documented. Gate A remains open.

## Regressions or unresolved issues

- Provider, exact model identifier, endpoint if non-default, credential
  availability, context limit, tokenizer, temperature, output limit, retry
  policy, and pricing are unconfigured.
- Actual 50/100/200/400 query correctness and degradation measurements remain
  pending.
- The optional 800-event continuation must not be generated before the 400-event
  conditions are evaluated.
- Final primary/stress event counts, final checkpoint matrix, final benchmark
  cases, expected outputs, baseline run, and application remain unapproved and
  unimplemented.
- No `IMPROVEMENT_CHANGELOG.md` entry was added because no scored experiment or
  measured model improvement occurred.
- No authentic coding-agent transcript export was available; no transcript was
  fabricated or reconstructed.

## Final decision

`KEEP` the existing non-scored calibration and the revised Gate A preparation.
Stop before runtime execution and request the missing provider/API configuration.

## Related git commits

- `1992588 docs: calibrate benchmark size before Gate A` — existing calibration
  data and pre-freeze size proposal.
- This task: one coherent Gate A pre-freeze revision/runtime-preparation commit,
  `docs: prepare Gate A runtime calibration`.
