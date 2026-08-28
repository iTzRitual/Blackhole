# Evaluation plan

**Status:** Gate A benchmark proposal with size calibration, pending human approval

This document proposes a long-horizon benchmark for Life Inbox. It is design-only:
no final benchmark cases, final expected outputs, scorer, evaluator implementation,
baseline implementation, or application implementation is included. The separate
size-calibration artifacts are non-scored synthetic inputs and are not the final
benchmark.

## 1. Evaluation goal

The benchmark tests this hypothesis:

> A structured stateful agent can maintain a more trustworthy longitudinal understanding of fragmented personal information than one long general-purpose AI conversation, while requiring less human maintenance.

This is primarily a longitudinal memory and state-maintenance evaluation. It is not
primarily an OCR or isolated classification benchmark. Extraction, linking, temporal
reconciliation, uncertainty handling, and deterministic projections matter because
they affect the answers the user receives over time.

## 2. Evaluation protocol at a glance

The primary run compares two systems on the same chronological synthetic life
timeline:

1. **Fair long-chat baseline:** one general-purpose model, one personal-life-admin
   system prompt, the same chronological captures, and the complete available
   conversation history whenever it fits. It has no SQLite memory, entity database,
   external persistent state, temporal reconciliation engine, graph, or
   agent-specific memory tool.
2. **Advanced candidate:** the system under test, using the same model family where
   practical and the same chronological captures and fixed queries. It may maintain
   structured state, but any additional resources must be documented.

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
query wording, and assertion weights must be frozen before final development cases
are authored. The calibration data is not a final case and does not supply final
ground truth.

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
- **Weighted assertion:** the smallest deterministic claim in a query answer, such
  as one current subscription price, one deadline, one unresolved field, or one
  duplicate relation.

The primary measurement unit is one weighted assertion at one checkpoint. The
primary result is reported overall and at every checkpoint so accuracy can be plotted
against history length.

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
definitions, assertion keys, and weights are frozen before final benchmark
generation.

## 6. Primary metric

The primary metric is **Longitudinal Query Accuracy at Zero Maintenance (LQA-0M)**.

For checkpoint `c`, let `A_c` be the private expected assertion set, `w(a)` its
frozen weight, and `correct(p, a)` indicate an exact canonical match between the
candidate answer and expected assertion `a`.

```text
LQA_c = sum(w(a) for correct expected assertions at c)
        / sum(w(a) for all expected assertions at c)

LQA_overall = sum over all checkpoints of correct weighted assertions
              / sum over all checkpoints of expected assertion weights
```

The primary report must include one result per fixed checkpoint and `LQA_overall`.
An assertion is correct only when its canonical subject/key, predicate, value, and
`known`/`inferred`/`unknown` status match the expected answer. An expected unknown is
a valid answer.

Proposed initial weights are `2` for high-consequence current state, financial,
obligation/deadline, uncertainty, contradiction, and approval assertions, and `1`
for ordinary historical, entity, duplicate, and supporting assertions. These
weights are a Gate A decision, not a hidden implementation choice.

The previously proposed final-state MES-F1 is retained, if useful, as a secondary
diagnostic. It is not the primary success criterion because the benchmark goal is
zero-maintenance longitudinal query accuracy.

## 7. Human-maintenance metric

The secondary strategic metric is **Maintenance Interventions Required to Reach 90%
(MIR-90)**.

The primary run is first completed with zero maintenance. The evaluator then applies
a deterministic repair protocol to the normalized answer/state view:

- `ADD`: add one missing expected assertion;
- `REPLACE`: correct one wrong value, lifecycle, link, or status for an existing
  assertion key;
- `SET_UNKNOWN`: replace an unsupported certainty with the correct explicit unknown;
- `RELATE`: correct one duplicate, change, or contradiction relation; or
- `DELETE`: remove one unsupported assertion.

One intervention is one such canonical assertion repair. Expected query assertions
carry stable state keys and a private dependency map so one underlying repair can fix
repeated appearances across later queries/checkpoints; the same root repair is not
counted once per repeated question. For the stateless long-chat baseline, the same
stable answer keys are used, without pretending that it has hidden structured state.

`MIR-90` is the minimum number of allowed repairs needed for aggregate `LQA_overall`
to reach at least `0.90`. If the zero-maintenance run already reaches 90%,
`MIR-90 = 0`. If reliable root-state dependency mapping cannot be produced within
the timebox, report the simpler fallback `detected maintenance interventions after
failure`, defined as the count of distinct wrong canonical assertion keys, rather
than claiming human minutes.

This is a deterministic maintenance-burden proxy, not a claim about actual
wall-clock human time. Actual time may be reported only as exploratory evidence.

## 8. Secondary metrics

Report these separately from LQA-0M and MIR-90:

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
6. Count correct weighted assertions for LQA-0M. Report unsupported extra claims,
   malformed records, and false-positive rates separately; fixed query response
   schemas may impose a maximum cardinality.
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
- `MIR-90` is a repair-count proxy, not real human time, and depends on a reliable
  assertion-to-state dependency map.
- A single model family and one synthetic timeline cannot establish general
  real-world superiority.
- Checkpoints can miss regressions between observations; the final timeline should
  include change points immediately before and after checkpoints where possible.
- Exact normalization may penalize semantically equivalent answers unless the
  contract defines date precision, decimal, interval, identity, and set equivalence
  carefully.
- A strong full-history baseline may leave little headroom; that is a valid result
  and should be reported rather than hidden.
- Calibration correctness cannot be interpreted until the selected model, context,
  tokenizer, and fixed prompt are pinned; token estimates alone do not demonstrate
  longitudinal degradation.

## 17. Benchmark size calibration

The calibration step is a required pre-freeze gate, not a scored benchmark phase.
It uses four non-final prefixes—50, 100, 200, and 400 events—with ten independent
evolving storylines. The histories include repeated updates, corrections,
contradictions, supersession, cancellations, missing secondary fields, exact
duplicates, and entity ambiguity. The 400-event prefix ends with an unresolved
contradiction so an explicit unknown is exercised at the cutoff.

The current planning estimates are:

| Events | Approx. history tokens | Approx. final input tokens | 75%-usable 32k context | 75%-usable 64k context | 75%-usable 128k context |
| ---: | ---: | ---: | :---: | :---: | :---: |
| 50 | 4,109 | 4,611 | fits | fits | fits |
| 100 | 8,223 | 8,725 | fits | fits | fits |
| 200 | 16,482 | 16,984 | fits | fits | fits |
| 400 | 32,995 | 33,497 | does not fit | fits | fits |

These figures use a conservative character-based estimate and must be replaced by
the selected model's tokenizer before the model run. One final query bundle at each
size is four calls and approximately 63,817 input tokens; three repeats would be
approximately 191,451 input tokens before output tokens. The 400-event call is
approximately 1.97 times the input volume of the 200-event call.

The fixed-prompt calibration run should report typed query correctness and
temporal/state degradation by size. It must not change the baseline prompt or model
configuration in response to individual failures. Select the smallest approximately
150–200-event length that shows a repeatable state-quality decline while remaining
within usable context and the hackathon budget. If degradation appears only after
truncation or context overflow, keep the realistic primary in the 150–200 range and
label 400 as stress. If there is no degradation through 400, review state churn with
the human owner rather than inflating event count solely to exhaust context.

The full proposal, generated artifacts, and unresolved model-run requirement are in
[`benchmark/calibration/README.md`](../benchmark/calibration/README.md) and
[`benchmark/calibration/reports/SIZE_CALIBRATION.md`](../benchmark/calibration/reports/SIZE_CALIBRATION.md).

## 18. Gate A review status

Gate A remains open pending human review of the calibration protocol and the final
model-run evidence. No final benchmark length, development case, expected output,
baseline, or application implementation is approved by this document.

### GRILL ME — GATE A

1. Approve the non-scored 50/100/200/400 calibration dataset and the fixed-prompt
   size-selection rule?
2. Approve selecting the smallest approximately 150–200-event primary that shows
   repeatable longitudinal degradation within usable context, with 400 as a
   secondary stress track when appropriate?
3. Approve LQA-0M as primary, with critical assertions weighted 2 and ordinary
   assertions weighted 1?
4. Approve MIR-90 as the deterministic maintenance proxy, with detected-intervention
   count as the fallback?
5. Approve the fair baseline as one continuous full-history conversation using the
   same model family and fixed queries, with human adjudication of obligations,
   inferences, contradictions, and expected unknowns before final benchmark freeze?
