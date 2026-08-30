/goal GENERALIZATION V1R1 — VERIFY SEALED CANDIDATES → OPEN ORACLE → SCORE ALL 6 → FINAL GENERALIZATION REPORT

This is the FIRST task in which V1R1 generalization oracle / expected outputs
may be accessed.

The blind candidate phase is complete.

Do NOT modify any runtime, prompt, candidate, benchmark case, response contract,
query bundle, expected output, or evaluator.

Do NOT invoke Codex/model/provider inference during scoring.

This task is deterministic verification + scoring + analysis only.

==================================================
KNOWN SEALED REFERENCES
==================================================

Repository:
https://github.com/iTzRitual/Blackhole

PUBLIC V1R1 BASE:
generalization/public-v1r1
79bea04e432e6566e3d6989e8fa411e7c613908b

LOCAL REPAIRED ORACLE HEAD:
fc707cb485629919434dc41f4014f10d5065b4db

The oracle branch/history is intentionally local-only.
DO NOT PUSH oracle history or a branch containing expected outputs to origin.

SEALED BASELINE:
branch:
generalization/blind-baseline-v1r1

remote head:
f58466a2605d38e324cfc565c011eb84591a2fee

candidate hashes:
g01:
943571f22882429a0518005ba41cbc9ffba3d3a73153ac2aae9f18e1287bc71b

g02:
2bdc02ab4f0d51b612ede8281d9dedafba837c0e2d56608ba16248740626f59c

g03:
0a1e1674aab9e80a59c3318e83693b151fab1f6c79a6b153024e33f1269f0e3f

Baseline operational retries:
g01 = 0
g02 = 2
g03 = 1
semantic-quality retries = 0

SEALED BLACKHOLE:
branch:
generalization/blind-blackhole-v1r1

remote head:
9d2ee431079fc7ad7b1921677eac3d15123cbe34

candidate hashes:
g01:
ab80ab7a3f096c456f1f18c6839141809ed51751c1968c5a12e16115e601c361

g02:
3a69cb75b287ac999ef0cc66f10f6e9fd3bf8588fe2c65c4b0922cc12ac1d667

g03:
07557d68f3361daa9d4c03567f4bb6de52e9fc4a14f803a4d4f376fdfc76d208

Blackhole operational retries:
g01 = 0
g02 = 0
g03 = 0

==================================================
ORACLE / PUBLIC HASHES
==================================================

Verify these BEFORE scoring.

Response contract:
c26d063189be0f44a7f099b49206d1731d0f933c60ece066c58630ce25ff0534

Query bundle:
6e5a0295b239f1029e2f38b713e1cba9f6ca6c921e9f712c5022b5f34814d366

V1R1 public cases:

g01:
c0dd1c6255c3591fb4467e8ac6bb4e46bffbd37661cf38bcb6ba67a9247a3cb5

g02:
22747fe3e01b4ed4ae41e5a0682cc584e72c487f7c9cff53a29d233d9d35f938

g03:
ca19c548d60c0a77ba742aa6c00532fac26d335dadcfdca86d209786744c3fec

Expected-output hashes:

g01:
f8e488e0da1c2b2348ba801532ba4276564a4b0041d41e8a47d766770d55a3e6

g02:
6176df7f65af0e3398225f26b86dd1be870e5d49302b59aa9c6e85a6c41d2dba

g03:
7507692a6944f3b03cfa7300a0d0dc1ce72916607a0b4af560f751ef42be169d

==================================================
PHASE 0 — CREATE ISOLATED LOCAL SCORING WORKTREE
==================================================

Current worktree should be:

C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-generalization-oracle

First verify:

- current worktree is clean;
- local oracle HEAD is exactly
  fc707cb485629919434dc41f4014f10d5065b4db;
- expected/oracle content is present;
- no candidate artifacts have been modified.

Create a NEW LOCAL worktree:

C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-generalization-scoring-v1r1

Local branch:

generalization/score-v1r1

Base it EXACTLY on:

fc707cb485629919434dc41f4014f10d5065b4db

If that path or branch already exists unexpectedly, STOP and report rather
than reusing an unknown workspace.

IMPORTANT:

This scoring branch contains oracle history.

DO NOT PUSH:
generalization/score-v1r1

DO NOT PUSH:
generalization/oracle-v1

Do not create any remote branch containing expected outputs.

==================================================
PHASE 1 — VERIFY THE BLIND SEALS BEFORE OPENING RESULTS
==================================================

Fetch from origin:

generalization/public-v1r1
generalization/blind-baseline-v1r1
generalization/blind-blackhole-v1r1

Verify exact remote heads:

public:
79bea04e432e6566e3d6989e8fa411e7c613908b

baseline:
f58466a2605d38e324cfc565c011eb84591a2fee

Blackhole:
9d2ee431079fc7ad7b1921677eac3d15123cbe34

Do NOT merge either candidate branch into the oracle branch.

Materialize candidate files from the exact sealed commits using a
byte-preserving method such as `git show <commit>:<path>` captured as bytes.

Do not JSON-parse and rewrite the candidates before hashing them.

Materialize:

baseline:
eval/results/generalization/v1/baseline-g01-candidate.json
eval/results/generalization/v1/baseline-g02-candidate.json
eval/results/generalization/v1/baseline-g03-candidate.json

Blackhole:
eval/results/generalization/v1/blackhole-g01-candidate.json
eval/results/generalization/v1/blackhole-g02-candidate.json
eval/results/generalization/v1/blackhole-g03-candidate.json

Also materialize both candidate manifests from their exact sealed commits.

Recompute SHA-256 for all six candidate files.

They MUST exactly match the six hashes stated above.

If ANY candidate hash differs:
STOP.
Do not score.
Return SEAL VERIFICATION FAILURE.

For the manifests:
recompute their SHA-256 independently and record it.

Do not trust a hash copied from a prose handoff.
There was a known display typo in the baseline handoff's manifest-hash line;
the actual file bytes are authoritative.

Verify both manifests independently state:
- correct public HEAD;
- no oracle access before sealing;
- no scoring before sealing;
- expected frozen configurations;
- correct candidate hashes.

Verify candidate branches do not contain V1R1 generalization expected/oracle
material.

Historical DEV expected material remains irrelevant and is not a failure.

Create a seal-verification evidence JSON before scoring.

==================================================
PHASE 2 — VERIFY ORACLE AFTER CANDIDATES ARE VERIFIED
==================================================

Only after Phase 1 passes:

inspect the repaired V1R1 oracle.

Verify:

- oracle HEAD exactly:
  fc707cb485629919434dc41f4014f10d5065b4db

- response contract SHA-256 matches;
- query bundle SHA-256 matches;
- all three V1R1 public case SHA-256 values match;
- all three expected-output SHA-256 values match.

Use the repaired V1R1 expected files, not historical original-v1 files.

Confirm the oracle/public semantic repair record says the V1→V1R1 change was
payload-shape-only and expected assertions were semantically invariant except
for permitted raw-event-hash repair metadata.

Do not change anything if a mismatch appears.

If ANY required oracle/public hash fails:
STOP.
Do not score.
Return ORACLE VERIFICATION FAILURE.

==================================================
PHASE 3 — SCORE ALL SIX CANDIDATES
==================================================

Use the EXISTING frozen deterministic evaluator.

Do NOT edit:
eval/score.py

Do NOT create a new scoring formula.

The scorer exposes:

python -m eval.score
  --scenario ...
  --expected ...
  --candidate ...
  --response-contract ...
  --output ...

Discover the exact repaired V1R1 case and expected filenames from the oracle
tree rather than guessing filenames.

Score:

baseline g01
baseline g02
baseline g03

Blackhole g01
Blackhole g02
Blackhole g03

Produce six immutable score JSON artifacts under a clearly named directory,
for example:

eval/results/generalization/v1/scored/

Use names that unambiguously identify:
- system;
- scenario;
- V1R1.

No provider/model calls are permitted.

For each scored candidate record at minimum:

- LQA-0M;
- checkpoint LQA values;
- TP;
- FP;
- FN;
- precision;
- recall;
- F1;
- DSCR count;
- DSCR per 100 events;
- schema validity;
- source integrity;
- safety;
- hard_failure;
- category metrics;
- knowledge-status metrics;
- attention false-positive rate.

Do not omit poor results.

==================================================
PHASE 4 — MACRO GENERALIZATION RESULT
==================================================

Create one deterministic aggregate report.

Because all three worlds have the same 80-event size:

PRIMARY:

For each system:

macro_LQA_0M =
arithmetic mean of scenario g01/g02/g03 LQA-0M.

Also report:
- each scenario LQA separately;
- mean checkpoint score for checkpoint 20 across worlds;
- same for 40, 60, 80.

SECONDARY:

Report:
- DSCR total across all three scenarios;
- DSCR per 100 events over all 240 fresh events;
- mean per-scenario DSCR;
- total TP / FP / FN;
- micro precision / recall / F1 from aggregate TP/FP/FN;
- hard failures;
- source-integrity failures;
- safety failures.

COMPARISON:

Report:

Blackhole macro LQA
minus
Baseline macro LQA

as absolute delta.

Also compute relative LQA improvement where mathematically defined.

Report error-rate reduction using:

error = 1 - LQA

and:

1 - (Blackhole error / Baseline error)

only if baseline error > 0.

Clearly label all formulas.

Do not invent statistical significance from only three scenarios.

==================================================
PHASE 5 — EFFICIENCY / RELIABILITY COMPARISON
==================================================

Use only sealed manifests/runtime evidence.

Do not rerun anything.

For successful candidates report:

- per-scenario successful-candidate runtime;
- mean successful-candidate runtime;
- total successful-candidate runtime;
- provider/model configuration;
- successful-run token usage where recorded.

Report operational reliability separately:

Baseline:
g01 0 retries
g02 2 operational retries
g03 1 operational retry

Blackhole:
0 retries across all three scenarios.

If failed-attempt runtime is explicitly and reliably recorded, you MAY also
calculate observed total benchmark execution time including operational failures.

If that evidence is incomplete or ambiguous:
do not estimate it.

Never mix "successful candidate runtime" with "wall clock including failed
attempts" without labeling them separately.

==================================================
PHASE 6 — FAILURE ANALYSIS
==================================================

Now that scoring is legitimately open, perform a descriptive analysis only.

NO TUNING.

Identify:

- weakest baseline query families/categories;
- weakest Blackhole query families/categories;
- where Blackhole most improves over baseline;
- where Blackhole still fails;
- variation across g01/g02/g03;
- known vs inferred vs unknown behavior;
- attention-related false positives/false negatives if visible from evaluator;
- duplicate/change/relation performance if supported by scored category data.

Distinguish:

A. semantic correctness failure;
B. schema/output failure;
C. source/provenance failure;
D. operational reliability failure.

Do not inspect expected answers in order to propose code changes in this task.

Do not modify runtime after seeing failures.

This is analysis of the frozen system, not an optimization task.

==================================================
PHASE 7 — REPORTS
==================================================

Create:

1.
eval/results/generalization/v1/GENERALIZATION_V1R1_RESULT.json

Machine-readable report containing:
- all six score artifact paths/hashes;
- verified candidate hashes;
- verified oracle hashes;
- per-scenario metrics;
- macro/micro metrics;
- efficiency/reliability comparison;
- explicit no-tuning statement.

2.
docs/GENERALIZATION_V1R1_REPORT.md

Human-readable report.

It must explain the chronology:

implementation freeze
→ V1 test-world creation
→ zero-call payload schema repair / V1R1 reseal
→ blind baseline + blind Blackhole candidate sealing
→ oracle opened only after both candidate sets were sealed
→ deterministic scoring
→ no post-result semantic tuning.

Include an explicit caveat:

This is a post-freeze shadow/generalization set of three fresh synthetic worlds,
not an organizer-provided official holdout and not a claim of statistical
significance.

3.
trajectories/coding/030-generalization-v1r1-scoring/

Include at minimum:
- prompt.md
- summary.md
- seal-verification.json

Record commands and hashes necessary to reproduce the score.

==================================================
PHASE 8 — LOCAL COMMIT ONLY
==================================================

Run relevant deterministic evaluator tests if they do not access a provider.

Do not run model/provider calls.

Verify git diff carefully.

Allowed modifications in the scoring branch:

- six score JSON artifacts;
- GENERALIZATION_V1R1_RESULT.json;
- docs/GENERALIZATION_V1R1_REPORT.md;
- trajectories/coding/030-generalization-v1r1-scoring/**

Do NOT modify:
- app/**
- baseline/**
- prompts/**
- benchmark/**
- eval/score.py
- candidates
- manifests
- expected files
- oracle files.

Make one coherent LOCAL commit:

generalization: score sealed V1R1 candidates

DO NOT PUSH THIS BRANCH.

The scoring branch descends from local oracle history and must remain local.

==================================================
FINAL OUTPUT
==================================================

Return:

# GENERALIZATION V1R1 SCORE GATE

PASS / FAIL

Then show a compact table:

System | G01 LQA | G02 LQA | G03 LQA | Macro LQA | DSCR total | DSCR/100

Then:

- absolute LQA delta;
- error-rate reduction;
- successful-candidate mean runtime;
- operational retry count;
- hard-failure count.

Then:

- candidate seal verification status;
- oracle verification status;
- scorer version;
- local scoring commit SHA;
- exact report paths;
- explicit confirmation:
  no model/provider calls,
  no runtime modifications,
  no post-result tuning,
  scoring branch NOT pushed.

If any seal/oracle verification fails:
STOP before scoring and clearly report the failed gate.
