# Human instruction summary (not verbatim)

Execute the official blind post-freeze generalization V1R1 long-chat baseline
from a fresh single-branch clone of the public `generalization/public-v1r1`
branch at public HEAD `79bea04e432e6566e3d6989e8fa411e7c613908b`. Work only
inside the new clone, do not inspect generalization oracle material, and do
not score or semantically assess any candidate.

Verify the public files, payload transport shape, and supplied public SHA-256
hashes. Create `generalization/blind-baseline-v1r1` from that HEAD. Run the
existing frozen baseline runner without modification for g01, g02, and g03 in
order using the baseline-v1 prompt, baseline-runner-v2 prompt, Codex CLI,
`gpt-5.6-luna`, reasoning `max`, read-only isolated workspace, one persistent
chronological conversation, and native discarded checkpoint forks. Produce
exactly one successful candidate per scenario; retry only operational failures
and preserve failed attempts.

After successful runs, perform structural-only validation, hash the candidates,
create the candidate manifest, preserve runtime and coding evidence, commit only
the allowed evidence artifacts, and push the run branch without merging. Do
not modify application, baseline, prompt, benchmark, or evaluator code/config.
