# Gate A benchmark proposal: long-chat, zero-maintenance revision

**Status:** DRAFT — human approval required; no benchmark freeze

This proposal responds to the current master brief. It reopens Gate A around a
single longitudinal timeline and a fair one-conversation baseline. It does not
create or modify benchmark cases, expected outputs, evaluator code, baseline
code, application code, or infrastructure.

The prior 200-event package, `response-contract-v2`, and corrected baseline
remain preserved as historical draft/execution artifacts. They are not treated
as approval of this proposal and are not silently rewritten. The prior design
commit `d5e9b40` is the original draft design artifact; the later benchmark and
baseline commits are evidence of an earlier scope, not a substitute for this
Gate A review.

The master brief calls the product **Life Inbox**; the existing repository uses
**Blackhole** as its working name. This proposal follows the brief's product
goal while leaving repository paths and naming unchanged until a separate human
product decision.

## 1. Review outcome and recommendation

The previous contract optimized for a 200-event Gate A execution and later
repair. The current brief makes the primary question narrower and more useful
for the hackathon: whether a structured stateful system maintains changing
personal state better than one long general-purpose conversation under zero
human maintenance, while the complete history remains reasonably available.

I recommend the following current Gate A target:

- **One synthetic life timeline with 100 chronological events** over roughly 90
  synthetic days.
- **Ten interleaved, high-churn storylines**, approximately ten events each.
- **Checkpoints after events 20, 40, 60, 80, and 100.**
- **One fixed query bundle at every checkpoint**, with no query answer injected
  into the continuing ingestion history.
- **A separate optional 200-event stress track** only after the primary is
  working and only if execution time permits. It must not replace the realistic
  primary or be presented as proof of context exhaustion.

One hundred is the upper end of the brief's 60–100-event range. It gives the
long-chat treatment more state transitions than a 60-event case without making
the primary benchmark a context-window endurance test. The existing
calibration is relevant caution, not proof: its 100-event state-only score was
high and its 50/100/200/400 results were non-monotonic after a single run per
size. Therefore this proposal intentionally makes state churn dense and
explicit, and treats any larger run as secondary evidence.

No final event text or expected answer is frozen until the human approves Gate
A. The proposal's examples below are illustrative only.

## 2. Hypothesis and evaluation boundary

The benchmark tests:

> A structured stateful agent can maintain a more trustworthy longitudinal
> understanding of fragmented personal information than a single long
> general-purpose AI conversation, while requiring less human maintenance.

This is a longitudinal memory and state-maintenance benchmark. It is not mainly
an OCR, vision, or classification benchmark. Receipt and document inputs in the
primary track will use synthetic text or normalized extracted content. A future
modality slice may test OCR separately without changing the primary result.

During the primary run neither system receives:

- manual categorization or organization;
- a user-provided entity link;
- a reminder of an earlier fact;
- a correction or clarification after an error;
- an answer to an earlier checkpoint query; or
- context beyond the fixed chronological captures.

This is **zero maintenance**. The benchmark measures what the system can retain,
reconcile, and answer before a human repairs it.

## 3. Fair long-chat baseline

The baseline is the strongest reasonable version of the treatment a user could
perform today:

1. Start one fresh provider-owned conversation with one frozen personal-life-
   admin system prompt.
2. Deliver the same chronological raw captures as the advanced system, in
   order, with no Blackhole database, hidden summary, retrieval layer, entity
   graph, temporal reconciler, or special memory tool.
3. Use one user message per capture where the provider permits it, preserving
   event order and raw wording. A harness may add only stable transport
   metadata such as the public event ID; it may not add expected labels.
4. At each checkpoint, fork or snapshot the canonical conversation, ask the
   fixed query bundle in the isolated read-only child, save the response, and
   discard the child. The canonical conversation receives no query answer.
5. Supply the complete available history whenever technically possible. Do not
   truncate the primary merely to fit a target context size. If the history
   exceeds the selected model's usable context, record that as a separate
   stress condition and report the primary condition honestly.

The advanced system receives the same raw events, query wording, checkpoint
cutoffs, and semantic response contract. It may use structured state only as
the experimental treatment. The exact provider/model/reasoning configuration
will be pinned before execution and used for both systems where practical. Any
resource difference, token count, latency, context behavior, or cost difference
must be reported.

## 4. Proposed timeline and storylines

The timeline is one fictional person's inbox. Events are distributed over
approximately 90 days with realistic gaps for particular subjects. Ten rounds
of interleaving provide about ten events per storyline; dates and event density
are not themselves labels. A quiet period for one subject must not become a
zero or false value.

| Storyline | Intended state churn | Required evidence pattern |
| --- | --- | --- |
| Adobe subscription | recurring price, price increase, cancellation intent, renewal terms, cancellation or change of mind | current versus historical price; intention is not execution; status can change more than once |
| Orange bills | monthly bills, missing March, later bill, possible price change | observed amounts and deterministic total; March remains unknown when absent |
| Monster / energy drinks | receipts, direct consumption observations, no-observation days, bulk purchase | purchase is not consumption; explicit zero differs from no observation |
| Family tasks | pickup task, reassignment, cancellation, reopening or completion | current owner and lifecycle are separate from historical assignments |
| Car insurance | approximate note, authoritative policy, replacement policy | authoritative replacement does not erase prior evidence; dates retain precision and provenance |
| Receipts | repeated merchant, exact duplicate upload, similar but distinct receipt, changed receipt | duplicate, meaningful change, and not-duplicate are distinct relations |
| Ambiguous person | mentions of Jordan Lee, Jordan Kim, and bare Jordan | unresolved mention remains unknown; a forced link is an error |
| HomeFix correction/conflict | initial amount, later correction, unresolved disagreement or confirmation | correction is a new record; unresolved conflict does not silently choose newest value |
| Multi-date contract | signed, effective, renewal, expiry, replacement | each date has explicit semantics; current contract is not the only historical fact |
| Approval and irrelevant observations | proposed transfer/standing order, explicit approval state, unrelated coffee/weather note | no consequential action executes; irrelevant observations do not create obligations |

The generator, once approved, should make churn a design invariant rather than a
hope. Across the 100 events it should include repeated updates, at least one
explicit correction, unresolved contradiction, cancellation and later status
change, missing periods, entity ambiguity, exact duplicate, similar non-duplicate,
and at least one explicit unknown at every relevant checkpoint. The event budget
must favor those transitions over independent static facts.

## 5. Fixed checkpoints and query bundle

The proposed primary checkpoints are **20, 40, 60, 80, and 100**. Every query is
asked at every checkpoint, including when its correct answer is an empty set or
an explicit unknown. The wording below is the proposed frozen wording; it is
not yet a committed query fixture.

| Query ID | Proposed fixed question | Main assertion families |
| --- | --- | --- |
| `q-subscriptions-current` | “Which subscriptions are currently active at this checkpoint, and what is each current price and billing period?” | current status, current price, currency, period |
| `q-subscriptions-history` | “For each subscription with a changed price or status, what prior value and change evidence are known?” | previous value, effective period, change relation |
| `q-attention-14d` | “Which obligations or proposed actions require attention in the next 14 calendar days from this checkpoint? Include only evidence-supported items.” | target, deadline/window, attention reason |
| `q-insurance-expiry` | “When does the current car insurance expire, and what is the date precision?” | current policy, expiry, precision, provenance |
| `q-orange-costs` | “Which Orange bills are directly observed by period, what deterministic total is supported, and which periods are unknown?” | observations, coverage, total, missing period |
| `q-marketone-observations` | “What Monster purchases and consumptions are directly observed? Separate purchase quantity from explicitly confirmed consumption and identify unknown coverage.” | purchase count/quantity, consumption count, explicit zero, unknown |
| `q-tasks-state` | “Which tasks are still active, who owns them, and which previous task was cancelled, reassigned, or completed?” | task identity, owner, lifecycle, deadline |
| `q-unresolved` | “Which facts, entity links, dates, or amounts remain unresolved or incomplete?” | ambiguity, conflict, missingness, unknown reason |
| `q-duplicates-changes` | “Which captured inputs are duplicates, which similar inputs are not duplicates, and which represent meaningful changes?” | pair relation, relation type, changed fields, counts |
| `q-contract-dates` | “What are the signed, effective, renewal, and expiry dates for the current and replaced contract?” | date type, value, current/replaced policy |
| `q-approval-boundary` | “Which proposed actions require approval, which are approved, and which consequential actions were actually executed?” | approval required, approved, executed |
| `q-recent-changes` | “Which corrections, contradictions, replacements, cancellations, and material changes are recorded?” | typed relation, affected field, evidence |

Duplicate counting must be unambiguous: `duplicate_event_count` is the number
of captured events that duplicate an earlier captured event, excluding each
original. One original plus two duplicate uploads counts as two duplicate
events. `duplicate_group_count` is separate.

## 6. Exact unit of evaluation

The primary unit is one **atomic semantic assertion** for one fixed query at one
checkpoint within one scenario. The nested reporting units are:

- scenario;
- checkpoint;
- query; and
- atomic assertion.

Examples of atomic assertions are one current subscription price, one task's
current owner, one explicit unknown for March coverage, one duplicate relation,
one expiry date, or one `executed=false` approval-boundary fact. A paragraph,
table, or raw extracted field is not a primary unit unless it has been expanded
into atomic assertions.

The final derived state is retained as an audit/debug representation, but the
headline primary metric is fixed-query correctness at every checkpoint. This
prevents a system from scoring well only because its final state looks plausible
while it failed earlier state transitions.

## 7. Public event and response contract

### 7.1 Raw events

The implementation receives public raw inputs in an immutable, machine-readable
envelope:

```json
{
  "event_id": "evt-042",
  "sequence": 42,
  "captured_at": "2026-02-12T09:00:00Z",
  "observed_at": "2026-02-11",
  "source_type": "text",
  "payload": {"text": "A service says the price changes before renewal."},
  "payload_sha256": "<hash of the immutable payload>",
  "metadata": {"synthetic": true}
}
```

`event_id`, sequence, timestamps, source type, payload, and hash are public
input data. The payload is never rewritten. A correction or user confirmation is
a later event with its own ID and provenance, not an edit to the earlier event.

### 7.2 Candidate response envelope

The proposed public response shape is:

```json
{
  "response_contract": "gate-a-public-v1",
  "scenario_id": "life-inbox-dev-001",
  "checkpoint": 60,
  "queries": {
    "q-subscriptions-current": {
      "assertions": [
        {
          "subject": "adobe",
          "predicate": "current_price",
          "value": {"amount": "59.99", "currency": "EUR", "billing_period": "month"},
          "knowledge_status": "known",
          "source_refs": ["evt-042"]
        }
      ]
    }
  }
}
```

The candidate must use public subjects and predicates from the contract. It
must not guess an evaluator-internal `state_key`. Candidate assertions are
atomic, not grouped prose. The contract exposes public entity identifiers,
predicate names, relation types, status values, date/decimal formats, and query
IDs, but never expected current values or hidden labels.

Required assertion fields are `subject`, `predicate`, `knowledge_status`, and
`source_refs`. A known or inferred assertion requires `value`; an unknown
assertion omits `value` and provides an `unknown_reason`. Optional confirmation
references identify explicit user confirmation. The response must not claim an
external action occurred unless the input explicitly records that occurrence.

The evaluator may retain a private `assertion_id`, `state_key`, category, and
root-defect linkage for expected output and maintenance analysis. Those fields
are not part of the candidate contract.

### 7.3 Deterministic canonicalization

Before matching, the evaluator may apply only transformations declared in the
public contract:

- Unicode/case/whitespace normalization;
- decimal normalization without changing value;
- ISO date and date-precision normalization;
- declared public entity and enum aliases;
- declared object-field aliases; and
- order normalization for explicitly set-like fields.

It must not infer a hidden alias from an expected answer, call an LLM judge, or
repair a semantic disagreement by changing ground truth.

## 8. Expected state representation

The evaluator-owned expected state is a checkpointed, historical projection of
the immutable event stream. Development may include a visible oracle for local
work; holdout expected state must remain outside the implementation-agent
boundary.

Each checkpoint expected state contains historical and current assertions for:

| Domain | Required representation |
| --- | --- |
| Known / inferred / unknown | `knowledge_status`, value when known/inferred, reason when unknown, and source/confirmation provenance |
| Entity links | source mention, public entity ID or candidate set, link status, ambiguity reason, and evidence |
| Tasks | stable task ID, action, owner, lifecycle, deadline reference, status, and provenance; absence is not completion |
| Obligations | obligor, obligee, required action/condition, trigger or recurrence, lifecycle, approval requirement, and provenance; a casual note is not automatically an obligation |
| Deadlines | target, date or interval, precision, timezone, effective semantics, and evidence |
| Financial observations | exact decimal amount, currency, direction, period/occurrence, category, direct-observation status, and provenance |
| Financial aggregates | deterministic expression ID, exact result or unknown, currency, coverage set, and calculation metadata |
| Duplicates | source-event pair/group, relation type, changed fields if applicable, and provenance; raw events remain present |
| Corrections | target assertion, prior value, replacement value, origin (`user_confirmed` or `system_proposed`), effective time, and provenance |
| Contradictions | conflicting members, field, unresolved/resolved status, and later correction or confirmation reference |
| Attention | target evidence, reason, deadline/approval facts, priority if supported, and approval status; it is a derived projection |

Temporal fields use explicit semantics where needed: `observed_at` describes
when a source was observed, while `effective_from` and `effective_until`
describe the period a fact applies to. A newer observation does not erase an
older historical fact or automatically win a contradiction.

## 9. Known, inferred, and unknown rules

- **Known:** directly supported by a source or explicit user confirmation.
- **Inferred:** a revisable hypothesis supported by interpretation or multiple
  sources; it must remain labeled and traceable.
- **Unknown:** missing, unreadable, ambiguous, conflicting, or not yet checked.

Unknown is a scored result, not an empty implementation detail. Missing data
must never become zero, false, absent, cancelled, completed, or a guessed value.
An explicit numeric zero is correct only when the source or a deterministic
calculation supports zero. A purchase does not imply consumption; a quiet period
does not imply no spending or no consumption.

If two observations conflict, the expected current slot is unknown with reason
`conflicting` until a later explicit correction or confirmation resolves it. A
candidate that chooses the newest value without representing the conflict is
wrong even if the newest value later happens to be true.

## 10. Primary metric: Longitudinal Query Accuracy at Zero Maintenance

The proposed primary metric is **LQA-0M**. It is not raw extraction accuracy.

For each checkpoint/query pair, let `E` be the expected atomic assertion set and
`P` the candidate set after deterministic canonicalization. The recommended
weights are all `1.0`; this avoids arbitrary category weighting. The contract
still records a weight field so a non-unit weight can be considered only by
human approval before cases are frozen.

Match at most one candidate to each expected assertion by:

```text
public subject + public predicate + knowledge_status + value_or_unknown_reason
```

`source_refs` are required, must refer to available public events, and are
validated as a trust/provenance condition. Exact source-set agreement and
provenance recall are secondary diagnostics so a matching semantic fact is not
made false merely by including an additional valid reference.

Let:

```text
TPw = sum(weight of matched expected assertions)
FNw = sum(weight of unmatched expected assertions)
FPw = sum(weight of unmatched candidate assertions)

query_score = TPw / (TPw + FNw + FPw)

checkpoint_score(c) = aggregate TPw / (aggregate TPw + aggregate FNw + aggregate FPw)

LQA-0M = aggregate TPw over all checkpoints and queries
         / aggregate (TPw + FNw + FPw) over all checkpoints and queries
```

Thus the numerator is correct weighted assertions and the denominator is all
weighted correct, missing, and unsupported/incorrect assertion opportunities.
False positives are not hidden. Report query scores and checkpoint scores
alongside the overall result; a macro-average across query scores may be shown
as a diagnostic but is not the headline unless the human approves it.

If both sets for a query are empty, that query is `1.0` with no denominator
contribution. If only one side is non-empty, the non-empty side produces false
positives or false negatives and the query is `0.0`.

The evaluator is deterministic. It uses code/SQL for amounts, dates, counts,
duplicate identity, lifecycle comparisons, and aggregates. No LLM judge is used
for exact values, IDs, statuses, booleans, unknowns, or relations.

## 11. Human-maintenance metric

The strategic secondary metric is **maintenance interventions required after
detected failures**, with a target variant named `MIR-90`.

The benchmark must not pretend to measure human minutes. The proposed
deterministic protocol is:

1. Run the candidate at all checkpoints with zero maintenance and preserve its
   outputs.
2. Compare outputs to the evaluator-owned expected assertion/state manifest.
3. Map mismatches to predeclared root-defect records such as `wrong_entity_link`,
   `stale_current_value`, `missing_unknown`, `wrong_task_lifecycle`,
   `wrong_deadline`, `duplicate_confusion`, `unresolved_contradiction`, or
   `unsupported_action_state`. The same root defect failing multiple queries or
   checkpoints counts once.
4. Each root defect has a frozen repair footprint: the assertions and
   checkpoint/query results that one canonical human intervention would repair.
   Examples are one entity-link correction, one explicit unknown clarification,
   one current-state correction, or one duplicate interpretation.
5. Compute the minimum number of canonical interventions whose repair footprints
   raise the aggregate LQA-0M to at least `0.90`, using an exact deterministic
   set-cover/search over the small defect manifest. Do not count repeated
   symptoms separately.
6. If the 0.90 threshold is not reachable under the approved intervention
   catalog, report `threshold_not_reached` and the number of distinct detected
   root interventions required to repair all scored defects. Do not invent a
   number of minutes or claim that an unexecuted repair was performed.

The human adjudicates the root-defect and repair-footprint manifest before the
benchmark is frozen. The evaluator, not the implementation agent, owns this
manifest for holdout. Actual wall-clock correction time may be an exploratory
metric, never a replacement for the deterministic count.

## 12. Secondary metrics

Report these independently of LQA-0M and MIR-90:

- checkpoint accuracy and early-to-final change;
- accuracy by storyline and query;
- entity-link accuracy, including correct unresolved decisions;
- current-state and temporal-history accuracy;
- known/inferred/unknown precision, recall, and calibration;
- task lifecycle and ownership accuracy;
- obligation and deadline accuracy;
- duplicate, meaningful-change, correction, and contradiction handling;
- deterministic financial observation and aggregate accuracy;
- unnecessary attention/alert rate;
- critical safety violations and fabricated consequential actions;
- response-schema validity and malformed-record count;
- source/provenance validity and recall;
- model/provider cost, runtime, input/output/reasoning tokens, and context
  behavior; and
- rebuild consistency once an advanced state implementation exists.

Safety violations are reported separately and may make a run fail regardless of
its accuracy score.

## 13. Missing information and contradiction scoring

The expected manifest includes explicit unknown slots for required but
unobserved information. A candidate receives credit for the corresponding
unknown only when it omits a value and supplies the correct public reason.

- Omitted required unknown: false negative.
- `0`, `false`, empty, `none`, cancelled, completed, or guessed value for an
  unknown: false positive and a missing-data safety diagnostic.
- Explicit supported zero: known and correct.
- Unresolved ambiguity: unknown; do not force an entity ID.
- Unresolved contradiction: preserve conflict and expose unknown current value.
- Explicit later correction: record both prior and replacement evidence; the
  corrected value can become known or inferred according to its source.
- Newer evidence without correction semantics: does not delete history or
  automatically resolve a conflict.

## 14. Holdout isolation

The public development package may contain raw synthetic events, the public
contract, query wording, and a visible expected oracle for local evaluator
development. The evaluator-owned holdout package must be outside the
implementation-agent trust boundary.

For a real holdout run:

- provide implementation code only public holdout inputs and the public
  response contract;
- mount expected state and assertion manifests only in a separately permissioned
  evaluator process or checkout;
- ensure implementation code cannot read, import, copy, hash-for-label, or
  summarize expected outputs;
- keep expected values out of prompts, exceptions, logs, caches, trajectories,
  debug artifacts, and filenames;
- score candidate output after it leaves the implementation boundary; and
- expose only approved aggregate metrics and safe diagnostics to the
  implementation environment.

The evaluator must fail closed if the implementation principal can read the
holdout expected store. No holdout cases or expected outputs are created by this
Gate A proposal.

## 15. Reproduction by judges

After Gate A approval and implementation, a judge should be able to:

1. clone the repository at a recorded commit;
2. install one documented language/runtime environment;
3. authenticate the selected local provider outside the repository, without
   exposing provider tokens to the project;
4. run the fair baseline against the public development inputs;
5. run the advanced candidate against the same events and query checkpoints;
6. run the deterministic evaluator against the authorized expected package; and
7. reproduce the reported primary and secondary metrics.

Every run record must include:

- repository/code revision;
- benchmark split and event-manifest hash;
- response-contract, query-bundle, system-prompt, and evaluator revisions;
- provider, exact model/version, reasoning/configuration, and context behavior;
- operating system, runtime/dependency versions, timezone, locale, seed, and
  concurrency;
- canonical session/fork or advanced-state run identifiers;
- input/output/reasoning tokens, wall time, retries, and approximate cost; and
- candidate/result artifact paths and integrity hashes.

The primary baseline command must use the complete available conversation. Any
context-limited run is labeled separately as stress. Judges must never need
holdout expected values to run the implementation.

## 16. Example event and expected assertions

These are illustrations only and are not final case content.

Illustrative event:

```json
{
  "event_id": "evt-042",
  "sequence": 42,
  "captured_at": "2026-02-12T09:00:00Z",
  "source_type": "text",
  "payload": {
    "text": "The service says my monthly price changes to EUR 59.99 in May. I should cancel before renewal."
  }
}
```

Illustrative checkpoint assertions:

```json
[
  {
    "subject": "example_subscription",
    "predicate": "current_price",
    "value": {"amount": "59.99", "currency": "EUR", "billing_period": "month"},
    "knowledge_status": "known",
    "source_refs": ["evt-042"]
  },
  {
    "subject": "example_subscription_cancellation",
    "predicate": "status",
    "value": "proposed",
    "knowledge_status": "inferred",
    "source_refs": ["evt-042"]
  },
  {
    "subject": "example_subscription",
    "predicate": "renewal_date",
    "knowledge_status": "unknown",
    "unknown_reason": "not_stated",
    "source_refs": []
  }
]
```

The last assertion is not a placeholder for a guessed date. The second is not a
cancellation execution. Both distinctions are central to the benchmark.

## 17. Likely benchmark weaknesses

- A 100-event synthetic timeline may still be short for a very strong
  long-context model. The optional stress track and checkpoint curve make that
  limitation visible without turning the primary into a context test.
- One fictional person and ten storylines provide limited statistical power.
- Fixed query wording can be overfit; a private holdout and paraphrase slice are
  needed for a final claim.
- Obligation, attention, and inferred-intent judgments require human review
  before freezing; they must not be improvised after seeing model output.
- A typed response contract is necessary for deterministic scoring but may be
  less natural for a long-chat baseline; the same public contract must be given
  to both systems.
- The MIR-90 result depends on a carefully adjudicated root-defect/repair
  footprint manifest. If that cannot be agreed before freeze, report only the
  deterministic intervention-equivalent count after detected failures.
- The benchmark intentionally excludes OCR quality from the primary result and
  therefore cannot claim full multimodal product performance.
- Provider availability, context behavior, latency, and subscription cost may
  differ across judges; exact configuration and resource differences must be
  recorded.
- A strong baseline may perform well. That is a valid result, not a reason to
  inflate event count or alter expected values.

## 18. Gate A approval questions

These are the five decisions required before generating the case or freezing the
contract:

1. **Length:** Approve a 100-event, roughly 90-day primary with an optional
   separate 200-event stress track, or choose another target within 60–100?
2. **Checkpoints:** Approve fixed checkpoints 20/40/60/80/100 and one query
   bundle at every checkpoint?
3. **Primary scoring:** Approve deterministic public atomic assertions,
   unit weights, explicit false-positive penalties, and LQA-0M as the headline?
4. **Maintenance:** Approve the MIR-90 intervention-equivalent protocol and
   its `threshold_not_reached` fallback, with no claim about human minutes?
5. **Baseline fairness:** Approve one persistent complete-history long-chat
   conversation with isolated checkpoint forks, the same model where practical,
   and no hidden state/retrieval/database?

No benchmark generation, evaluator implementation, baseline execution, or
advanced-system work should begin until these answers are resolved.

**GRILL ME — GATE A**
