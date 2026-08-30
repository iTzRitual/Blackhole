# Prompt record

Source: `C:\Users\natan\.codex\attachments\10a0cecf-80df-454c-ac82-68726df0e3e5\pasted-text-1.txt`

The initiating instruction was supplied as a pasted task brief. The following
is a faithful summary of the instruction, not a fabricated verbatim transcript:

- Create an independent Product V2 dogfood / acceptance system on branch
  `product/v2-dogfood`, in the dedicated worktree
  `C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-dogfood`, based exactly
  on commit `68b7b15d353b12cffb65a770f8583aa0ebb849dd`.
- Do not edit, inspect, merge, switch, or cherry-pick the concurrent
  `product/v2-runtime` and `product/v2-ui` worktrees, and do not access local
  generalization-oracle/scoring worktrees.
- Do not modify product code, runtime, frontend, prompts, V1 expected answers,
  V1 scoring, or benchmark ground truth. Do not create a hidden optimization
  oracle or call a live model unnecessarily.
- Design from product intent and real dogfood failures. Build an honest
  development acceptance suite that tests whether a normal person could trust
  Blackhole as external memory, including messy ordinary-life information,
  English and Polish captures, and both single- and multi-step cases.
- Add approximately 40–60 realistic machine-readable acceptance cases covering
  capture, memory, attention, Ask, Undo, attachments, reliability, open-world
  memory, corrections, uncertainty, duplicates, contradictions, changing plans,
  and cross-capture retrieval. Include the specified seed examples and explicit
  Attention false-positive cases.
- Define a black-box case format with timestamps/timezones, capture sequences,
  optional attachments, time advances, expected user-visible behavior, Ask
  questions, Attention expectations, retrieval/evidence expectations, and
  retraction actions. Do not encode hidden implementation predicates.
- Add safe small fixtures, schemas, a deterministic mock/stub harness that can
  later target the integrated V2 Host through an adapter, and skips when the
  current base does not expose that API. CI must not call live Codex.
- Add a 15–25 minute human dogfood protocol with plain-language PASS/FAIL
  observations plus a separate technical troubleshooting appendix.
- Define product-level quality gates and PASS/FAIL/PARTIAL/NOT TESTED reporting
  separately from historical LQA. Document that visible cases are development
  acceptance tests, not unseen generalization evidence.
- Validate case parsing, schema behavior, duplicate-ID rejection,
  timestamp/timezone validation, fixture resolution, deterministic mock runs,
  no live provider requirement, and no product implementation-file changes.
- Create `docs/PRODUCT_V2_DOGFOOD.md`, an organized acceptance directory, and
  the coding trajectory under
  `trajectories/coding/033-product-v2-dogfood-acceptance/`.
- Commit only the coherent acceptance-system changes to `product/v2-dogfood`.
- Return a Product V2 Dogfood Acceptance Gate report containing branch, base and
  final SHAs, worktree, case count, coverage, false-positive/open-world/
  attachment/reliability coverage, protocol, harness status, tests,
  limitations, changed files, and explicit confirmations that app code,
  runtime/UI worktrees, V1 oracle, and V1 benchmark tuning were untouched.
