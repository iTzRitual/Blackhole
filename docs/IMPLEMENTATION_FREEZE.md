# Blackhole implementation freeze

**Status:** Frozen

**Freeze recorded:** 2026-08-29 20:02:14 +02:00 (Europe/Berlin)

**Implementation freeze SHA:**
`171a6cc1c656d6ab901f41bda8440ee5d59967e3`

This SHA is the consolidated implementation/evidence commit. The final
freeze-record commit that adds this document and the `implementation-freeze-v1`
tag is documentation-only; it does not change application behavior. The tag is
the repository handoff reference for the complete freeze record.

## Frozen benchmark and evidence

- Gate A remains frozen at one public 200-event scenario with checkpoints at
  50, 100, 150, and 200.
- Gate B's `response-contract-v2` repair remains valid.
- The official fair `baseline-v1` remains `LQA-0M=0.30149145529538973` with
  `DSCR=277`.
- The current kept development reference remains Experiment 005 at
  `LQA-0M=0.8695006212469447` with `DSCR=40`.
- Calibration evidence, evaluator behavior, expected development values, and
  all protected result artifacts remain unchanged. The E002 “final” files are
  retained as historical/superseded evidence; no new authoritative final
  comparison was generated in this phase.
- These development measurements are not independent generalization evidence
  and do not establish holdout or production performance.

## Frozen architecture

The consolidated product boundary is a local Host-owned runtime. `HostRuntime`
owns the Blackhole Home, SQLite `StateStore`, `IngestionEngine`, validated
non-sensitive configuration, provider readiness, processing lifecycle, and
rebuildable derived state. Capture appends immutable raw evidence and returns
without provider work. Later processing uses the externally authenticated local
Codex CLI when available, while semantic normalization, completeness, relation
recovery, duplicate-aware projection, date handling, and financial aggregation
remain versioned/deterministic responsibilities. The PWA is a static,
same-origin client of the Host domain API; it does not own persistence or
provider credentials.

Loopback binding is the default. The documented trusted-LAN demonstration
requires the explicit command below and remains unauthenticated/private-network
only:

```text
python -m app.web_app --host 0.0.0.0 --port 8080 --trusted-lan-demo
```

Pairing, device tokens, TLS, public networking, cloud relay, shell routes,
arbitrary attachment persistence, OCR, scheduling, and consequential external
actions are not part of the frozen implementation.

## Validation evidence at freeze

- `python -m unittest discover -s . -p "test_*.py" -v`: 85 tests passed;
  75 application/qualification tests and 10 evaluator tests.
- `python -m compileall -q app eval scripts`: passed.
- `python benchmark/dev/generate_benchmark.py --check`: checked 200 events and
  four checkpoints.
- `python eval/contract_smoke.py`: non-scored contract smoke passed; its
  existing artifact was unchanged.
- `python scripts/qualification_check.py --inventory`: all hard checks passed;
  23 coding trajectories and 42 runtime trajectories were inventoried. Three
  warnings remain for intentionally preserved stale named result artifacts.
- Fresh-path deterministic E005 replay: `LQA-0M=0.8695006212469447`,
  `DSCR=40`, four checkpoints, no provider calls, and no change to the kept
  result.
- PWA and Host tests passed, covering immediate capture, same-origin API
  routes, manifest/assets, service-worker API exclusion, reduced-motion/mobile
  static requirements, provider-safe status, and trusted-LAN bind policy.
- One bounded neutral real smoke after consolidation returned HTTP 200 for
  health, both captures, and Ask; processed two events in approximately 20.7
  seconds and rebuilt state with two captures, three facts, and one relation.
  It reproduced the known novel-entity-linking limitation and was not used for
  prompt tuning.

## Protected artifact hashes

The SHA-256 values verified at freeze are:

| Artifact | SHA-256 |
| --- | --- |
| `benchmark/dev/cases/scenario-001.json` | `7FED14D9A856071AD16732D125D54DD286726EA4640A0D1AA041BF6E5D05EB38` |
| `benchmark/dev/expected/scenario-001.json` | `502CC5758A3ADB1B1C8AFEAE8B228F00D4C981D799D8C6AEC76B244FC6A582E7` |
| `benchmark/dev/response-contract-v2.json` | `31DEDD4ADF1F0E2103CB8783C507D50263730708769FB4B9DD2ABAB98E499621` |
| `eval/results/baseline-v1.json` | `654CC88E6A9402506F2C66602AFDBF764DA3DCD11EE01C6642B9F6F2AD166805` |
| `eval/results/experiment-005-duplicate-evidence-full.json` | `DCE2C1502D295282D015AC444A159BB2F53C133B5475F2D26F71456636B9A084` |

The pre-existing `eval/results/contract-smoke.json` was compared across the
hardening branch and pre-merge master and had no committed diff, so it was not
regenerated or overwritten as consolidation output.

## What is allowed after the freeze

Allowed work is limited to documentation, reproducible submission preparation,
video/demo packaging, and separately authorized post-freeze generalization
experiments in isolated evidence paths. Such work must preserve the frozen
benchmark, evaluator, response contract, baseline, calibration evidence, raw
sources, holdout boundary, and approval boundary. A new experiment requires a
new trajectory and a reproducible run record.

Post-freeze generalization results will not be used to tune the runtime.

No benchmark optimization, E006 treatment, holdout material, baseline rerun,
or final-comparison regeneration is part of this freeze task. The stale
product-phase comparison remains available only as historical evidence until a
later, explicitly authorized submission phase.

## Remaining limitations

The frozen product is a local hackathon implementation, not production
infrastructure. The real neutral smoke did not reliably resolve a novel entity
across two mentions, and its bounded history answer did not surface the stored
effective date. Attachment bytes are not persisted end-to-end; provider usage
is not exposed through the safe HTTP transport; and there is no pairing or
remote deployment security model. No holdout or post-freeze generalization
claim is made.
