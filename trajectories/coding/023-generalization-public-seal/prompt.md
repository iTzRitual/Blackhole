# Generalization public seal — prompt record

This is a faithful summary of the user-provided task specification, not a
fabricated transcript.

Audit the already-frozen post-freeze generalization package in the existing
oracle worktree. If its generated files are present, tracked, reproducible,
and hash-consistent, create a sibling `generalization/public-v1` worktree from
`implementation-freeze-v1`. Materialize only the public response contract,
public query bundle, three public scenario files, and a safe public manifest.

Perform static compatibility, protected-runtime, history, and leakage checks;
discover and record the already-frozen baseline and advanced configurations;
do not execute the baseline, Blackhole runtime, provider, semantic requests,
or scoring. Commit the sealed public-input-only branch locally and stop.
