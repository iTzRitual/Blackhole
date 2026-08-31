# ChatGPT advisory decision log

This is a submission-safe summary of ChatGPT's advisory role in the Blackhole
project. A complete private advisory transcript exists locally and informed
this record, but the transcript is not committed, copied, or published. This
file is not a coding trajectory, not a provider trace, and not a reconstructed
transcript. The coding and runtime trajectories in `trajectories/` remain the
authoritative records of agent implementation work.

## Role and boundaries

ChatGPT was used as an advisory planning and interpretation layer. It helped
turn observed failures into bounded work, compare evidence against the project
contract, identify when a change needed explicit authorization, and keep V1
benchmark/evaluator boundaries separate from Product V2 product work. It did
not own the repository, authenticate a provider, access V1 oracle/scoring
worktrees, or author the coding trajectories on behalf of the implementation
agent.

The human remained the product owner and final decision-maker. ChatGPT advice
could be accepted, rejected, constrained, or redirected; implementation claims
come from the corresponding Codex trajectory and Git evidence rather than from
the advisory transcript.

The advice consistently preserved these constraints:

- raw evidence remains immutable during normal operation and derived state is
  rebuildable;
- unknown, inferred, conflicting, and confirmed values remain distinct;
- deterministic time, arithmetic, lifecycle, duplicate, and aggregation work
  stays in code or SQL;
- consequential actions require explicit user approval; and
- evaluator-owned holdout ground truth remains outside the implementation
  boundary.

## Decision progression

### 1. Benchmark and experiment planning

The early advisory work helped frame Blackhole as a longitudinal state-
maintenance problem rather than a static extraction or OCR contest. It supported
the decision to calibrate history length, freeze the public 200-event
development scenario with four checkpoints, and use a stateless fair baseline
with a fixed response contract. It also helped distinguish an experiment's
hypothesis, metric, replay evidence, and disposition from general project
notes.

### 2. Interpreting the V1 results

The large DEV improvement from the stateless baseline to the kept E005 replay
was treated as evidence about the frozen synthetic development world, not as a
holdout or production claim. When the three fresh post-freeze synthetic worlds
showed a much smaller transfer, the advisory conclusion was to report the gap
plainly rather than tune the baseline or rewrite the benchmark narrative.

The durable lesson became:

> Optimizing an agent for measurable structured correctness can accidentally
> optimize the product away from the user.

### 3. Worktree isolation and architecture discussion

ChatGPT advised keeping the frozen V1 runtime and evidence stable while Product
V2 work proceeded in explicitly isolated runtime, UI, acceptance, and repair
workstreams. The architecture discussion emphasized a local Host ownership
boundary, subscription-first CLI authentication, an immediate durable Capture,
an asynchronous queue, open-world Memory, deterministic projections, and an
approval boundary for external actions.

### 4. Dogfood interpretation and P0/P1 sequencing

Human dogfooding was treated as a separate product-quality signal. The advisory
review helped classify observed problems into lifecycle/queue ownership,
provider schema and diagnostics, Ask routing, language invariance, provenance,
semantic truth, permanent Undo, operational logging, and final presentation.
Each follow-up was kept narrow, recorded in its own trajectory, and stopped at
the authorized scope or live-call limit.

The advice explicitly rejected using a benchmark-shaped case as a substitute
for human product evidence. It also kept the real provider latency disclosure
intact: Capture is immediate, while semantic understanding is asynchronous and
can still be slow.

### 5. Gates and integration

ChatGPT helped define the distinction between deterministic acceptance,
authenticated live smoke, visual review, and unseen generalization. The
integrated Product V2 result was therefore recorded as development acceptance
and dogfood evidence (`50/50`), not as an unseen benchmark result. The final
configuration boundary was kept explicit: Product V2 uses low reasoning and
batch size 2, while legacy/V1-compatible settings remain separate.

### 6. Submission planning

For final submission preparation, the advisory focus moved from product changes
to judge comprehension and reproducibility: a first-screen README, a five-
minute demo path, a safe synthetic prepared Home, V1/Product V2 evidence
separation, known limitations, trajectory discoverability, privacy hygiene,
deterministic verification, and exact Git master/tag/remote checks.

## What this record does not claim

This log does not claim that ChatGPT directly authored any coding trajectory,
performed a live provider run, saw private human dogfood data, or accessed
holdout expected outputs. It records the role of advisory reasoning at the
level needed to understand the project decisions; it intentionally omits
private information, credentials, raw model output, and hidden reasoning.
