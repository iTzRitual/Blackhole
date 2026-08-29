# Baseline v0 — invalid contract evidence

Status: preserved historical evidence; not an official baseline.

`reason_invalid: response/evaluator contract mismatch`

The v0 candidate and score were produced from the Gate A run recorded before
the public semantic response boundary was repaired. The model used grouped
records and dotted evaluator-oriented `state_key` values, while the evaluator
expected a different assertion identity. It also contained representative
schema violations such as `unknown` assertions with a `value`. The resulting
`LQA-0M=0.0000` had zero true positives and is not interpretable as semantic
performance.

The original files were preserved byte-for-byte by rename from commit
`64d4662`:

- `baseline-v0-invalid-contract-candidate.json` — raw candidate output
- `baseline-v0-invalid-contract.json` — prior evaluator output

They must not be overwritten, tuned against, or reported as the official
baseline. The corrected run is a separate `baseline-v1` artifact scored under
the frozen `response-contract-v2` contract.
