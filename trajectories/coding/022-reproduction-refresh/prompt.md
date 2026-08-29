# GOAL — JUDGE-FACING REPRODUCTION REFRESH

This is a DOCUMENTATION-ONLY post-freeze task.

Another worktree is independently designing the post-freeze generalization
oracle.

Do not interact with it.

Current remote master HEAD:

8d3b4ff7a1979540f2e65dd9b493f0731e006f72

Frozen implementation SHA:

171a6cc1c656d6ab901f41bda8440ee5d59967e3

==================================================
PURPOSE
==================================================

Correct judge-facing instructions so they describe the CURRENT integrated
Blackhole Host + PWA rather than the superseded seeded-demo transport.

This task MUST NOT change:

runtime behavior
benchmark behavior
evaluation behavior
generalization
metrics

==================================================
WORKTREE
==================================================

Do NOT switch the primary worktree.

Create:

branch:
submission/reproduction-refresh

worktree:
../Blackhole-reproduction-refresh

from:

8d3b4ff7a1979540f2e65dd9b493f0731e006f72

All edits happen there.

Do NOT merge during this goal.

==================================================
HARD FREEZE
==================================================

DO NOT MODIFY:

app/**
baseline/**
benchmark/**
eval/**
prompts/**
.github/workflows/**
scripts/**

If documentation is inconsistent with code:

correct the documentation.

Do NOT modify code to make old documentation true.

==================================================
KNOWN ISSUE TO VERIFY
==================================================

The current README and docs/REPRODUCTION.md may still describe the earlier
seeded demo flow:

python scripts/seed_demo.py --reset
python -m app.web_app ...

and may describe:

POST /api/reset
automatic demo seeding
a separate demo SQLite database

The integrated frozen product no longer uses that as its normal Host path.

Inspect the actual current code and correct all CURRENT/JUDGE-FACING claims.

Historical documentation and trajectories may retain the old demo history.

Do not rewrite history.

==================================================
AUTHORITATIVE CURRENT PRODUCT MODEL
==================================================

Judge-facing docs should reflect:

Blackhole App
= mobile-first PWA served by Blackhole Host

Blackhole Host
= local Python runtime + BLACKHOLE_HOME + SQLite + deferred ingestion

Codex Provider
= externally authenticated local Codex CLI

Current flow:

Capture
→ HostRuntime.capture()
→ immutable raw event
→ pending
→ immediate Saved.

Later Ask:
→ ensure_state_fresh()
→ process pending when needed
→ Codex semantic extraction
→ deterministic/rebuildable state
→ bounded query projection
→ response

==================================================
PRIMARY QUICKSTART
==================================================

Establish and verify the current minimal run path.

Expected direction:

python -m app.host init
python -m app.host doctor
python -m app.web_app --host 127.0.0.1 --port 8080

Then:

http://127.0.0.1:8080

Use the ACTUAL implemented commands/options.

Do not invent commands.

Document that:

- Codex authentication is external;
- no OPENAI_API_KEY is required;
- capture works even if provider processing is unavailable;
- semantic freshness requires authenticated Codex when pending captures exist.

==================================================
TRUSTED LAN DEMO
==================================================

Document the existing explicit phone-demo path accurately:

python -m app.web_app \
  --host 0.0.0.0 \
  --port 8080 \
  --trusted-lan-demo

State prominently:

- trusted private network only;
- no device authentication;
- no pairing;
- no TLS;
- not Internet-safe.

Do NOT market this as production remote access.

==================================================
REAL SMOKE
==================================================

Document the existing neutral Host smoke command accurately.

Inspect:

scripts/host_smoke.py

Provide a repository-relative example output path.

Do not run it unless an authenticated Codex call is explicitly needed.

The normal docs-validation path should not consume model inference.

==================================================
OLD SEEDED DEMO
==================================================

Do NOT delete:

scripts/seed_demo.py
app/demo.py
historical demo trajectories

They are historical/reproducibility evidence.

But make it unambiguous that:

the old seeded-demo database is NOT the normal integrated Host database.

If kept in docs, label it:

Historical deterministic demo utility

not:

Try the current product

Do not claim the current Host auto-seeds it.

Do not claim /api/reset exists if the current transport does not expose it.

==================================================
README REFRESH
==================================================

Update README.md narrowly.

At minimum:

1. Replace stale "Try the local demo" instructions with current Host/PWA
   quickstart.

2. Update "What is implemented" so it includes current components such as:

   app/host.py
   app/runtime_config.py
   app/codex_discovery.py
   app/query_service.py
   app/web_app.py
   app/web/

   using their actual responsibilities.

3. Preserve:
   - product idea;
   - frozen DEV baseline;
   - E005 result;
   - honest limitations.

4. Make `final-comparison-v1.json` unmistakably historical/superseded if it is
   referenced.

5. Do NOT add a post-freeze generalization score.

6. Do NOT call E005 holdout evidence.

Do not perform the final submission-copy rewrite yet.

==================================================
REPRODUCTION REFRESH
==================================================

Update docs/REPRODUCTION.md.

Preserve historical benchmark reproduction sections.

Correct the CURRENT PRODUCT section.

Separate clearly:

A. historical seeded demo utility

B. current integrated Blackhole Host/PWA

C. benchmark reproduction

D. real Codex smoke

No developer-specific absolute paths.

==================================================
SUBMISSION CHECKLIST
==================================================

Update docs/SUBMISSION_CHECKLIST.md only for facts genuinely resolved by this
task.

For example:

- current reproduction docs corrected;
- current quickstart checked.

Do NOT mark complete:

generalization
final comparison
final README hot take
final main failure mode
video
HackerEarth submission

unless actually completed.

==================================================
TAG VERIFICATION
==================================================

Verify local and REMOTE state of:

implementation-freeze-v1

Use commands equivalent to:

git show implementation-freeze-v1 --no-patch
git ls-remote --tags origin implementation-freeze-v1

Expected documented handoff target:

8d3b4ff7a1979540f2e65dd9b493f0731e006f72

If:

- the local tag exists;
- it points EXACTLY to the documented target;
- remote tag is missing;

then push ONLY that existing tag:

git push origin implementation-freeze-v1

Do NOT recreate or move it.

If the local tag points anywhere else:

STOP and report.

Do not force-push a tag.

==================================================
VALIDATION
==================================================

Without provider inference, verify:

python -m app.host --help
python -m app.web_app --help

Use a temporary BLACKHOLE_HOME and run current safe setup/doctor commands.

Run deterministic tests if practical.

Do not alter ~/.blackhole during validation.

Do not require Codex inference.

Check all README/reproduction commands against the actual CLI.

==================================================
NO VIDEO REWRITE YET
==================================================

Do NOT rewrite:

docs/VIDEO_SCRIPT.md
docs/VIDEO_SHOT_LIST.md

They will be rewritten AFTER post-freeze generalization because the final
measured story is not known yet.

You may report that they are stale.

==================================================
TRAJECTORY
==================================================

Create:

trajectories/coding/022-reproduction-refresh/

prompt.md
summary.md

Record:

- stale claims found;
- current code used as authority;
- docs corrected;
- commands verified;
- tag remote status;
- no runtime changes;
- commit.

==================================================
COMMIT
==================================================

Suggested:

docs: refresh Host reproduction instructions

Commit on:

submission/reproduction-refresh

Do NOT merge.

==================================================
RETURN
==================================================

Return:

REPRODUCTION REFRESH GATE

Include:

1. worktree;
2. branch;
3. base SHA;
4. stale claims removed/corrected;
5. current quickstart;
6. Host/Codex prerequisites;
7. trusted-LAN wording;
8. historical seeded-demo treatment;
9. README changes;
10. REPRODUCTION changes;
11. commands actually validated;
12. remote freeze-tag status;
13. whether tag needed pushing;
14. files changed;
15. confirmation zero app/runtime/eval changes;
16. remaining stale video docs;
17. remaining generalization/final-comparison work;
18. commit SHA.

STOP.
