# Product V2 integration task

Source instruction: the human-provided pasted brief at
`C:\Users\natan\.codex\attachments\6ec97fb9-ca56-4544-8cce-3d2c84b460a9\pasted-text-1.txt`.

Summary of the authorization in that brief: create the isolated fourth
worktree `C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-integration`
on branch `product/v2-integration`, based exactly on
`68b7b15d353b12cffb65a770f8583aa0ebb849dd`; verify and merge the Product V2
runtime (`cbf706b6497ae22e1c964b991a6ca1ec6a4307c9`), UI
(`35854aad409a964057572ffcfa8667e1af287325`), and dogfood
(`ef63200854b1480a0c102c14f5f3a6aec9f09ab2`) branches with normal merge
commits; reconcile the real Host/API and UI for capture, attachments,
background processing, Attention, open-world Memory, Ask, and Undo; run the
independent acceptance suite, deterministic/reliability/HTTP checks, and
local visual review; document reproducible evidence; and commit only the
integration branch.

The brief explicitly prohibits modifying the three source worktrees, master,
historical V1 benchmark/evaluator/baseline/calibration evidence, or oracle and
generalization material. The final report must distinguish Product V2
acceptance from frozen V1 evaluation and honestly report PASS/PARTIAL/FAIL,
known limitations, skipped live smoke, and unchanged boundaries.
