# Authorizing prompt

The direct human instruction was supplied in the referenced pasted text file:

`C:\Users\natan\.codex\attachments\0c629a02-2490-4619-b1d6-02f903b516b9\pasted-text-1.txt`

The file begins with `/goal BLACKHOLE PRODUCT V2 — HUMAN DOGFOOD P0 FIXES` and
authorizes implementation in a new isolated worktree only:

- source evidence: `Blackhole-v2-integration`, branch `product/v2-integration`,
  required HEAD `4224d826a5c35811f5eae582a510144cdce77e73`;
- target worktree: `Blackhole-v2-dogfood-fixes`, branch
  `product/v2-dogfood-fixes`, based exactly on that SHA;
- preserve the integration worktree, master, all other Product V2 worktrees,
  the frozen V1 benchmark/evaluator/baseline, and the human-dogfood home;
- diagnose and fix the Product V2 store/queue mismatch, real PWA V2 routing,
  normal `app.web_app` background processing, the actual Codex provider failure,
  retry spinning, truthful pending/failed UI state, and stale service-worker
  updates;
- add a deterministic regression covering a fresh home, normal web launch,
  real HTTP V2 capture, delayed semantic processing, Memory, Attention, Ask,
  status agreement, and no legacy-queue dependency;
- only after deterministic fixes pass, run at most two live neutral captures and
  two Ask questions in a new temporary home, without benchmark cases or manual
  `product_process` processing;
- inspect the existing human-dogfood home only read-only, hash it before and
  after, document all evidence, run the specified validation suites, and
  commit only on `product/v2-dogfood-fixes`;
- report the final gate as PASS only when both the normal-launch regression and
  the live Codex normal-launch smoke succeed; otherwise report PARTIAL with the
  exact sanitized operational failure.

This is a faithful task summary, not a fabricated transcript. The referenced
file remains the source of the complete instruction.
