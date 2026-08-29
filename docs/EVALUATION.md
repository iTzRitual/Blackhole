# Evaluation plan

**Status:** Gate A benchmark proposal with size calibration, pending human approval

This document proposes a long-horizon benchmark for Blackhole. It is design-only:
no final benchmark cases, final expected outputs, scorer, evaluator implementation,
baseline implementation, or application implementation is included. The separate
size-calibration artifacts are non-scored synthetic inputs and are not the final
benchmark.

## 1. Evaluation goal

The benchmark tests this hypothesis:

> A structured stateful agent can maintain a more trustworthy longitudinal understanding of fragmented personal information than one long general-purpose AI conversation, while requiring less human maintenance.

This is primarily a longitudinal memory and state-maintenance evaluation. It is not
primarily an OCR, vision, or isolated classification benchmark. Receipt, document,
image-derived, and other modalities may be represented by synthetic text or
normalized extracted content so that primary errors measure state maintenance,
linking, temporal reconciliation, uncertainty handling, and deterministic
projections rather than OCR quality.

## 2. Evaluation protocol at a glance

The primary run compares two systems on the same chronological synthetic life
timeline:

1. **Fair long-chat baseline:** one general-purpose model, one frozen reasonable
   personal-life-admin system prompt, the same chronological captures, and the
   complete available conversation history whenever it fits. It has no SQLite
   memory, entity database, external persistent state, temporal reconciliation
   engine, graph, or agent-specific memory tool.
2. **Advanced candidate:** the system under test, using the same exact semantic
   runtime model where practical and the same chronological captures and fixed
   queries. It may maintain structured state, but any additional resources must be
   documented as the experimental treatment.

Both systems receive no manual organization, reminders, corrections, entity links, or
extra context during the primary run. At fixed timeline checkpoints, both answer the
same fixed query bundle. A separate stress experiment may test context-window
exhaustion; it must not replace the primary full-history baseline.

## 3. Benchmark overview and proposed timeline

The final primary timeline length is intentionally **not frozen yet**. The separate
calibration dataset at
[`benchmark/calibration/`](../benchmark/calibration/) compares 50, 100, 200, and
400-event prefixes using ten independent evolving storylines. It measures whether
state quality degrades while the history remains usable, rather than selecting a
length solely to fill the context window.

The current preferred final primary target is approximately **150–200 events**, if
the fixed-prompt calibration run shows longitudinal degradation in that range while
remaining within the selected model's usable context and hackathon budget. A
400-event history is the current optional stress candidate. The calibration report
and its explicit decision rule are in
[`benchmark/calibration/reports/SIZE_CALIBRATION.md`](../benchmark/calibration/reports/SIZE_CALIBRATION.md).

Once the length is selected, the final timeline should use fixed checkpoints at
approximately 25%, 50%, 75%, and the final event. Exact event counts, checkpoints,
query wording, empty-answer behavior, and canonicalization rules must be frozen
before final development cases are authored. The calibration data is not a final
case and does not supply final ground truth.

The proposed final case contains interleaved storylines rather than isolated toy
cases:

| Storyline | Longitudinal behavior tested |
| --- | --- |
| Subscription | recurring payments, price increase, cancellation intention, renewal terms, and change of mind or cancellation |
| Bills | repeated periods, missing coverage, possible price change, and incomplete evidence |
| Purchases versus observations | receipts versus explicit consumption observations, no-information periods, and bulk purchase that is not consumption |
| Family task | pickup task, reassignment to another person, and later task state |
| Insurance | approximate expiry note, authoritative policy document, and replacement policy |
| Receipts | exact duplicate upload, similar but distinct receipts, and merchant-name repetition |
| Irrelevant note | information that should not create an obligation or attention item |
| Ambiguous entity | insufficient evidence for a forced entity link |
| Contradictory observation | disagreement followed by unresolved or explicitly correcting evidence |
| Multi-date contract | signing, effective, renewal, and expiry dates with different semantics |
| Financial transaction | structured amount, currency, period, and deterministic aggregation |
| Approval-required item | proposed consequential action that must not be executed automatically |

The final case should interleave these storylines throughout the selected timeline.
No final cases are created by this proposal.

## 4. Exact unit of evaluation

The benchmark has three nested units:

- **Scenario:** the complete isolated synthetic timeline, its public initial context,
  and its cutoff/checkpoint schedule. No state carries between scenarios.
- **Checkpoint query bundle:** the fixed set of questions asked after a specified
  event count.
- **Atomic assertion:** the smallest deterministic claim in a query answer, such
  as one current subscription price, one deadline, one unresolved field, or one
  duplicate relation.

The primary measurement unit is one canonical assertion comparison within one fixed
query at one checkpoint. The primary result is reported overall and at every
checkpoint so accuracy can be plotted against history length. Assertions are not
arbitrarily weighted in the primary score.

The benchmark does not score only the final state. The final state remains an
important diagnostic and expected-state representation, but the primary outcome is
whether the system can answer fixed questions correctly without human maintenance as
the timeline grows.

## 5. Fixed checkpoint queries and assertions

The query bundle is versioned and identical for baseline and advanced systems. Query
wording is fixed for the primary run; paraphrased queries may be a separate
robustness slice.

| Query ID | Fixed question intent | Typical assertions |
| --- | --- | --- |
| `q-subscriptions-current` | Which subscriptions are currently active, and what does each currently cost? | active state, current price, currency, billing period |
| `q-subscriptions-history` | Did a subscription previously cost something different, and what changed? | prior price, current price, effective period, change relation |
| `q-attention-14d` | Which obligations require attention in the next 14 days? | obligation identity, due window, attention requirement |
| `q-insurance-expiry` | When does the current car insurance expire? | target policy, date/interval, date precision, provenance |
| `q-orange-costs` | What information about recurring costs is known? | observed amounts, coverage, missing period unknown, aggregate where defined |
| `q-monster-observations` | How many purchases are directly observed, and how many consumptions are directly confirmed? | purchase count, consumption count, unknown coverage, no purchase-to-consumption inference |
| `q-tasks-state` | Which tasks are still active, and which previous task was cancelled or reassigned? | task identity, lifecycle, owner, cancellation/reassignment |
| `q-unresolved` | Which facts remain unresolved or incomplete? | explicit unknowns, ambiguity, conflict reasons |
| `q-duplicates-changes` | Which inputs were duplicates, and which similar inputs represented meaningful changes? | pair relation, duplicate/change type, changed fields |
| `q-recent-changes` | What changed recently? | entity, prior/current values, effective period, evidence |
| `q-approval-boundary` | Which item requires human approval before an external action? | proposed action, approval required, executed=false |

Each question expands into one or more expected typed assertions. The query
definitions, assertion keys, and empty-answer behavior are frozen before final
benchmark generation.

## 6. Primary metric

The primary metric is **Longitudinal Query Accuracy at Zero Maintenance (LQA-0M)**.

For each fixed query `q` at checkpoint `c`, let `E_(c,q)` be the private expected
assertion set and `P_(c,q)` the candidate assertions after deterministic
canonicalization. Match assertions one-to-one by canonical state key, predicate,
value, knowledge status, and any required relation/provenance fields. Then:

```text
TP_(c,q) = correctly matched supported assertions
FP_(c,q) = unsupported, fabricated, or incorrect candidate assertions
FN_(c,q) = expected assertions omitted by the candidate

query_score_(c,q) = TP_(c,q) / (TP_(c,q) + FP_(c,q) + FN_(c,q))

checkpoint_score_c = mean(query_score_(c,q) for every fixed query q at c)

LQA-0M = mean(query_score_(c,q) over every fixed query and primary checkpoint)
```

If both the expected and candidate assertion sets for a query are empty, the query
score is deterministically `1.0`. If exactly one set is empty, its non-empty side
produces only false positives or false negatives and the score is `0.0`. This is the
only zero-denominator special case.

The primary score uses equal query weight and equal checkpoint weight; it does not
use arbitrary 2:1 assertion weights. An expected unknown is a valid answer, while a
fabricated value or unsupported assertion is penalized as a false positive. The
primary report must include every checkpoint, every query score, and the aggregate
LQA-0M.

Precision, recall, and F1 may remain secondary diagnostics. Critical categories are
reported separately and are never hidden by the aggregate:

- current-state accuracy;
- temporal/history accuracy;
- known/inferred/unknown handling;
- obligations and deadlines;
- deterministic financial correctness;
- duplicate/change handling;
- contradiction handling; and
- safety violations.

Critical safety violations remain a separate hard failure regardless of LQA-0M.

## 7. Human-maintenance metric

The secondary strategic metric is **Distinct State Corrections Required (DSCR)**.

After the zero-maintenance run, an evaluator groups the candidate's incorrect,
unsupported, or missing assertions by the distinct underlying state defect that a
human would need to correct. Multiple query or checkpoint failures caused by one
root defect count once. A correction cluster must identify its affected state key(s),
evidence, and category; it must not be created merely by counting repeated symptoms.

Report:

- total DSCR;
- `DSCR_per_100_events = 100 * DSCR / captured_event_count`; and
- correction categories such as stale current state, entity link, unsupported
  certainty, temporal/date, task lifecycle, obligation/deadline, financial,
  duplicate/change, contradiction, provenance, and safety.

DSCR is a correction-count proxy. It must not be described as human minutes. Actual
wall-clock maintenance time may be collected only as exploratory evidence.

## 8. Secondary metrics

Report these separately from LQA-0M and DSCR:

- accuracy at every timeline checkpoint and the change from early to final
  checkpoint;
- entity-linking accuracy, including correct unresolved decisions;
- temporal and current-state accuracy;
- known/inferred/unknown precision, recall, and calibration;
- task lifecycle and ownership accuracy;
- obligation and deadline accuracy;
- duplicate, meaningful-change, and correction accuracy;
- contradiction detection and preservation;
- deterministic financial observation and aggregate accuracy;
- query accuracy by storyline;
- unnecessary attention/alert rate;
- critical safety-violation count;
- output-schema validity;
- model/API cost, runtime, and token consumption; and
- rebuild consistency where a rebuildable state is exposed.

The baseline must report total input/output tokens and context usage. If the full
conversation exceeds the model context window, record the event and run that
condition only as a separately labeled stress experiment.

## 9. Scenario and data contract

The implementation-facing scenario package contains public inputs only:

```json
{
  "contract_version": "0.3-gate-a-proposed-calibration",
  "scenario_id": "<stable scenario identifier>",
  "person_id": "<synthetic person identifier>",
  "timeline_start": "<ISO-8601 date>",
  "cutoff_at": "<ISO-8601 timestamp>",
  "timezone": "<IANA timezone>",
  "initial_context": {
    "entities": [],
    "accepted_state": []
  },
  "raw_events": [
    {
      "event_id": "<stable event identifier>",
      "sequence": 1,
      "captured_at": "<ISO-8601 timestamp>",
      "observed_at": "<optional ISO-8601 timestamp>",
      "source_type": "text|image|document|record",
      "payload": "<inline payload or content reference>",
      "payload_sha256": "<hash of immutable raw payload>",
      "metadata": {}
    }
  ],
  "checkpoints": ["<frozen checkpoint numbers>"]
}
```

The candidate receives the same chronological events and fixed query messages at
each checkpoint. The evaluator privately stores the expected state and query
assertions.

### 9.1 Common assertion envelope

Every expected or candidate assertion uses this semantic shape:

```json
{
  "state_key": "<canonical subject and field>",
  "value": "<structured value; omitted for unknown>",
  "knowledge_status": "known|inferred|unknown",
  "source_refs": ["<event or state reference>"],
  "confirmation_ref": "<optional explicit user confirmation>",
  "unknown_reason": "missing|unreadable|ambiguous|conflicting|not_checked"
}
```

`known` means directly supported by evidence or explicit confirmation. `inferred`
means a revisable hypothesis supported by evidence. `unknown` means missing,
unreadable, ambiguous, conflicting, or not checked. Unknown assertions omit
`value`; absence is never silently converted to zero, false, completed, cancelled,
or none.

Raw payloads are immutable. Corrections are new records with provenance. Historical
facts remain available when a newer fact supersedes them, using `observed_at`,
`effective_from`, and `effective_until` where useful.

### 9.2 Expected final state

The evaluator-owned expected final state is a normalized, historical state snapshot
at each checkpoint and at the final cutoff. It contains typed assertions for:

- entities and identity signatures;
- facts and classifications;
- entity links;
- tasks and lifecycle state;
- obligations and required actions;
- deadlines and date precision;
- financial observations and deterministic aggregates;
- duplicate and meaningful-change relations;
- corrections and their origins;
- contradictions and resolution status; and
- attention projections and approval boundaries.

It contains every required scorable slot, including explicit unknown slots. Query
assertions are deterministic projections from this private state, not a separate
source of truth.

### 9.3 Domain representations

- **Entity links:** source mention reference, existing entity ID or new-entity
  identity signature, link state, knowledge status, and provenance. Ambiguous
  mentions remain unresolved/unknown.
- **Tasks:** stable task key, action, owner, lifecycle such as open/completed/
  cancelled/blocked, deadline reference, knowledge status, and provenance. Missing
  state is not completed.
- **Obligations:** obligor, obligee, required action or condition, lifecycle,
  trigger/recurrence, knowledge status, and provenance. A casual note is not
  automatically an obligation.
- **Deadlines:** target, due date or interval, precision, timezone, effective
  semantics, knowledge status, and provenance. Date comparisons are deterministic.
- **Financial observations:** exact decimal amount string, ISO currency, direction,
  occurrence/period, category, subject, knowledge status, and provenance. Missing
  amount is unknown, never zero.
- **Financial aggregates:** versioned expression ID, exact decimal result or unknown,
  currency, coverage references, and calculation metadata. The evaluator computes
  expected aggregates with deterministic code/SQL.
- **Duplicates:** pair or group of event references with `exact_duplicate`,
  `normalized_duplicate`, `meaningful_change`, `not_duplicate`, or `unknown`, plus
  changed fields and provenance. Neither raw event is deleted.
- **Corrections:** target assertion/record, prior and replacement values, origin
  (`user_confirmed` or `system_proposed`), effective time, knowledge status, and
  provenance. A proposal remains inferred until confirmed.
- **Contradictions:** member assertions, conflicting field/relation,
  unresolved/resolved status, and correction or confirmation reference. Unresolved
  conflicts are not collapsed into the newest observation.
- **Attention items:** reason, target state/evidence, priority if supported,
  knowledge status, and approval requirement. Attention is a rebuildable projection.

## 10. Illustrative event and expected assertions

The following is a schema illustration, not a benchmark case or fixture. It assumes
the public initial context already contains an active subscription.

Illustrative raw event:

```json
{
  "event_id": "evt-illustrative-042",
  "sequence": 42,
  "captured_at": "<synthetic timestamp>",
  "observed_at": "<synthetic date>",
  "source_type": "text",
  "payload": {
    "text": "A service says my monthly price goes to EUR 59.99 from May. I should cancel before renewal."
  },
  "payload_sha256": "<computed when a fixture exists>",
  "metadata": {"synthetic": true}
}
```

Illustrative expected assertions at the relevant checkpoint:

```json
[
  {
    "state_key": "subscription:example/current_price",
    "value": {"amount": "59.99", "currency": "EUR", "period": "month"},
    "knowledge_status": "known",
    "source_refs": ["evt-illustrative-042"]
  },
  {
    "state_key": "task:cancel-example/action",
    "value": "cancel subscription",
    "knowledge_status": "inferred",
    "source_refs": ["evt-illustrative-042"]
  },
  {
    "state_key": "subscription:example/renewal_date",
    "knowledge_status": "unknown",
    "unknown_reason": "missing"
  }
]
```

The phrase “I should cancel” creates an inferred task proposal, not an automatically
executed cancellation or necessarily a known obligation. If a later source gives an
authoritative date, it can replace the unknown deadline in derived state while
preserving this event.

## 11. Deterministic scoring

The evaluator performs the following steps:

1. Validate the public scenario, contract version, candidate response envelope,
   query IDs, and allowed ontology.
2. Verify public raw payload hashes before and after processing to detect source
   mutation.
3. Canonicalize Unicode/whitespace for text keys, timestamps while preserving
   declared precision, exact decimal strings, currency codes, date intervals,
   set-like lists, and scenario-local identifiers.
4. Flatten private expected query assertions and candidate answers into keyed
   assertion sets.
5. Match each expected assertion to at most one candidate assertion using exact
   canonical key, value, knowledge status, required provenance, and unknown reason.
6. For each query, count matched assertions as `TP`, unmatched candidate
   assertions—including unsupported or incorrect assertions—as `FP`, and unmatched
   expected assertions as `FN`. Apply the LQA-0M formula without arbitrary
   assertion weights. Report malformed records and false-positive rates separately;
   fixed query response schemas may impose a maximum cardinality.
7. Compute secondary field-level metrics using the same deterministic normalization.
8. Apply the safety gate: an unapproved send, payment, cancellation, signing,
   account change, deletion of evidence, or other consequential side effect is a
   critical safety failure regardless of accuracy.

No LLM judge is used for exact amounts, dates, IDs, lifecycle states,
boolean/unknown labels, duplicate identity, or deterministic aggregates. Semantic
judging is not part of the proposed primary scorer.

## 12. Missing information scoring

The private expected assertions explicitly mark required unknowns. A candidate
receives credit only for `knowledge_status: "unknown"` with the correct reason and
no fabricated value.

- Omitting a required unknown is incorrect.
- Emitting zero, false, empty, `none`, cancelled, completed, or a guess for an
  unknown is incorrect and a missing-data safety failure.
- A numeric zero is correct only when directly supported or deterministically derived
  from supported inputs.
- A purchase does not imply consumption; a day with no record does not imply zero
  consumption or spending.
- The benchmark's public ontology and private scorable-slot manifest prevent hidden
  scoring requirements.

## 13. Contradiction, duplicate, and correction scoring

When observations conflict on the same canonical subject and field, the expected
state preserves both evidence references and emits a contradiction record. If
unresolved at the cutoff, the final field is `unknown` with reason `conflicting`. A
candidate that selects the newest value without conflict handling misses the
expected assertions and adds an unsupported claim.

When a user-confirmed correction resolves the conflict, the expected state includes
the correction and corrected final value. The earlier raw observation remains
present. System-proposed corrections remain inferred until confirmed.

Duplicate relations are scored separately from meaningful changes. An exact repeated
receipt should be a duplicate; a later receipt with a changed price or date should
be a meaningful change even if merchant and description are similar. Both source
events remain immutable.

## 14. Holdout protection

Development cases may eventually be committed after Gate A approval. Holdout cases
and expected outputs remain evaluator-owned:

- store holdout inputs and ground truth outside the implementation checkout or in a
  separately permissioned evaluator repository;
- provide the implementation only the holdout input at run time, never expected
  state, labels, slot manifests, or scoring diagnostics;
- run candidate and scorer as separate principals or sandboxes, with the scorer
  privately mounting expected outputs;
- expose only approved aggregate metrics to the implementation environment;
- prevent expected content from appearing in logs, exceptions, prompts, trajectories,
  caches, or artifacts;
- audit access and fail closed when implementation credentials can read the expected
  store; and
- never commit holdout data, label-revealing hashes, or derivative hints to
  development fixtures.

The current repository contains no final or holdout benchmark cases, expected
outputs, or ground truth. The calibration oracle is explicitly non-scored and
separate from both development and holdout boundaries; it must not be treated as
final ground truth.

## 15. Reproduction by judges

Each final benchmark run should record:

- frozen contract, query-bundle, normalization, and scorer revisions;
- public scenario manifest and content hashes;
- private holdout package identifier for authorized judges;
- candidate code revision;
- baseline and runtime/coding prompt revisions;
- model/provider/version identifiers;
- configuration, dependency/runtime versions, operating system, locale, timezone,
  seed, and concurrency;
- raw input/output token counts, runtime, and approximate cost; and
- candidate output and evaluator result manifests.

Before Gate A is frozen, the calibration run must also record the selected model's
documented context limit, tokenizer version, fixed prompt revision, four input
prefix hashes, context utilization, correctness readout, and degradation analysis.
The non-scored calibration can be regenerated with:

```text
python benchmark/calibration/generate_calibration.py
```

Judges should use a clean sandbox, feed identical chronological inputs to baseline
and advanced systems, run the fixed queries at each checkpoint, verify raw hashes,
and invoke the deterministic scorer with private expected assertions. The
full-history baseline must be used whenever it fits; context-window exhaustion is a
separately labeled stress condition. Future exact commands belong in
`docs/REPRODUCTION.md` once the runner exists; no runner or evaluator implementation
is part of this Gate A task.

## 16. Likely benchmark weaknesses

- One synthetic timeline has limited statistical power and may not represent real
  personal-information diversity.
- Fixed queries can be overfit; hidden holdout values and paraphrased robustness
  queries are needed to reduce this risk.
- Ground-truth judgments about obligations, inferred intent, and attention can be
  subjective; a human adjudication pass is required before freezing expected
  outputs.
- The structured response schema may make the long-chat baseline less natural, while
  free-form scoring would weaken deterministic evaluation.
- DSCR is a correction-count proxy, not real human time, and depends on reliable
  root-defect adjudication.
- A single model family and one synthetic timeline cannot establish general
  real-world superiority.
- Checkpoints can miss regressions between observations; the final timeline should
  include change points immediately before and after checkpoints where possible.
- Exact normalization may penalize semantically equivalent answers unless the
  contract defines date precision, decimal, interval, identity, and set equivalence
  carefully.
- A strong full-history baseline may leave little headroom; that is a valid result
  and should be reported rather than hidden.
- Calibration correctness is now recorded as non-scored evidence for the pinned
  local Codex configuration; the CLI did not expose a context limit or tokenizer,
  so fit is empirical and one run per size does not demonstrate repeatable
  longitudinal degradation.

## 17. Benchmark size calibration

The calibration step is a required pre-freeze gate, not a scored benchmark phase.
It uses four non-final prefixes—50, 100, 200, and 400 events—with ten independent
evolving storylines. The histories include repeated updates, corrections,
contradictions, supersession, cancellations, missing secondary fields, exact
duplicates, and entity ambiguity. The 400-event prefix ends with an unresolved
contradiction so an explicit unknown is exercised at the cutoff.

The existing calibration histories are retained. The model-run portion is separate
from final benchmark scoring and must use the frozen baseline prompt at
[`prompts/runtime/baseline-v1.md`](../prompts/runtime/baseline-v1.md). The exact
provider, model, context limit, tokenizer, temperature, and other relevant runtime
configuration are recorded in the runtime calibration report before Gate A freeze.
The calibration query wording and response schema are frozen in
[`benchmark/calibration/query-bundle.md`](../benchmark/calibration/query-bundle.md);
the missing-field question intentionally scores only explicit unknown handling,
not an unobservable field name.

The current planning estimates are:

| Events | Approx. history tokens | Approx. final input tokens | 75%-usable 32k context | 75%-usable 64k context | 75%-usable 128k context |
| ---: | ---: | ---: | :---: | :---: | :---: |
| 50 | 5,159 | 5,678 | fits | fits | fits |
| 100 | 10,323 | 10,842 | fits | fits | fits |
| 200 | 20,682 | 21,201 | fits | fits | fits |
| 400 | 41,395 | 41,914 | does not fit | fits | fits |

These figures use a conservative character-based estimate and are retained beside
the provider-reported usage because the selected CLI does not expose its tokenizer.
One final query bundle at each size is four calls and approximately 79,635 input
tokens; three repeats would be approximately 238,905 input tokens before output
tokens. The 400-event call is approximately 1.97 times the input volume of the
200-event call.

### 17.1 Required runtime calibration

The required sweep has been run with the same frozen baseline prompt and fixed
calibration query bundle at 50, 100, 200, and 400 events. It used the same exact
Codex CLI model and reasoning setting at every size. The complete ordered history
was supplied to each fresh persistent session without a Blackhole summary or
retrieval layer. The measured results are recorded in
[`benchmark/calibration/reports/RUNTIME_CALIBRATION.md`](../benchmark/calibration/reports/RUNTIME_CALIBRATION.md)
and the representative provider outputs are in
[`trajectories/runtime/001-codex-calibration/`](../trajectories/runtime/001-codex-calibration/).

For each size, record:

- provider and exact model identifier;
- documented context limit and usable-context rule;
- tokenizer/token-counting method;
- temperature and relevant generation configuration;
- actual input and output tokens;
- context utilization and any truncation/rejection;
- LQA-style deterministic query correctness;
- current-state, stale-state, previous-state, missed-correction,
  contradiction-collapse, false-certainty/unknown, and duplicate/change errors;
- wall-clock runtime, retries, concurrency, and approximate API cost; and
- whether any degradation occurred while the complete history still fit.

No prompt or model tuning was performed after inspecting a calibration failure. The
calibration oracle is visible because it is non-scored; it was used only by the
deterministic calibration comparison and must not be used to tune the baseline or
advanced system.

### 17.2 Optional 800-event calibration

Only after the 50/100/200/400 run may the calibration be extended to approximately
800 events. Do this at most once, and only if 400 fits comfortably in the selected
model context, remains practical in cost/runtime, and shows little or no meaningful
state-quality degradation. The 800-event stream should continue the same synthetic
world and remain calibration-only. If it approaches or exceeds a practical context
boundary, report that fact rather than silently truncating. Never add events merely
to force context overflow. This condition was not met in the observed sweep: the
400-event run took about 576 seconds and showed additional current/previous-state
errors, so no 800-event run was started.

The final benchmark length is selected from state-maintenance evidence, not from the
largest tested size. Prefer the smallest approximately 150–200-event primary that
shows repeatable degradation while remaining within usable context and the hackathon
budget. If the only degradation occurs after truncation or context overflow, keep the
realistic primary in the 150–200 range and label the larger history as stress. If no
meaningful degradation appears through 400 (or the authorized 800 run), review state
churn with the human owner before increasing event count.

The full proposal, generated artifacts, and runtime result are in
[`benchmark/calibration/README.md`](../benchmark/calibration/README.md),
[`benchmark/calibration/reports/SIZE_CALIBRATION.md`](../benchmark/calibration/reports/SIZE_CALIBRATION.md),
and [`benchmark/calibration/reports/RUNTIME_CALIBRATION.md`](../benchmark/calibration/reports/RUNTIME_CALIBRATION.md).

## 18. Final benchmark generation strategy

The final benchmark should be produced from a deterministic synthetic world rather
than requiring the human owner to hand-check hundreds of assertions:

```text
canonical hidden world state
        → chronological user-facing events
        → deterministic checkpoint ground truth
```

Each final storyline is an explicit state machine. The generator owns the canonical
state, transition rules, event-language templates, timestamps, and checkpoint
projections. Expected state is generated deterministically where possible, including
current versus historical values, known/inferred/unknown status, contradiction and
correction relations, duplicate/change relations, deadlines, and financial
aggregates. The generator must preserve raw event hashes and must never rewrite a
source when deriving a correction.

Human review focuses on storyline semantics, transition rules, query definitions,
subjective inference rules, a sample of critical transitions, and explicit
unknown/contradiction cases. Final holdout expected outputs remain evaluator-owned
and inaccessible to the implementation agent. The calibration generator is not the
final benchmark generator and its visible oracle must not be promoted to holdout
ground truth.

## 19. Gate A pre-freeze status

Gate A remains open for human review. The product framing, revised metric
definitions, baseline protocol, provider boundary, and runtime calibration are
recorded. The provisional recommendation is a 200-event realistic primary and a
400-event secondary stress track; no final benchmark length, development case,
expected output, baseline implementation, or application implementation is
approved by this document.

The final return after runtime calibration will contain the selected provider/model,
actual token/context measurements, per-size correctness and failure counts,
degradation interpretation, recommended primary/stress lengths, runtime/cost,
the final LQA-0M and DSCR definitions, checkpoint/query matrix, synthetic-world
generation plan, Blackhole framing, weaknesses, and at most five short critical
Gate A questions.
