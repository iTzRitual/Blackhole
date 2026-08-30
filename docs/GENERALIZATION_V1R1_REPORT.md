# GENERALIZATION V1R1 REPORT

## Gate result

**PASS** — candidate seals, the repaired local oracle, and all six deterministic scoring runs passed their required gates. This report is a post-freeze shadow/generalization result, not a runtime or prompt change.

This is a post-freeze shadow/generalization set of three fresh synthetic worlds, not an organizer-provided official holdout and not a claim of statistical significance.

The large DEV improvement did not transfer strongly to these unseen worlds. The
V1R1 Blackhole macro-LQA lead is only `+0.0120635896`, and Blackhole trails the
baseline in G03; this result is descriptive evidence about the frozen system,
not a basis for retroactive tuning.

## Scope and chronology

- Worlds: `g01`, `g02`, `g03`; 80 events per world; 240 fresh events total.
- Checkpoints: 20, 40, 60, and 80; 12 fixed queries per checkpoint.
- Contract: `response-contract-v2`; scorer: `lqa-0m-v2`.

The execution chronology was:

implementation freeze → V1 test-world creation → zero-call payload schema repair / V1R1 reseal → blind baseline + blind Blackhole candidate sealing → oracle opened only after both candidate sets were sealed → deterministic scoring → no post-result semantic tuning.

The V1R1 repair record reports that event text, ordering, timestamps, metadata, relations, query inputs, and expected semantic assertions were unchanged; only the public payload container and dependent raw-event hashes changed. All 240 event digests, the query bundle, and the response contract were verified accordingly.

## Verification gates

- Public head: `79bea04e432e6566e3d6989e8fa411e7c613908b`.
- Sealed baseline head: `f58466a2605d38e324cfc565c011eb84591a2fee`; sealed Blackhole head: `9d2ee431079fc7ad7b1921677eac3d15123cbe34`.
- Oracle head: `fc707cb485629919434dc41f4014f10d5065b4db`; all eight required contract/query/case/expected hashes matched.
- Candidate seal verification: **PASS** for all six candidates; both manifests matched the public head, frozen configuration, candidate hashes, no-oracle-access claim, and no-scoring-before-sealing claim.
- Candidate branches contained no V1R1 expected/oracle paths.
- The sealed candidate hashes are checkout-byte hashes. The Git blobs are LF-normalized while the sealed Windows checkout bytes are CRLF; verification used disposable detached checkouts with `core.autocrlf=true` and copied bytes without JSON parsing or rewriting before hashing. Raw Git-blob hashes are recorded separately in the seal evidence.
- No model/provider calls were made by this scoring task.

## Scores

| System | G01 LQA | G02 LQA | G03 LQA | Macro LQA | DSCR total | DSCR / 100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.2893117299 | 0.1836918290 | 0.3045098806 | 0.2591711465 | 575 | 239.5833333333 |
| Blackhole | 0.2989223909 | 0.2418606412 | 0.2729211760 | 0.2712347361 | 397 | 165.4166666667 |

Per-world evaluator outputs:

| System | World | LQA-0M | C20 | C40 | C60 | C80 | TP | FP | FN | DSCR | Schema | Source | Safety | Hard failure |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| Baseline | g01 | 0.2893117299 | 0.4822649573 | 0.4249819625 | 0.0833333333 | 0.1666666667 | 50 | 81 | 121 | 135 | FAIL | PASS | PASS | False |
| Baseline | g02 | 0.1836918290 | 0.0833333333 | 0.3782196970 | 0.0000000000 | 0.2732142857 | 51 | 155 | 139 | 230 | FAIL | PASS | PASS | False |
| Baseline | g03 | 0.3045098806 | 0.4981872294 | 0.4055665785 | 0.0000000000 | 0.3142857143 | 85 | 184 | 116 | 210 | FAIL | PASS | PASS | False |
| Blackhole | g01 | 0.2989223909 | 0.3249007937 | 0.2958333333 | 0.2888888889 | 0.2860665478 | 68 | 126 | 103 | 117 | PASS | PASS | PASS | False |
| Blackhole | g02 | 0.2418606412 | 0.2896825397 | 0.2659147870 | 0.1960714286 | 0.2157738095 | 69 | 132 | 121 | 148 | PASS | PASS | PASS | False |
| Blackhole | g03 | 0.2729211760 | 0.4000992063 | 0.2725018038 | 0.1821789322 | 0.2369047619 | 77 | 119 | 124 | 132 | PASS | PASS | PASS | False |

Mean checkpoint LQA across worlds:

| System | C20 | C40 | C60 | C80 |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 0.3545951733 | 0.4029227460 | 0.0277777778 | 0.2513888889 |
| Blackhole | 0.3382275132 | 0.2780833080 | 0.2223797499 | 0.2462483731 |

## Aggregate comparison

- Absolute LQA delta: **+0.0120635896** (`Blackhole macro_LQA_0M - Baseline macro_LQA_0M`).
- Relative LQA improvement: **4.65%**, computed as `(Blackhole - Baseline) / Baseline`.
- Baseline error: `0.7408288535`; Blackhole error: `0.7287652639`.
- Error-rate reduction: **1.63%**, computed as `1 - (Blackhole error / Baseline error)` with `error = 1 - LQA`.

| System | DSCR total | DSCR / 100 over 240 events | Mean DSCR/world | TP | FP | FN | Micro precision | Micro recall | Micro F1 | Hard | Source failures | Safety failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 575 | 239.5833333333 | 191.6666666667 | 186 | 420 | 376 | 0.3069306931 | 0.3309608541 | 0.3184931507 | 0 | 0 | 0 |
| Blackhole | 397 | 165.4166666667 | 132.3333333333 | 214 | 377 | 348 | 0.3620981387 | 0.3807829181 | 0.3712055507 | 0 | 0 | 0 |

Schema validity is reported separately from `hard_failure` because the frozen evaluator only marks source-integrity or safety violations as hard failures. Baseline is schema-invalid in all three worlds with 60 missing-query errors total; Blackhole is schema-valid in all three. Neither system has a hard, source-integrity, or safety failure.

## Efficiency and reliability

| System | Provider / model / reasoning | G01 runtime (s) | G02 runtime (s) | G03 runtime (s) | Mean successful runtime (s) | Total successful runtime (s) | Operational retries |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | Codex CLI / gpt-5.6-luna / max | 3060.775933 | 2960.018914 | 3178.631731 | 3066.475526 | 9199.426578 | 3 |
| Blackhole | Codex CLI / gpt-5.6-luna / high | 864.525625 | 913.252582 | 914.154316 | 897.310841 | 2691.932523 | 0 |

Successful-run token usage where recorded:

| System | Input tokens | Cached input tokens | Output tokens | Reasoning output tokens |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 332453 | 266240 | 255 | 127 |
| Blackhole | 377220 | not recorded | 146863 | 111678 |

- Baseline operational retries: `g01=0`, `g02=2`, `g03=1` (three total); semantic-quality retries: 0.
- Blackhole operational retries: `g01=0`, `g02=0`, `g03=0`; semantic-quality retries: 0.
- These are successful-candidate runtimes only. Failed-attempt runtime and wall-clock totals including failures were not estimated because the sealed evidence is incomplete for that purpose.

## Descriptive failure analysis (no tuning)

### Query families

| Query family | Baseline mean | Blackhole mean | Delta |
| --- | ---: | ---: | ---: |
| `q-service-costs` | 0.3884920635 | 0.1011904762 | -0.2873015873 |
| `q-subscriptions-current` | 0.4375000000 | 0.2265632516 | -0.2109367484 |
| `q-attention-14d` | 0.1902777778 | 0.0000000000 | -0.1902777778 |
| `q-subscriptions-history` | 0.0833333333 | 0.0000000000 | -0.0833333333 |
| `q-unresolved` | 0.1487103175 | 0.1473214286 | -0.0013888889 |
| `q-duplicates-changes` | 0.0411594578 | 0.0440476190 | +0.0028881612 |
| `q-tasks-state` | 0.2357593795 | 0.2558329462 | +0.0200735666 |
| `q-recent-changes` | 0.0000000000 | 0.0833333333 | +0.0833333333 |
| `q-contract-dates` | 0.5198412698 | 0.6127976190 | +0.0929563492 |
| `q-purchase-consumption` | 0.3122023810 | 0.4333333333 | +0.1211309524 |
| `q-insurance-current` | 0.3027777778 | 0.5420634921 | +0.2392857143 |
| `q-approval-boundary` | 0.4500000000 | 0.8083333333 | +0.3583333333 |

The weakest baseline families by mean query score are recent changes (`0.0000000000`), duplicates/changes (`0.0411594578`), subscription history (`0.0833333333`), unresolved facts (`0.1487103175`), and attention (`0.1902777778`). The weakest Blackhole families are attention (`0.0000000000`), subscription history (`0.0000000000`), duplicates/changes (`0.0440476190`), recent changes (`0.0833333333`), and service costs (`0.1011904762`).

Blackhole’s largest improvements are approval boundary (`+0.3583333333`), insurance current (`+0.2392857143`), purchase/consumption (`+0.1211309524`), contract dates (`+0.0929563492`), and recent changes (`+0.0833333333`). Its largest regressions are service costs (`-0.2873015873`), current subscriptions (`-0.2109367484`), attention (`-0.1902777778`), and subscription history (`-0.0833333333`).

By world, Blackhole is ahead in G01 by `+0.0096106610` and G02 by `+0.0581688122`, but behind in G03 by `-0.0315887045`.

### Category and knowledge-status behavior

The evaluator’s aggregate category buckets show state-maintenance improving from score `0.2360406091` (baseline) to `0.2782834850` (Blackhole). Relation reconciliation remains score `0.0000000000` for both; relation false positives fall from 170 to 102, but no true positives are recorded in that bucket. Duplicate/change also remains score `0.0000000000` for both, with 13 baseline false positives versus 32 Blackhole false positives. Blackhole has additional entity-resolution false positives (19 total); baseline has none in that bucket.

For knowledge status, known assertions improve from score `0.1977142857` to `0.2461355529` and from 173 to 207 true positives. Unknown assertions decline from score `0.1300000000` to `0.0804597701` (13 to 7 true positives); inferred assertions have zero true positives for both systems. This indicates a known-status gain alongside weak unknown/inferred handling in the frozen outputs.

### Attention, schema, provenance, and reliability

Attention is a clear Blackhole failure mode: baseline has 5 TP, 11 FP, 20 FN and false-positive rate `0.6875000000`; Blackhole has 0 TP, 17 FP, 25 FN and false-positive rate `1.0000000000`. Blackhole’s attention query is score-zero in every world.

Baseline has schema/output failures in every world: it omits all 12 query objects at G01 checkpoints 60 and 80, G02 checkpoints 20 and 60, and G03 checkpoint 60. Blackhole has no schema errors.

All six candidates pass source-integrity validation and the safety scan. Provenance exactness is true for 48/144 baseline query observations versus 60/144 Blackhole observations; mean provenance recall is `0.9736689815` versus `0.9000578704`. These provenance metrics are reported separately from source-integrity failures.

Operationally, baseline required three retries while Blackhole required none. This is an observed reliability difference, not a semantic-quality retry or a rerun performed by this scoring task.

## Reproducibility and artifacts

The existing evaluator was invoked six times with the repaired V1R1 scenario, expected, candidate, and response-contract paths:

```text
python -m eval.score --scenario benchmark/generalization/v1/cases/scenario-gNN.json --expected benchmark/generalization/v1/expected/scenario-gNN.json --candidate eval/results/generalization/v1/<system>-gNN-candidate.json --response-contract benchmark/generalization/v1/response-contract-v2.json --output eval/results/generalization/v1/scored/<system>-gNN-v1r1-score.json
```

| System | World | Score artifact | SHA-256 |
| --- | --- | --- | --- |
| Baseline | g01 | `eval/results/generalization/v1/scored/baseline-g01-v1r1-score.json` | `4142b84e28c812d973ff6c707fc086bae6c6623d18dc60a9f35ec8986f6f299a` |
| Baseline | g02 | `eval/results/generalization/v1/scored/baseline-g02-v1r1-score.json` | `396366dc78f0dc87ea83a357cbe4a4e0e3926e93c46f48a6c6a7c9f35c3aba75` |
| Baseline | g03 | `eval/results/generalization/v1/scored/baseline-g03-v1r1-score.json` | `0548c58aaa221348075f20c93452a785a6de4ef85b2a3df5a8720fbb4592b071` |
| Blackhole | g01 | `eval/results/generalization/v1/scored/blackhole-g01-v1r1-score.json` | `c711b2c734ef9ff2c409b734c0da6eeceda0ed972f55933b3d54ee0d3d3365a6` |
| Blackhole | g02 | `eval/results/generalization/v1/scored/blackhole-g02-v1r1-score.json` | `ab4e925c91e9c379ac62020d8dcf3c9043b85c2736c8204b947ad125649c9b4f` |
| Blackhole | g03 | `eval/results/generalization/v1/scored/blackhole-g03-v1r1-score.json` | `c1bd94ae3be7bfe52f806ab3e71981709b0f77120c998b1876b20e4a81b0028c` |

The machine-readable aggregate report is `eval/results/generalization/v1/GENERALIZATION_V1R1_RESULT.json`. Seal evidence is `trajectories/coding/030-generalization-v1r1-scoring/seal-verification.json`.

No runtime, prompt, candidate, benchmark case, response contract, query bundle, expected output, or evaluator was modified after results were observed. The scoring branch `generalization/score-v1r1` is local-only and was not pushed. Decision: keep the frozen system and artifacts unchanged; this task records results only.
