# Experiment 005 summary

## Status

Complete. The exact human instruction is recorded in `prompt.md`; it was
provided as an attachment and is preserved as a task instruction, not a
fabricated transcript. No benchmark case, expected output, query bundle,
evaluator code, or protected evaluator artifact was changed; the new E005
evaluation outputs are recorded separately below.

## Goal

Determine whether the current projection loses valid semantic observations
only because their source capture belongs to a true duplicate group, and if so,
add generic duplicate/evidence components that consolidate semantic evidence
without creating duplicate real-world occurrences or double-counting aggregates.

## Agent/tool used

Codex in the shared local workspace using PowerShell, `rg`, Python,
`apply_patch`, the existing SQLite state store, runner, evaluator, and recorded
public semantic extraction. No provider calls are authorized for this task.
No authentic transcript is being fabricated.

## Initial hypothesis

True duplicate captures should remain one counting unit, but their observations
should be available as evidence for a canonical duplicate component. A
deterministic, rebuildable consolidation boundary may recover several current
state facts without changing raw events, relations outside duplicate types, or
financial/task counts.

## Frozen reference

Experiment 004 is the current kept reference at LQA-0M `0.8630770101`, DSCR
`41`, with checkpoints `0.8888888889 / 0.8713728401 / 0.8321654040 /
0.8598809075`. The benchmark, expected output, query bundle,
`response-contract-v2`, evaluator, `baseline-v1`, calibration evidence, and
all prior experiment artifacts are protected.

## Phase 0 audit

The read-only audit used the public development scenario's expected output
offline and the E004 SQLite state. It did not send expected data to a runtime
agent and did not inspect holdout material. The existing projection excludes
observations whose source event is the source of an `exact_duplicate`,
`normalized_duplicate`, or `duplicate` relationship before current-state
reconciliation.

| Diagnostic | Result |
| --- | ---: |
| True duplicate relation edges | 48 |
| Connected components across true duplicate relation types | 24 |
| Events in those components | 72 |
| Non-canonical component members | 48 |
| Unique expected state keys recovered only from discarded duplicate evidence | 3 |

The three cutoff-aware, meaningful losses were all at checkpoint 200:

| State key | Lost evidence | Category | Query |
| --- | --- | --- | --- |
| `streamly / next_renewal` | `evt-191`, `2026-03-20` | current state | `q-subscriptions-current` |
| `gymflex / expiry_date` | `evt-159` / `evt-199`, `2027-02-28` | temporal history | `q-contract-dates` |
| `bank_standing_order / approved` | `evt-200`, `false` | safety | `q-approval-boundary` |

This is exactly three meaningful defects, so the experiment proceeds. The audit
did not treat extraction omissions, incorrect relations, non-duplicate changes,
or unrelated expected assertions as duplicate-projection losses. An earlier
diagnostic accidentally matched later observations to earlier checkpoints; it
was discarded and the table above uses checkpoint-aware visibility.

## Design and implementation decisions

- The change is opt-in through `--duplicate-evidence consolidate`; the existing
  projection mode remains available as the comparison path.
- True duplicate components use only `exact_duplicate`,
  `normalized_duplicate`, and `duplicate` relationships. Edges are treated as
  undirected for component construction, with the earliest raw sequence as the
  canonical event.
- Derived `duplicate_components` metadata records the stable component ID,
  canonical event, and all member event IDs. Raw events, raw observations, and
  raw relationship evidence remain unchanged.
- Component observations are consolidated by subject and predicate. Identical
  values do not create another occurrence; additional predicates survive;
  unresolved value disagreement becomes `unknown/conflicting`; unknown or
  inferred evidence is not silently upgraded; and only an unambiguous terminal
  correction/supersession chain can resolve a conflict.
- Provenance is unioned only from observations supporting that predicate. All
  component members remain available in component metadata rather than being
  attached to unrelated predicates.

## Tools and actions

Used PowerShell, `rg`, `apply_patch`, Python `unittest`, the existing benchmark
generator, contract smoke, unchanged evaluator, `app.advanced_runner` replay,
`eval.score_slice`, `eval.score`, and read-only SQLite/hash audits. The runner
replayed the existing public semantic extraction from
`trajectories/runtime/experiment-001-full-v1`; no provider or verifier call was
made, and no baseline prompt was tuned.

## Failures, retries, and changed approaches

The first full replay exposed a false conflict at checkpoint 150 because two
explicit supersession rows formed a chain inside one duplicate component. The
resolver was changed to identify one terminal supersession branch and the full
replay was rerun. A subsequent comparison showed that attaching every component
member to every predicate added provenance-only DSCR noise. Provenance was
narrowed to supporting observations while component metadata retained all
members; FAST and full replays were rerun. The final replay has no unresolved
semantic regression.

## Human feedback and checkpoints

The human instruction authorized this single experiment, froze the public
benchmark and prior evidence, prohibited holdout access and E004 verifier use,
and required a stop after the experiment. No additional human checkpoint or
provider configuration was used during execution.

## Evaluation performed

- Eight neutral duplicate-evidence tests passed, covering identical values,
  added predicates, unresolved conflicts, similar-not-duplicate boundaries,
  meaningful changes, duplicate chains, unknown preservation, explicit
  correction, and rebuildability.
- Full application tests passed: 42 tests. Evaluator tests passed: 10 tests.
- `python benchmark/dev/generate_benchmark.py --check` passed.
- `python eval/contract_smoke.py` passed with the correct smoke score `1.0` and
  the intentionally malformed case rejected.
- The standard 50-event FAST replay remained LQA-0M `0.8888888889`, DSCR `4`,
  with no hard failure.
- The final public 200-event replay used checkpoints 50/100/150/200 and the
  unchanged evaluator. It formed 24 components containing 72 events, including
  48 non-canonical members; 51 observations were recovered from duplicate-source
  captures and 36 identical observations were consolidated. Count invariants
  recorded 200 raw events, 48 duplicate relation edges, 24 single-occurrence
  component units, 287 input observations, 251 projected observation groups,
  and `projected_groups_not_increased=true`.

## Result

E005 full replay scored LQA-0M `0.8695006212` versus E004's `0.8630770101`,
with checkpoint scores `0.8888888889 / 0.8713728401 / 0.8321654040 /
0.8855753519`, totals `TP=330, FP=35, FN=45`, and DSCR `40` versus `41`.
It recovered the three audited facts: Streamly next renewal, GymFlex expiry,
and bank standing-order approval. Financial, duplicate/change,
entity-resolution, relation-reconciliation, and unknown-state metrics did not
regress; schema, source-integrity, and safety checks passed.

## Regressions or unresolved issues

The LQA gain was `+0.0064236111`, below the optional `+0.015` heuristic, but
the experiment met the alternative keep condition by materially improving all
three pre-identified projection-loss categories while reducing DSCR by one.
The remaining public benchmark defects are outside this experiment. No E006
benchmark-optimization experiment was started.

## Final decision

**KEEP** duplicate-aware evidence consolidation as the current advanced
reference. It is not a new benchmark, baseline, holdout result, or production
claim. The next work, if authorized, must be post-freeze generalization rather
than another benchmark-optimization experiment.

## Related artifacts and commit

- Candidate: `eval/results/experiment-005-duplicate-evidence-full-candidate.json`
- Score: `eval/results/experiment-005-duplicate-evidence-full.json`
- FAST score: `eval/results/experiment-005-duplicate-evidence-fast.json`
- Runtime evidence: `trajectories/runtime/experiment-005-duplicate-evidence-full/`
- Neutral tests: `app/tests/test_duplicate_evidence.py`
- Prior kept reference: `eval/results/experiment-004-deterministic-full.json`
- Protected official baseline: `eval/results/baseline-v1.json`
- Related git commits: E004 `5e8ca977399d1d7b94ecfba1833d56e6961ff9fb`; E005 is
  this commit, `experiment: add duplicate-aware evidence consolidation` (the
  final SHA is reported in the task handoff).

Protected artifact SHA-256 values verified before commit:

- `eval/results/baseline-v1.json`: `654CC88E6A9402506F2C66602AFDBF764DA3DCD11EE01C6642B9F6F2AD166805`
- `benchmark/dev/cases/scenario-001.json`: `7FED14D9A856071AD16732D125D54DD286726EA4640A0D1AA041BF6E5D05EB38`
- `benchmark/dev/expected/scenario-001.json`: `502CC5758A3ADB1B1C8AFEAE8B228F00D4C981D799D8C6AEC76B244FC6A582E7`
- `benchmark/dev/response-contract-v2.json`: `31DEDD4ADF1F0E2103CB8783C507D50263730708769FB4B9DD2ABAB98E499621`

No authentic session transcript is available and none was fabricated.
