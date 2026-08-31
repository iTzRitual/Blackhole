# H2H-002 — native single-thread chat comparison

H2H-002 is a sealed, post-freeze descriptive comparison of the frozen Product
V2 runtime, a native single-thread conversation, and an augmented raw-memory
conversation. It is separate from the frozen V1 benchmark, H2H-001, Product V2
acceptance evidence, and evaluator-owned holdout material.

## Run

- Run: `h2h-002-20260831T163229Z`
- Frozen Product V2 commit: `cc0cca8e8d9c3a5ab0955f365ea71c639cac7548`
- Manifest SHA-256: `91cfe29865cdecec62d1759b29a8845e40ee8c54bf378d148f3e5f008f1064fd`
- Seed: `2026083102`
- Shape: 3 fresh synthetic worlds, 60 captures, checkpoints at 7/14/20,
  52 atomic assertions per system
- Runtime: `gpt-5.6-luna`, low reasoning, maximum provider concurrency 2

System A used one continuing native chat with plain capture text. System B used
the same model with the live raw captures and capture metadata re-supplied at
each query. System C used the normal Product V2 HTTP capture, processing, state,
Ask, and permanent Undo paths in fresh Homes.

## Results

| System | Resolved assertions | Semantic macro F1 | Claim precision proxy | Wrong-confident proxy | Attention F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Native single thread | 59.6% | 0.771 | 70.5% | 29.5% | 0.222 |
| Augmented raw memory | 67.3% | 0.786 | 77.8% | 22.2% | 1.000 |
| Blackhole Product V2 | 61.5% | 0.726 | 68.8% | 34.4% | **0.941** |

The overall semantic comparison was mixed: the augmented raw-memory comparator
resolved more assertions on this small authored set. The preregistered video
rule therefore selected Attention rather than a resolved-task metric:

> In a fresh preregistered comparison against using one normal AI thread as
> memory, Blackhole improved active Attention F1 from 0.22 to 0.94.

Blackhole Attention precision/recall were `0.907 / 1.000`; native single-thread
precision/recall were `0.222 / 0.222`. Product V2 also provided query-free
Attention state, durable source-linked state, and explicit Undo; the two chat
comparators required a query to produce an answer.

## Operational record

- System A: 18 query attempts, 158.373 seconds total, schema failures `0`.
- System B: 18 query attempts, 154.416 seconds total, schema failures `0`.
- System C: 60 captures, 33 extraction calls, 9 Ask provider calls, zero
  extraction errors, and 919.642 seconds total.
- All Product V2 checkpoint processing and retraction calls succeeded.

The exact sealed cases, expected assertions, schema, runner, runtime records,
and machine-readable result remain outside this source checkout in the retained
H2H-002 run directory. The repository keeps this compact report and the coding
trajectory so the claim is documented without embedding provider traces.

## Limits and disposition

This is three small synthetic worlds, not holdout evidence or a significance
test. Claim precision, wrong-confident output, and forget leakage use the
predeclared deterministic token-bounded proxies. Exact Product V2 provider
context bytes were not exposed by the normal HTTP contract. No binary attachment
stress was included.

**Decision: KEEP as descriptive post-freeze evidence.** No Product V2 code,
frozen benchmark semantics, baseline, evaluator, calibration evidence, or
holdout boundary was changed for this comparison. Do not interpret it as proof
that Blackhole makes the underlying model universally more accurate.
