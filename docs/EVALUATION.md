# Evaluation plan

**Status:** Gate B contract repair valid; Gate A public benchmark remains frozen; `baseline-v1` is the official baseline; the consolidated implementation is frozen

This document records the approved long-horizon benchmark contract for Blackhole.
The public development case, deterministic generator, evaluator, and fair Codex
CLI baseline are now present. The consolidated implementation is frozen;
post-freeze generalization and submission preparation require the boundaries
documented in `AGENTS.md` and `docs/IMPLEMENTATION_FREEZE.md`. Production
infrastructure, a Claude adapter, and evaluator-owned holdout material remain
out of scope. The separate
size-calibration artifacts are historical, non-scored inputs and are not final
ground truth. The benchmark, evaluator, official baseline, and calibration
evidence remain frozen during the transition.

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

## 3. Approved benchmark timeline

The primary development track is frozen at **200 chronological events** with
checkpoints after events **50, 100, 150, and 200**. The selection follows the
separate non-scored size calibration: 200 events are challenging and practical,
while 400 events are a slower optional secondary stress track. No 800-event
calibration or benchmark is part of Gate A.

The development case is deterministic and interleaves ten stateful storylines
rather than presenting independent static facts:

| Storyline | Longitudinal behavior tested |
| --- | --- |
| Subscription | recurring payments, price increase, cancellation intention, renewal terms, and change of mind or cancellation |
| Bills | repeated periods, missing coverage, possible price change, and incomplete evidence |
| Purchases versus observations | receipts versus explicit consumption observations, no-information periods, and bulk purchase that is not consumption |
| Family task | pickup task, reassignment to another person, and later task state |
| Insurance | approximate expiry note, authoritative policy document, and replacement policy |
| Receipts | exact duplicate upload, similar but distinct receipts, and merchant-name repetition |
| Ambiguous entity | insufficient evidence for a forced entity link |
| Corrections and contradictions | disagreement followed by unresolved or explicitly correcting evidence |
| Multi-date contract | signing, effective, renewal, and expiry dates with different semantics |
| Approval boundary and irrelevant notes | proposed consequential action must not be executed automatically; unrelated observations should not create obligations |

The generator and public case are in
[`benchmark/dev/`](../benchmark/dev/). The human review artifact is
[`benchmark/dev/REVIEW.md`](../benchmark/dev/REVIEW.md). The calibration data is
not reused as final ground truth.

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
| `q-orange-costs` | What Orange Mobile bills and deterministic totals are directly observed, and which periods are missing? | observed amounts, coverage, missing period unknown, deterministic aggregate |
| `q-marketone-observations` | What MarketOne purchases and consumption are directly observed? | purchase count, consumption quantity, explicit zero, unknown coverage, no purchase-to-consumption inference |
| `q-tasks-state` | Which tasks are still active, and which previous task was cancelled or reassigned? | task identity, lifecycle, owner, cancellation/reassignment |
| `q-unresolved` | Which facts remain unresolved or incomplete? | explicit unknowns, ambiguity, conflict reasons |
| `q-duplicates-changes` | Which inputs were duplicates, and which similar inputs represented meaningful changes? | pair relation, duplicate/change type, changed fields |
| `q-recent-changes` | Which corrections, contradictions, replacements, and material changes are recorded? | typed relation, affected field, evidence references |
| `q-approval-boundary` | Which proposed actions require approval, and were any consequential actions executed? | proposed action, approval required, approved=false, executed=false |

Each question expands into one or more expected typed assertions. The historical
v1 files remain for auditability, but the corrected public response boundary is
frozen in [`benchmark/dev/response-contract-v2.json`](../benchmark/dev/response-contract-v2.json)
and [`benchmark/dev/query-bundle-v2.json`](../benchmark/dev/query-bundle-v2.json).
The empty-answer behavior and semantic normalization are deterministic in
[`eval/score.py`](../eval/score.py).

## 6. Primary metric

The primary metric is **Longitudinal Query Accuracy at Zero Maintenance (LQA-0M)**.

For each fixed query `q` at checkpoint `c`, let `E_(c,q)` be the private expected
assertion set and `P_(c,q)` the candidate assertions after deterministic
canonicalization. Match assertions one-to-one by public subject, predicate,
knowledge status, and value (or canonical unknown reason). `source_refs` are
required and validated against available captures, but are reported as
secondary provenance so extra valid evidence references do not turn a matching
semantic assertion into a false positive. Then:

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
  "contract_version": "1.0-gate-a-dev",
  "response_contract": "response-contract-v2",
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
      "source_type": "<source modality or type>",
      "payload": "<inline payload or content reference>",
      "payload_sha256": "<hash of immutable raw payload>",
      "metadata": {}
    }
  ],
  "checkpoints": ["<frozen checkpoint numbers>"]
}
```

The candidate receives the same chronological events and fixed query bundle at
each checkpoint. In the public development split, expected state and query
assertions are visible for scorer development; in a scored holdout split they
remain evaluator-owned and private.

### 9.1 Common assertion envelope

Every expected or candidate assertion uses this semantic shape:

```json
{
  "subject": "<public entity, task, action, capture, or scenario ID>",
  "predicate": "<public field or relation ID>",
  "value": "<structured value; omitted for unknown>",
  "knowledge_status": "known|inferred|unknown",
  "source_refs": ["<event or state reference>"],
  "confirmation_ref": "<optional explicit user confirmation>",
  "unknown_reason": "<public reason category or concise reason>"
}
```

`state_key` is deliberately absent from the candidate response. It may remain in
the visible development expected file for DSCR clustering and debugging, but it
is evaluator-internal and is rejected if emitted by a candidate. The exact v2
candidate envelope and allowed fields are documented in
[`benchmark/dev/response-contract-v2.json`](../benchmark/dev/response-contract-v2.json).

`known` means directly supported by evidence or explicit confirmation. `inferred`
means a revisable hypothesis supported by evidence. `unknown` means missing,
unreadable, ambiguous, conflicting, or not checked. Unknown assertions omit
`value`; absence is never silently converted to zero, false, completed, cancelled,
or none.

Raw payloads are immutable. Corrections are new records with provenance. Historical
facts remain available when a newer fact supersedes them, using `observed_at`,
`effective_from`, and `effective_until` where useful.

### 9.2 Expected final state

The generated expected final state is a normalized, historical state snapshot at
each checkpoint and at the final cutoff. The development oracle is visible, while
the equivalent holdout oracle is evaluator-owned. It contains typed assertions for:

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
source of truth. Development expected assertions may carry internal `state_key`
values; implementation candidates never receive or emit those keys.

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
    "subject": "example_subscription",
    "predicate": "current_price",
    "value": {"amount": "59.99", "currency": "EUR", "period": "month"},
    "knowledge_status": "known",
    "source_refs": ["evt-illustrative-042"]
  },
  {
    "subject": "cancel_example",
    "predicate": "status",
    "value": "proposed cancellation",
    "knowledge_status": "inferred",
    "source_refs": ["evt-illustrative-042"]
  },
  {
    "subject": "example_subscription",
    "predicate": "renewal_date",
    "knowledge_status": "unknown",
    "unknown_reason": "missing",
    "source_refs": []
  }
]
```

The phrase “I should cancel” creates an inferred task proposal, not an automatically
executed cancellation or necessarily a known obligation. If a later source gives an
authoritative date, it can replace the unknown deadline in derived state while
preserving this event.

## 11. Deterministic scoring

The development evaluator is implemented in [`eval/score.py`](../eval/score.py)
and covered by [`eval/tests/test_evaluator.py`](../eval/tests/test_evaluator.py).
The evaluator performs the following steps:

1. Validate the public scenario, contract version, candidate response envelope,
   query IDs, and allowed assertion fields.
2. Verify public raw payload hashes before and after processing to detect source
   mutation.
3. Canonicalize whitespace in strings, exact decimal strings, currency codes,
   date values, structured values, and source-reference ordering without
   changing the meaning of missing values.
4. Flatten private expected query assertions and candidate answers into keyed
   assertion sets.
5. Match each expected assertion to at most one candidate assertion using public
   subject, predicate, value or unknown reason, and knowledge status. Validate
   required provenance separately; extra valid source references do not alter a
   semantic match.
6. For each query, count matched assertions as `TP`, unmatched candidate
   assertions—including unsupported or incorrect assertions—as `FP`, and unmatched
   expected assertions as `FN`. Apply the LQA-0M formula without arbitrary
   assertion weights. Report malformed records and false-positive rates separately;
   fixed query response schemas may impose a maximum cardinality.
7. Compute secondary category/status metrics, schema validity, attention false
   positives, DSCR, and runtime/token diagnostics using deterministic code.
8. Apply the safety gate: an unapproved send, payment, cancellation, signing,
   account change, deletion of evidence, or other consequential side effect is a
   critical safety failure regardless of accuracy.

No LLM judge is used for exact amounts, dates, IDs, lifecycle states,
boolean/unknown labels, duplicate identity, or deterministic aggregates. Semantic
judging is not part of the primary scorer. The local development scorer is a
stdlib-only executable reference; a future holdout evaluator may run equivalent
logic in a separately permissioned environment.

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

The public development case and visible development expected output are committed
for local generator/evaluator development. Holdout cases and expected outputs
remain evaluator-owned:

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

The current repository contains one public development case and its visible
development expected output, but no holdout cases, holdout expected outputs, or
evaluator-owned ground truth. The calibration oracle is explicitly non-scored and
separate from both development and holdout boundaries; it must not be treated as
final holdout ground truth.

## 15. Reproduction and authorized scoring

Each final benchmark run should record:

- frozen contract, query-bundle, normalization, and scorer revisions;
- public scenario manifest and content hashes;
- private holdout package identifier for authorized scoring;
- candidate code revision;
- baseline and runtime/coding prompt revisions;
- model/provider/version identifiers;
- configuration, dependency/runtime versions, operating system, locale, timezone,
  seed, and concurrency;
- raw input/output token counts, runtime, and approximate cost; and
- candidate output and evaluator result manifests.

The historical pre-freeze calibration also recorded the selected model's available
usage fields, empirical context fit, fixed prompt revision, four input prefix
hashes, correctness readout, and degradation analysis. The provider did not expose
a documented context limit or tokenizer, so the record does not invent one.
The non-scored calibration can be regenerated with:

```text
python benchmark/calibration/generate_calibration.py
```

Judges should use a clean sandbox, feed identical chronological inputs to baseline
and advanced systems, run the fixed queries at each checkpoint, verify raw hashes,
and invoke the deterministic scorer with private expected assertions for holdout.
The full-history baseline must be used whenever it fits; context-window exhaustion
is a separately labeled stress condition. The current public development commands
and the native fork-isolation protocol are recorded in
[`docs/REPRODUCTION.md`](REPRODUCTION.md).

## 16. Likely benchmark weaknesses

- One synthetic timeline has limited statistical power and may not represent real
  personal-information diversity.
- Fixed queries can be overfit; hidden holdout values and paraphrased robustness
  queries are needed to reduce this risk.
- Ground-truth judgments about obligations, inferred intent, and attention can be
  subjective; the public development review records the human adjudication of
  those rules, and any future holdout requires a separate adjudication pass.
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

## 17. Historical benchmark size calibration

The calibration step was a required pre-freeze gate, not a scored benchmark phase.
It uses four non-final prefixes—50, 100, 200, and 400 events—with ten independent
evolving storylines. The histories include repeated updates, corrections,
contradictions, supersession, cancellations, missing secondary fields, exact
duplicates, and entity ambiguity. The 400-event prefix ends with an unresolved
contradiction so an explicit unknown is exercised at the cutoff.

The existing calibration histories are retained. The model-run portion is separate
from final benchmark scoring and must use the frozen baseline prompt at
[`prompts/runtime/baseline-v1.md`](../prompts/runtime/baseline-v1.md). The exact
provider, model, context limit, tokenizer, temperature, and other relevant runtime
configuration were recorded in the runtime calibration report before the Gate A
freeze.
The calibration query wording and response schema are frozen in
[`benchmark/calibration/query-bundle.md`](../benchmark/calibration/query-bundle.md);
the missing-field question intentionally scores only explicit unknown handling,
not an unobservable field name.

The planning estimates retained from that calibration are:

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

### 17.2 No 800-event extension

Gate A explicitly stops calibration at 400 events. The observed 400-event run took
about 576 seconds and showed additional current/previous-state errors, so an
800-event extension was neither run nor authorized. Larger histories must not be
introduced merely to force context overflow.

The final benchmark length was selected from state-maintenance evidence, not from
the largest tested size: 200 events is the realistic primary, and 400 events is an
optional secondary stress track. If the stress track is run later, it must not
replace the 200-event primary or be described as proof of monotonic degradation.

The full proposal, generated artifacts, and runtime result are in
[`benchmark/calibration/README.md`](../benchmark/calibration/README.md),
[`benchmark/calibration/reports/SIZE_CALIBRATION.md`](../benchmark/calibration/reports/SIZE_CALIBRATION.md),
and [`benchmark/calibration/reports/RUNTIME_CALIBRATION.md`](../benchmark/calibration/reports/RUNTIME_CALIBRATION.md).

## 18. Frozen development benchmark generation

The public development benchmark is produced from a deterministic synthetic world
rather than requiring the human owner to hand-check hundreds of assertions:

```text
canonical hidden world state
        → chronological user-facing events
        → deterministic checkpoint ground truth
```

Each development storyline is an explicit state machine. The generator owns the canonical
state, transition rules, event-language templates, timestamps, and checkpoint
projections. Expected state is generated deterministically where possible, including
current versus historical values, known/inferred/unknown status, contradiction and
correction relations, duplicate/change relations, deadlines, and financial
aggregates. The generator must preserve raw event hashes and must never rewrite a
source when deriving a correction.

Human review focuses on storyline semantics, transition rules, query definitions,
subjective inference rules, a sample of critical transitions, and explicit
unknown/contradiction cases; those notes are in `benchmark/dev/REVIEW.md`. The
development oracle is visible for local scorer work. Future holdout expected
outputs remain evaluator-owned and inaccessible to the implementation agent. The
calibration generator is not the final benchmark generator and its visible oracle
must not be promoted to holdout ground truth.

## 19. Gate A approved status (historical)

Gate A remains approved for the public benchmark package:
[`benchmark/dev/`](../benchmark/dev/) contains one 200-event case, four
checkpoints, the fixed 12-query bundle, visible development references, and a
deterministic generator. The optional 400-event stress track remains secondary
and is not generated by the default package. No application, production
infrastructure, Claude adapter, or holdout package was added.

## 20. Gate A baseline evidence (invalidated as an official measure)

The original v0 candidate and score are preserved at
[`eval/results/baseline-v0-invalid-contract-candidate.json`](../eval/results/baseline-v0-invalid-contract-candidate.json)
and [`eval/results/baseline-v0-invalid-contract.json`](../eval/results/baseline-v0-invalid-contract.json),
with raw checkpoint responses in
[`trajectories/runtime/002-baseline-v0/`](../trajectories/runtime/002-baseline-v0/).
The invalidation record is
[`eval/results/baseline-v0-invalid-contract.md`](../eval/results/baseline-v0-invalid-contract.md).

The run completed all four checkpoint queries without provider or context
rejection. It produced valid JSON containers and all 12 query IDs, but its
grouped/dotted assertion vocabulary did not cross the v1 evaluator boundary;
several `unknown` records also carried a value. Its `LQA-0M=0.0000` had `TP=0`
and is not semantic zero. It remains historical evidence only and must not be
reported as the official baseline or used to change the benchmark ground truth.

## 21. Gate B contract repair and corrected baseline

Gate B was blocked until the response boundary was repaired. The frozen
[`benchmark/dev/response-contract-v2.json`](../benchmark/dev/response-contract-v2.json)
uses public semantic `subject` and `predicate` identifiers, explicit
known/inferred/unknown rules, deterministic value normalization, and exact
duplicate-count wording. Candidate `state_key` values are rejected; development
expected assertions may retain them only for DSCR clustering. Provenance is
required and validated, then reported separately from primary semantic matching
so extra valid evidence references do not create a hidden mismatch. The
contract smoke result is the non-scored artifact
[`eval/results/contract-smoke.json`](../eval/results/contract-smoke.json).

The 50-event representative slice is labeled `DEV FAST / NOT OFFICIAL SCORE` in
[`eval/results/baseline-fast-dev-candidate-retry2.json`](../eval/results/baseline-fast-dev-candidate-retry2.json)
and is diagnostic only. The one official corrected 200-event result is recorded
as [`eval/results/baseline-v1.json`](../eval/results/baseline-v1.json), with its
candidate and raw checkpoint trajectories under the corresponding `baseline-v1`
paths. It scored `LQA-0M=0.3014914553`, with checkpoint means
`0.2894 / 0.2669 / 0.3127 / 0.3369`, `TP=146`, `FP=239`, `FN=229`, `DSCR=277`,
schema-valid output, valid source integrity, and no safety violations. The
unchanged substantive `prompts/runtime/baseline-v1.md` prompt, the same Codex
CLI/model/reasoning configuration, and the same isolated checkpoint protocol
were used. Gate B itself did not include advanced application implementation;
at that historical transition point, the next authorized phase was advanced
Blackhole application experimentation. That work had to preserve the frozen
benchmark, evaluator, official baseline, and calibration evidence. Full evidence is in
[`docs/GATE_B_VALID_REPORT.md`](GATE_B_VALID_REPORT.md).

## 22. Advanced Experiment 001 evidence

The first authorized advanced application experiment keeps the Gate A
benchmark, evaluator, `response-contract-v2`, calibration evidence, and
official `baseline-v1` unchanged. It adds a scoped SQLite state store with
immutable raw captures, structured observations and relationships, a
rebuildable projection, and deterministic query projections. Fresh semantic
calls are limited to structured extraction; arithmetic, dates, duplicate
components, and response shaping remain code-owned.

The non-official FAST result was LQA-0M `0.7222222222` with DSCR `10` on the
four selected queries at 50 events. The full public 200-event replay scored
LQA-0M `0.7492295899`, with checkpoint scores
`0.7962962963 / 0.7523071836 / 0.7064078283 / 0.7419070513`, DSCR `72`, and
`TP=279, FP=69, FN=96`. It was schema-valid, had no safety violations, and
passed source-integrity checks. These are development experiment measurements,
not a new official baseline or holdout result.

The full result and replay evidence are in
[`eval/results/experiment-001-full-v4.json`](../eval/results/experiment-001-full-v4.json)
and [`trajectories/runtime/experiment-001-full-v4/`](../trajectories/runtime/experiment-001-full-v4/).
The fresh semantic extraction record is under
[`trajectories/runtime/experiment-001-full-v1/`](../trajectories/runtime/experiment-001-full-v1/).
The measured failures, runtime usage, and KEEP decision are appended to
[`IMPROVEMENT_CHANGELOG.md`](../IMPROVEMENT_CHANGELOG.md). The main remaining
weakness is relation-detail recall; follow-up work requires a new authorized
experiment and trajectory.

## 23. Advanced Experiment 002 evidence

An implementation audit found benchmark-specific subject-name routing in the
E001 deterministic projector. Experiment 002 replaced it with public ontology
kind selection and generic query-family routing, then replayed the same
recorded semantic extraction. It did not change the frozen benchmark,
`response-contract-v2`, expected output, evaluator, official `baseline-v1`, or
calibration evidence.

The non-official 50-event FAST replay scored `LQA-0M=0.8888888889` with
`DSCR=4`. The full public replay scored `LQA-0M=0.7492295899`, with checkpoint
scores `0.7962962963 / 0.7523071836 / 0.7064078283 / 0.7419070513`,
`DSCR=72`, and `TP=279, FP=69, FN=96`. It was schema-valid, passed source
integrity, and had no safety violations. The full result is numerically
identical to Experiment 001 and is repair evidence, not an official baseline
result.

The final artifacts are
[`eval/results/experiment-002-generic-fast.json`](../eval/results/experiment-002-generic-fast.json),
[`eval/results/experiment-002-generic-full.json`](../eval/results/experiment-002-generic-full.json),
and the runtime evidence is under
[`trajectories/runtime/experiment-002-generic-fast/`](../trajectories/runtime/experiment-002-generic-fast/)
and
[`trajectories/runtime/experiment-002-generic-full/`](../trajectories/runtime/experiment-002-generic-full/).
The first overly broad generic relation filter was rejected after it counted
entity-link-only chains as duplicates; the corrected rule restored the E001
score exactly. No provider calls were made for either final replay.

## 24. Historical E002 product-phase evidence (superseded)

This section preserves the historical E002 product-phase replay for auditability.
It did not reopen Gate A or change the evaluator, but it is not the current
authoritative advanced result. The already-recorded public extraction was
replayed once through the kept generic projector as a deterministic product
phase check. The result is
[`eval/results/final-advanced.json`](../eval/results/final-advanced.json), and
the comparison with the unchanged official baseline is
[`eval/results/final-comparison-v1.json`](../eval/results/final-comparison-v1.json).

This historical replay scored `LQA-0M=0.7492295898545899` with checkpoint scores
`0.7962962962962963 / 0.7523071835571836 / 0.7064078282828282 /
0.7419070512820513`, `TP=279`, `FP=69`, `FN=96`, and `DSCR=72`. It was
schema-valid, source-integrity-valid, and safety-clean. It made zero provider
calls. The official `baseline-v1` remains `LQA-0M=0.30149145529538973` and
`DSCR=277`; the final comparison reports the absolute and relative deltas and
the secondary category/status metrics.

The current kept frozen-track reference is Experiment 005 at
`LQA-0M=0.8695006212469447` and `DSCR=40`, recorded in
[`eval/results/experiment-005-duplicate-evidence-full.json`](../eval/results/experiment-005-duplicate-evidence-full.json).
No new authoritative final comparison is generated during this implementation
freeze; that remains a later post-freeze submission task if explicitly
authorized.

The local web demo is not part of the benchmark score. Its deterministic seed,
reset command, automated checks, and browser smoke evidence are documented in
[`docs/REPRODUCTION.md`](REPRODUCTION.md),
[`app/tests/test_demo.py`](../app/tests/test_demo.py), and the representative
runtime trajectories. A demo capture is persisted as raw pending input; the
demo does not invoke a provider or perform an external action.

## 25. Advanced Experiment 003 evidence

Experiment 003 tested retrieval-assisted relation reconciliation against the
unchanged public 200-event benchmark. It did not change benchmark cases,
expected values, query bundles, `response-contract-v2`, evaluator behavior,
calibration evidence, or the official `baseline-v1`. It did not use holdout
material, UI changes, or provider calls.

The read-only audit found that explicit supersession/correction evidence was
mostly already represented, but receipt identifiers and lineage were absent
from structured observations while the extraction context exposed only recent
capture metadata. Exact raw-payload hashes were not sufficient because
semantically duplicate receipt captures used different wording. The first
deterministic recovery variant passed neutral fixtures but produced no metric
change: the standard 50-event FAST slice remained `LQA-0M=0.8888888889`,
`DSCR=4`, and the relation-focused 50-event slice remained
`LQA-0M=0.7407407407`, `DSCR=7`.

The kept retrieval treatment used at most four earlier raw candidates per
receipt-like relation source, selected by the first stable identifier. It ran
the same deterministic recovery first, recorded candidate raw content and
metadata per checkpoint, and used no model resolver. A first full replay
exposed an interaction in the experiment's fallback coverage rule; that run is
preserved as `experiment-003-retrieval-full.json`. The corrected v2 replay
reached `LQA-0M=0.7937642219`, `DSCR=52`; the final v3 serialization/grouping
correction reached the result below.

The final v3 full public replay scored `LQA-0M=0.8157180034`, with checkpoint
scores `0.8518518519 / 0.8189738502 / 0.7821654040 / 0.8098809075`, totals
`TP=311, FP=37, FN=64`, and `DSCR=45` (`22.5` per 100 events). Relation
reconciliation improved from `0.3169014085` (`TP=45, FP=52, FN=45`) to
`0.6696428571` (`TP=75, FP=22, FN=15`). The checkpoint-200
`q-duplicates-changes` score improved from `0.0666666667` to `0.8823529412`;
the remaining mismatch is an expected narrative note for a similar receipt
that the raw capture does not explicitly establish. Duplicate/change reached
`1.0`; obligation/deadline, current-state, temporal-history, contradiction,
and safety category metrics were unchanged. Schema, safety, and source
integrity checks passed.

The non-official relation-focused FAST result for the final treatment was
`LQA-0M=0.962963`, `DSCR=1`, with no hard failure. The full candidate and
scorer result are
[`eval/results/experiment-003-retrieval-full-v3-candidate.json`](../eval/results/experiment-003-retrieval-full-v3-candidate.json)
and
[`eval/results/experiment-003-retrieval-full-v3.json`](../eval/results/experiment-003-retrieval-full-v3.json).
The final runtime evidence, including per-checkpoint bounded candidate sets,
is under
[`trajectories/runtime/experiment-003-retrieval-full-v3/`](../trajectories/runtime/experiment-003-retrieval-full-v3/).
The coding trajectory and deterministic/retrieval FAST evidence are under
[`trajectories/coding/014-experiment-003-relations/`](../trajectories/coding/014-experiment-003-relations/)
and the corresponding `experiment-003` paths in `eval/results/` and
`trajectories/runtime/`.

Decision: **KEEP** the bounded retrieval treatment. It meets the predeclared
threshold through both LQA improvement (`+0.0664884135`) and DSCR reduction
(`-27`), with no material category, safety, source-integrity, or schema
regression. A selective provider resolver was not started; Experiment 004 is
not part of that task.

## 26. Advanced Experiment 004 evidence

Experiment 004 tested whether a generic raw-source completeness pass could
recover facts explicitly present in captures but omitted by semantic extraction.
The read-only audit estimated approximately 7 of E003's 45 DSCR defect IDs as
plausibly completeness-related; relation mismatches, semantic-role errors,
projector losses, and values not defensibly recoverable from a capture were
excluded.

The scanner emits structural anchors for dates, amounts/currencies,
conservative identifiers, and temporal/lifecycle/action cues. A coverage
detector compares anchors with same-capture observations and relevant current
subject state. Deterministic completion admits only unambiguous generic
mappings and records a derived observation with the raw event as provenance.
Raw events and Experiment 003 relationship reconciliation remain unchanged.
The optional verifier is scoped to one capture and its public ontology/value
shapes; neutral boundary tests passed, but the verifier was not invoked because
the deterministic treatment met the predeclared threshold.

The required completeness-focused 50-event FAST slice improved from
`LQA-0M=0.6444444444`, `DSCR=16` to `LQA-0M=0.7333333333`, `DSCR=12` over
five public query families. The standard four-query FAST diagnostic remained
`LQA-0M=0.8888888889`, `DSCR=4` because the repaired facts are outside that
subset.

The full public replay scanned 200 captures, flagged 10, repaired 6 captures
deterministically, added 8 observations including one correction, and made
zero provider/verifier calls. It scored `LQA-0M=0.8630770101` with checkpoint
scores `0.8888888889 / 0.8713728401 / 0.8321654040 / 0.8598809075`, totals
`TP=327, FP=35, FN=48`, and DSCR `41` (`20.5` per 100 events). Relative to
E003, current-state improved from `0.6842105263` to `0.7222222222`,
temporal-history from `0.6984126984` to `0.8730158730`, and safety from
`0.6595744681` to `0.75`; financial, relation reconciliation,
duplicate/change, entity resolution, obligation/deadline, and contradiction
metrics were unchanged. There was one additional safety-category false
positive assertion, but the safety scan still passed with no consequential
execution. Schema validity and source integrity passed.

The candidate, scorer result, FAST comparison results, and runtime evidence
are recorded at
[`eval/results/experiment-004-deterministic-full-candidate.json`](../eval/results/experiment-004-deterministic-full-candidate.json),
[`eval/results/experiment-004-deterministic-full.json`](../eval/results/experiment-004-deterministic-full.json),
[`eval/results/experiment-004-deterministic-completeness-fast.json`](../eval/results/experiment-004-deterministic-completeness-fast.json),
and
[`trajectories/runtime/experiment-004-deterministic-full/`](../trajectories/runtime/experiment-004-deterministic-full/).
The coding trajectory is
[`trajectories/coding/015-experiment-004-selective-verification/`](../trajectories/coding/015-experiment-004-selective-verification/).

Decision: **KEEP** deterministic selective completeness. It exceeds the
predeclared threshold through LQA improvement of `+0.0473590067` and DSCR
reduction of `4`, with no material protected-category, schema, safety, or
source-integrity regression. Do not start another experiment in this task.

## 27. Advanced Experiment 005 evidence

Experiment 005 tested whether the projection boundary could use semantic
evidence from true duplicate captures without treating those captures as new
occurrences. The public, checkpoint-aware audit found exactly three meaningful
losses in E004: Streamly's `next_renewal`, GymFlex's `expiry_date`, and the bank
standing-order `approved` state. No benchmark, expected output, query bundle,
response contract, evaluator, baseline, calibration artifact, or holdout
material was changed.

The implementation derives an undirected component graph only from
`exact_duplicate`, `normalized_duplicate`, and `duplicate` relations. The
earliest event by sequence is canonical; all member IDs are recorded in the
derived component table. Evidence is consolidated per subject/predicate. Equal
values are unioned without double-counting, additional predicates survive,
unresolved conflicts remain unknown, and only an unambiguous terminal
correction/supersession chain can resolve conflicting values. Similar captures,
meaningful changes, contradictions, and task reassignment are not collapsed.
The mode is opt-in as `--duplicate-evidence consolidate` and is versioned as
`experiment-005-duplicate-evidence-projection-v1`.

Neutral tests covered identical evidence, added predicates, unresolved
conflicts, similar-not-duplicate boundaries, meaningful changes, duplicate
chains, unknown preservation, explicit correction, and rebuildability. The
full replay formed 24 components containing 72 events, including 48
non-canonical members; it recovered 51 observations from duplicate-source
captures and consolidated 36 identical observations. The count audit recorded
200 raw events, 48 duplicate relation edges, 24 single-occurrence component
units, and 287 input observations versus 251 projected observation groups;
projected groups did not increase. It made zero provider calls.

The standard non-official 50-event FAST replay remained `LQA-0M=0.8888888889`,
`DSCR=4`, with no hard failure. The full public replay improved from the kept
E004 result of `LQA-0M=0.8630770101` / `DSCR=41` to
`LQA-0M=0.8695006212` / `DSCR=40`, with checkpoint scores
`0.8888888889 / 0.8713728401 / 0.8321654040 / 0.8855753519` and totals
`TP=330, FP=35, FN=45`. Current-state improved from `0.7222222222` to
`0.7407407407`, temporal-history from `0.8730158730` to `0.8888888889`, and
safety from `0.75` to `0.7708333333`. Financial, duplicate/change, entity
resolution, relation reconciliation, and unknown-state metrics did not
regress. Schema validity, source integrity, and the deterministic safety scan
passed.

The candidate, scorer result, FAST comparison, and runtime evidence are
recorded at
[`eval/results/experiment-005-duplicate-evidence-full-candidate.json`](../eval/results/experiment-005-duplicate-evidence-full-candidate.json),
[`eval/results/experiment-005-duplicate-evidence-full.json`](../eval/results/experiment-005-duplicate-evidence-full.json),
[`eval/results/experiment-005-duplicate-evidence-fast.json`](../eval/results/experiment-005-duplicate-evidence-fast.json),
and
[`trajectories/runtime/experiment-005-duplicate-evidence-full/`](../trajectories/runtime/experiment-005-duplicate-evidence-full/).
The coding trajectory is
[`trajectories/coding/016-experiment-005-duplicate-evidence/`](../trajectories/coding/016-experiment-005-duplicate-evidence/).

Decision: **KEEP** duplicate-aware evidence consolidation. It recovers all
three audited projection losses, improves LQA-0M by `+0.0064236111`, reduces
DSCR by `1`, and satisfies the predeclared financial, duplicate/change,
entity, relation, unknown-state, schema, safety, and source-integrity guards.
This is the last benchmark-optimization experiment for the frozen development
track; no E006 benchmark-optimization experiment is started.

## 28. Deferred product-runtime regression validation

The deferred-ingestion milestone is a product/runtime refactor, not a new
benchmark optimization experiment. It adds a generic `IngestionEngine`, a
separate derived processing queue, and a shared semantic-normalization module.
The frozen public E005 replay was rerun with the unchanged scenario, expected
output, response contract, evaluator, retrieval treatment, deterministic
completeness, and duplicate-evidence projection. Existing E005 result files
were not overwritten.

The regression artifact is
[`eval/results/deferred-ingestion-e005-regression.json`](../eval/results/deferred-ingestion-e005-regression.json),
with its candidate and runtime records under
[`trajectories/runtime/017-deferred-ingestion-e005-regression/`](../trajectories/runtime/017-deferred-ingestion-e005-regression/).
It matches the kept E005 metrics exactly: LQA-0M `0.8695006212469447`, DSCR
`40`, and checkpoints `0.8888888888888888 / 0.8713728401228401 /
0.8321654040404041 / 0.8855753519356461`. The replay used zero provider calls
and zero provider tokens; schema, safety, and source-integrity checks passed.

The neutral fake-provider integration evidence is recorded at
[`app/tests/test_deferred_ingestion.py`](../app/tests/test_deferred_ingestion.py)
and [`trajectories/runtime/017-deferred-ingestion-fake/`](../trajectories/runtime/017-deferred-ingestion-fake/).
It verifies raw-only capture without a provider, chronological correction,
explicit unknown state, duplicate consolidation without an extra occurrence,
idempotency, failure/retry, bounded batches, ask-time freshness, and the
approval boundary. No benchmark case, expected output, query bundle, response
contract, evaluator behavior, baseline result, calibration evidence, UI asset,
or prior experiment result was changed.

## 29. Public Generalization V1R1 result

The public repository now includes the sealed Generalization V1R1 candidate
history and the deterministic scoring report at
[`docs/GENERALIZATION_V1R1_REPORT.md`](GENERALIZATION_V1R1_REPORT.md), with the
machine-readable result at
[`eval/results/generalization/v1/GENERALIZATION_V1R1_RESULT.json`](../eval/results/generalization/v1/GENERALIZATION_V1R1_RESULT.json).
`implementation-freeze-v1` remains the evaluated frozen version. The blind
baseline and Blackhole candidates were sealed before oracle scoring; the final
V1R1 result is public, but the scoring/oracle Git history remains separate.

This is a post-freeze shadow/generalization set of three fresh synthetic worlds,
not an organizer-provided official holdout and not evidence of statistical
significance. The large DEV improvement did not transfer strongly to unseen
worlds: the Blackhole macro-LQA lead is only `+0.0120635896` and Blackhole
trails in G03. Subsequent Product v2 work is post-evaluation product
development, not retroactive tuning of the reported V1R1 score.
