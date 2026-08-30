# Generalization V1R1 Scoring — Trajectory Summary

## Goal

Verify the sealed V1R1 baseline and Blackhole candidates, open and verify the
repaired local oracle only after both candidate sets passed sealing, score all
six candidates with the existing deterministic evaluator, produce the required
reports and evidence, and make one local-only scoring commit without changing
the frozen runtime or benchmark inputs.

## Agent/tool used

Codex using the local PowerShell/Git/Python environment and apply_patch for
trajectory and report artifacts. The evaluator was run with python -m
eval.score. No model or provider call was made by this scoring task.

## Initial hypothesis

This was a verification and reporting task, not an optimization experiment;
there was no tuning hypothesis. A materialization assumption was tested:
the stated candidate hashes were found to be hashes of CRLF Windows checkout
bytes, while the exact Git blobs were LF-normalized. Disposable detached
checkouts with core.autocrlf=true reproduced all six stated hashes exactly.

## Important implementation decisions

- Used Blackhole-generalization-oracle at
  fc707cb485629919434dc41f4014f10d5065b4db and created the new local
  generalization/score-v1r1 worktree from that exact commit.
- Fetched and verified the exact public, blind-baseline, and blind-Blackhole
  remote heads. Candidate branches were not merged.
- Verified candidate bytes from disposable detached checkouts before opening
  V1R1 expected output. Candidate and manifest copies were temporary and were
  removed before the final commit; raw Git-blob hashes and checkout-byte
  hashes are retained in seal-verification.json.
- Verified the repaired V1R1 contract, query bundle, three public cases, three
  expected files, oracle HEAD, and the schema-repair audit. The audit records
  payload-container/hash repair only and semantic expected-output invariance.
- Used the frozen lqa-0m-v2 evaluator without editing eval/score.py.
- Generated aggregate metrics from the six immutable score artifacts and
  sealed manifest runtime/retry/token evidence. No failed-attempt runtime was
  estimated.

## Tools/actions used

- Read the initiating pasted instruction before proceeding.
- Inspected Git worktrees/status, fetched the three sealed remote references,
  listed exact sealed paths, and checked candidate-branch expected/oracle
  boundary paths.
- Materialized and independently hashed candidate files and manifests; parsed
  manifests only after byte verification.
- Created pre-scoring seal evidence.
- Verified oracle hashes and the V1R1 repair audit.
- Ran the six existing deterministic evaluator commands:
  baseline/Blackhole × G01/G02/G03, using the repaired V1R1 scenario,
  expected, and response-contract paths.
- Aggregated per-world, checkpoint, category, knowledge-status, query-family,
  attention, provenance, DSCR, efficiency, and reliability metrics.
- Wrote the machine report, human report, and this trajectory.

## Failures, retries, and changed approaches

- The first worktree guard reused PowerShell LASTEXITCODE after later
  commands and conservatively aborted. The guard was corrected; no worktree
  was created by the failed attempt, and the intended worktree was then
  created successfully.
- Raw Git-blob hashes initially differed from the stated candidate hashes
  because of LF versus CRLF checkout bytes. The discrepancy was investigated
  independently across all six candidates; a disposable sealed-style checkout
  reproduced every stated hash. No source or frozen file was changed.
- The first human-report generation attempt hit the Windows console
  cp1250 encoding limit on the chronology arrow and left only a traceback in
  the new file. That file was deleted and the same report was regenerated with
  UTF-8 output.
- Shell cleanup using Remove-Item was blocked by the safety filter, first
  with -Force and then without it. The eight explicit temporary files were
  removed with apply_patch instead.
- All six scoring commands completed successfully. No provider/model retry
  was made.

## Human feedback or checkpoints

The initiating instruction was supplied in the referenced pasted text file.
No additional human feedback was received during execution. The enforced
checkpoints were: candidate seal PASS, oracle verification PASS, then
deterministic scoring and report generation.

## Evaluation performed

The frozen evaluator version was lqa-0m-v2, with response-contract-v2.
Results:

- Baseline G01/G02/G03 LQA-0M: 0.289311729936730,
  0.183691829004329, 0.304509880551547; macro
  0.259171146497535.
- Blackhole G01/G02/G03 LQA-0M: 0.298922390926067,
  0.241860641186299, 0.272921176046176; macro
  0.271234736052848.
- Absolute macro delta: +0.012063589555312; error-rate reduction:
  1.628390889242%.
- DSCR totals: baseline 575, Blackhole 397.
- Hard failures, source-integrity failures, and safety failures: 0 for
  both systems.
- Baseline schema validity: 0/3 worlds, with 60 missing-query errors.
  Blackhole schema validity: 3/3 worlds.
- Operational retries: baseline 3 total (0/2/1), Blackhole 0.
- No scoring provider/model calls.

## Result

The GENERALIZATION V1R1 SCORE GATE is PASS. Blackhole has a modest positive
macro-LQA delta and lower DSCR, is schema-valid in all three worlds, and has
no operational retries in the sealed evidence. The per-query analysis shows
strongest gains in approval-boundary and insurance queries, while attention,
service-cost, subscription-history, and duplicate/change behavior remain
weak.

## Regressions or unresolved issues

This task did not change or tune the runtime. Baseline schema omissions,
Blackhole attention false positives/false negatives, weak duplicate/change
and relation reconciliation scores, weak inferred/unknown handling, and
cross-world variation are recorded descriptively in the human and machine
reports. Failed-attempt wall-clock totals are intentionally not estimated.
This shadow set is not an organizer-provided official holdout and does not
support a statistical-significance claim.

## Final decision

KEEP the frozen system and artifacts unchanged. Treat this as a deterministic
post-freeze generalization report only; perform no post-result semantic
tuning.

## Related git commit

generalization: score sealed V1R1 candidates — local-only scoring branch; the
final commit SHA is reported from the final repository HEAD in the task
handoff.
