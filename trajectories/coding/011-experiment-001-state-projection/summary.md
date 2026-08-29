# Experiment 001 — append-only state projection

## Goal

Test whether a minimal generic Blackhole-owned append-only event store and
deterministic rebuildable state projection improve current-state and temporal
reconciliation over the valid stateless long-chat baseline.

## Agent/tool used

Codex using the local repository, Python, SQLite, the installed Codex CLI when
runtime calls are required, and deterministic evaluator tooling. No holdout
material or provider credentials are to be accessed.

## Initial hypothesis

An append-only event store plus deterministic/rebuildable current-state
projection can reduce stale/superseded-state errors without requiring the LLM
to reread the entire life history. The baseline evidence motivating this
experiment is current-state accuracy `0.1507` and temporal-history accuracy
`0.2989`.

## Important implementation decisions

* Raw captures are stored in SQLite with payload hashes and aborting
  update/delete triggers. Duplicate insertion is idempotent only when the
  complete immutable event matches.
* Model extraction is scoped to each new chronological batch. It proposes
  structured observations and relationships; it does not answer checkpoint
  queries or receive expected output.
* Observations retain operation, provenance, knowledge status, and history.
  `rebuild_projection()` clears and recreates current facts from the retained
  observations and relationships, with an explicit projection version and
  input digest.
* Contradictions remain unknown until an explicit later correction or
  supersession relation resolves them. The v2 projector also uses declared
  changed fields to resolve a prior conflict; it never rewrites the raw event.
* Query responses are produced by a deterministic, query-scoped public
  projector. Date windows, history traversal, duplicate grouping, and
  financial arithmetic are code-owned. Unsupported query families return an
  empty result rather than dumping all state.
* A replay-extraction-directory option separates semantic extraction from
  projection revisions. This made the v1-to-v4 projector comparison
  repeatable without additional provider calls or prompt tuning.
* The provider boundary remains subscription-first: the installed Codex CLI
  owns authentication, and no token is requested, read, copied, exported, or
  persisted. No UI, production infrastructure, Claude adapter, or holdout
  material was added.

## Tools/actions used

Codex used PowerShell, Python, SQLite, the installed Codex CLI, the public
development benchmark, and the unchanged deterministic evaluator. It created
the scoped `app/` modules, the versioned runtime prompt, unit tests, replay
diagnostics, evaluation artifacts, and runtime trajectories. Validation used:

* `python benchmark/dev/generate_benchmark.py --check`
* `python eval/contract_smoke.py`
* `python -m compileall -q app eval`
* `python -m unittest discover -s . -p "test_*.py"`
* the unchanged full evaluator command against the public 200-event case,
  `response-contract-v2`, and public development expected output.

## Failures encountered

* The first FAST extraction with the default `max` reasoning setting exceeded
  the 900-second call budget and was manually stopped before a score; its
  valid raw extraction output was retained for diagnostics.
* A retry with a ten-event batch returned an empty model output after about
  284 seconds and failed fast.
* A replayed model-query response ended without its final root brace. The
  bounded parser repair accepted only this unambiguous closing-delimiter case.
* The repaired model-query path scored `0.0990021008` on the four-query FAST
  diagnostic and was removed from the primary path; deterministic projection
  is the tested query path.
* The first full v1 projector used a catch-all state dump and scored
  `0.1589548193`, worse than the official baseline. That fallback was removed
  rather than retained for apparent recall.
* Codex emitted a non-fatal Windows hook warning about a filename being too
  long during the fresh full extraction calls; all four extraction calls
  returned successfully.

## Retries or changed approaches

The initial deterministic projector was narrowed into query-specific public
projections after its FAST result. A second revision added explicit object
field decomposition, temporal/attention handling, and code-owned financial
aggregation. The final two small revisions filtered false duplicate chains to
receipt evidence and counted duplicate groups over duplicate-plus-meaningful
connected components. Each revision was replayed from the same recorded
semantic extraction outputs. No baseline prompt was tuned in response to an
individual calibration or experiment failure.

## Human feedback or checkpoints

The human-authorized goal freezes Gate A at 200 events and Gate B's repaired
response contract. Experiment 001 is authorized autonomously, with FAST DEV
first and no benchmark or official-baseline changes.

## Evaluation performed

The official unchanged baseline result remains `baseline-v1` with
`LQA-0M=0.3014914553`, `DSCR=277`, and SHA-256
`654cc88e6a9402506f2c66602afdbf764da3dcd11ee01c6642b9f6f2ad166805` for
`eval/results/baseline-v1.json`. Its candidate artifact also remains unchanged
with SHA-256
`ced986d760464f258ccd971d8767ccab05f0a8ae01ca10b749e41540ca27add7`.

The non-official Experiment 001 measurements were:

| Run | Events / queries | LQA-0M | DSCR | TP / FP / FN |
| --- | ---: | ---: | ---: | ---: |
| FAST live semantic extraction + deterministic query | 50 / 4 | 0.6083333333 | 15 | 17 / 7 / 8 |
| FAST final deterministic replay | 50 / 4 | 0.7222222222 | 10 | 20 / 5 / 5 |
| Full v1 projector | 200 / 48 | 0.1589548193 | 299 | 127 / 1900 / 248 |
| Full v4 final deterministic replay | 200 / 48 | 0.7492295899 | 72 | 279 / 69 / 96 |

The full v4 checkpoint scores were `0.7962962963`, `0.7523071836`,
`0.7064078283`, and `0.7419070513` at 50/100/150/200. The result was
schema-valid, had zero safety violations, and passed source-integrity checks.
The full v4 secondary relation-reconciliation score was `0.3169014085`, which
identifies relationship detail as the main remaining weakness. The fresh
full semantic calls used 132,514 input, 72,711 output, and 53,751 reasoning
tokens over 887.453 seconds. The final v4 replay itself made no provider
calls.

## Result

The hypothesis was supported. The smallest tested architecture produced a
full public development score of `0.7492295899`, an absolute improvement of
`0.4477381346` over the preserved official baseline, while reducing DSCR from
277 to 72. The improvement came from durable state, explicit history and
relations, and deterministic projections rather than from changing benchmark
facts, the evaluator, the response contract, or the official baseline.

## Regressions or unresolved issues

The fresh semantic extraction path is still expensive and was run with
reasoning `high` because `max` was not practically usable for the full
milestone. The final candidate still loses relation-detail assertions,
especially duplicate/change relationship detail; contract date recall and
some task/recent-change assertions also remain incomplete. The implementation
is an experiment slice, not a production-ready application, and has no user
interface or external-action subsystem.

## Final decision

**KEEP.** Experiment 001 is a meaningful, evidence-backed improvement and the
full 200-event milestone is complete. Stop here as authorized; do not begin a
second experiment in this task. Any next experiment should target the
remaining relation-detail weakness under a new trajectory and changelog
entry.

## Related git commit

This trajectory is finalized in the single coherent Experiment 001 commit that
contains it; the commit SHA is reported in the task handoff.

No authentic session transcript is available; no transcript is fabricated.
