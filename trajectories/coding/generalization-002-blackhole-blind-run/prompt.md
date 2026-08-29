# Prompt

## Initiating human instruction

The initiating instruction was:

> /goal Referenced pasted text files:
> - pasted text file: C:\\Users\\natan\\.codex\\attachments\\d58194d8-ad6b-4265-9b92-10d1792baca1\\pasted-text-1.txt. Read this file before continuing.

The referenced pasted text was read before work began. It authorized the following blind post-freeze execution:

```text
# GOAL — BLIND POST-FREEZE GENERALIZATION / FROZEN BLACKHOLE E005

This is the official BLIND POST-FREEZE GENERALIZATION execution of the frozen
Blackhole system.

Public branch:

generalization/public-v1

Public sealed HEAD:

39d003cfe63dcba1e5ce701bca785963b9683157

==================================================
ABSOLUTE BLINDNESS
==================================================

Do NOT use any existing Blackhole worktree.

Do NOT inspect sibling project directories.

Do NOT inspect:

generalization/oracle-v1
expected outputs
oracle generator
oracle manifest
coverage audit
defect catalog
scored results.

Do not use:

git worktree list

or local refs from an existing clone.

Create a NEW single-branch clone directly from GitHub.

Preferred path:

C:\\Users\\natan\\OneDrive\\Dokumenty\\ChatGPT\\Blackhole-gen-advanced

Conceptually:

git clone \\
  --single-branch \\
  --no-tags \\
  --branch generalization/public-v1 \\
  https://github.com/iTzRitual/Blackhole.git \\
  Blackhole-gen-advanced

Remain inside that clone.

==================================================
VERIFY PUBLIC INPUT
==================================================

Verify HEAD exactly:

39d003cfe63dcba1e5ce701bca785963b9683157

Verify NO:

benchmark/generalization/v1/expected/

Verify no ground truth/oracle/defect catalog exists in the current tree.

If any answer material exists:

STOP.

==================================================
VERIFY PUBLIC HASHES
==================================================

Expected:

g01:
7d085476b63de804f6166e6b0e94491b3f0dbc537425816f3f7bfd5b44025eb6

g02:
2676f16f53636eb0613a427cc85e2a5dd2c9496d3e79096b172cfd225d788368

g03:
cf9d32d150dac64d34059cf07041d9e0a8d075fc827afad1b1758e9ecd5a2223

contract:
c26d063189be0f44a7f099b49206d1731d0f933c60ece066c58630ce25ff0534

query bundle:
6e5a0295b239f1029e2f38b713e1cba9f6ca6c921e9f712c5022b5f34814d366

STOP if mismatched.

==================================================
FROZEN BLACKHOLE CONFIGURATION
==================================================

Use the frozen kept E005 configuration EXACTLY.

Do NOT choose configuration based on these scenarios.

Provider:
Codex CLI

Model:
gpt-5.6-luna

Semantic reasoning:
high

Batch size:
50

Relation recovery:
retrieval

Completeness:
deterministic

Duplicate evidence:
consolidate

Query projection:
deterministic ResponseProjector

Timeout:
900 seconds

DO NOT use:

--use-query-model

DO NOT change:

prompts
ontology semantics
state store
retrieval
completeness
duplicate consolidation
projection
semantic normalization.

==================================================
CREATE RUN BRANCH
==================================================

Create:

generalization/blind-blackhole-v1

from current public HEAD.

==================================================
ONE-RUN POLICY
==================================================

Each scenario receives ONE official successful candidate run.

Order:

g01
g02
g03

Do not rerun because candidate output seems weak.

Only infrastructure failure before successful candidate production allows an
operational retry.

Preserve any failed attempt evidence.

Malformed-but-produced semantic behavior is part of the observed system and
is not grounds for a quality retry.

==================================================
RUN G01
==================================================

Conceptually:

python -m app.advanced_runner \\
  --scenario benchmark/generalization/v1/cases/scenario-g01.json \\
  --query-bundle benchmark/generalization/v1/query-bundle-v2.json \\
  --response-contract benchmark/generalization/v1/response-contract-v2.json \\
  --output eval/results/generalization/v1/blackhole-g01-candidate.json \\
  --trajectory trajectories/runtime/generalization-v1-blackhole-g01 \\
  --max-events 80 \\
  --batch-size 50 \\
  --semantic-reasoning high \\
  --relation-recovery retrieval \\
  --completeness deterministic \\
  --duplicate-evidence consolidate \\
  --run-id generalization-v1-blackhole-g01 \\
  --label \"POST-FREEZE GENERALIZATION / BLIND / BLACKHOLE G01\" \\
  --timeout 900

Use the actual supported module/script invocation.

Do not modify the runner.

==================================================
G02
==================================================

Use exactly the same configuration.

Only change:

scenario
output
trajectory
run-id
label

Output:

eval/results/generalization/v1/blackhole-g02-candidate.json

Trajectory:

trajectories/runtime/generalization-v1-blackhole-g02

==================================================
G03
==================================================

Same frozen configuration.

Output:

eval/results/generalization/v1/blackhole-g03-candidate.json

Trajectory:

trajectories/runtime/generalization-v1-blackhole-g03

==================================================
NO SCORING
==================================================

Do NOT run:

eval/score.py
eval/score_slice.py

Do not calculate:

LQA
DSCR
TP/FP/FN
category accuracy.

Do not manually inspect semantic quality against any oracle.

==================================================
STRUCTURAL VALIDATION ONLY
==================================================

Allowed:

- JSON parse;
- response contract name;
- scenario ID;
- checkpoints;
- required public query IDs;
- source refs refer to received public captures.

Do not repair model-produced facts.

Do not tune after seeing outputs.

==================================================
RUNTIME EVIDENCE
==================================================

Preserve authentic runtime traces.

Record per scenario:

- number of extraction calls;
- model;
- reasoning;
- input tokens;
- output tokens;
- reasoning tokens;
- provider runtime;
- completeness behavior;
- relation recovery behavior;
- duplicate consolidation stats;
- final state counts.

Do not record chain-of-thought.

==================================================
HASH AND SEAL
==================================================

Compute SHA-256 of:

blackhole-g01-candidate.json
blackhole-g02-candidate.json
blackhole-g03-candidate.json

Create:

eval/results/generalization/v1/BLACKHOLE_CANDIDATE_MANIFEST.json

Include:

- public HEAD;
- frozen implementation reference;
- exact runtime configuration;
- scenario IDs;
- candidate hashes;
- runtime/usage;
- operational retries;
- statement:

  \"These frozen Blackhole candidates were sealed before any generalization
  expected output was available in this clone and before any scoring.\"

No expected hashes.

==================================================
CODING TRAJECTORY
==================================================

Create:

trajectories/coding/generalization-002-blackhole-blind-run/

prompt.md
summary.md

Do not speculate about score.

==================================================
FROZEN DEV CHECK
==================================================

Do NOT rerun provider work on DEV.

You may run the existing deterministic E005 replay ONLY if necessary to
confirm the runner configuration, but prefer relying on already frozen
evidence.

No semantic tuning.

==================================================
COMMIT AND PUSH
==================================================

Commit only:

candidate files
runtime trajectories
candidate manifest
coding trajectory

Suggested:

generalization: seal blind Blackhole candidates

Push:

generalization/blind-blackhole-v1

Do not merge.

==================================================
DIFF CHECK
==================================================

Compare against:

generalization/public-v1

There must be no modification to:

app/**
prompts/**
baseline/**
benchmark/**
eval/score.py

Only candidate/results and evidence additions.

==================================================
RETURN
==================================================

Return:

BLIND BLACKHOLE CANDIDATE GATE

Include:

1. fresh clone path;
2. branch;
3. public base SHA;
4. blindness audit;
5. exact frozen configuration;
6. g01 runtime;
7. g02 runtime;
8. g03 runtime;
9. provider calls per scenario;
10. token usage per scenario;
11. operational retries;
12. g01 candidate SHA;
13. g02 candidate SHA;
14. g03 candidate SHA;
15. manifest SHA;
16. final state counts;
17. commit SHA;
18. pushed branch;
19. confirmation no expected output was accessible;
20. confirmation no scoring;
21. confirmation no frozen runtime changes.

STOP.
```
