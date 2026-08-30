# Task prompt

This task was initiated by the user’s `/goal` message referencing the pasted
text file:

`C:\Users\natan\.codex\attachments\5ca2d5ea-d795-4239-8f43-63310b20bc6c\pasted-text-1.txt`

The file was read before implementation. It authorizes a time-boxed final
Product V2 task on a new isolated worktree based exactly on
`05c337b46798031adea8ee0f1cf6b34b40572bc1`:

- implement permanent Undo/forget semantics, including pending, processing,
  processed, failed/retry, race-safe late-provider handling, idempotency,
  semantic-truth-compatible rebuild behavior, raw-content deletion, and
  content-addressed attachment garbage collection;
- add concise human-readable Product V2 PowerShell/server operational logs with
  default sanitization and useful lifecycle, provider, Ask, retry, and Undo
  information;
- add the specified deterministic Undo, deletion, attachment, semantic, Ask,
  Attention, Memory, provenance, race, and logging regressions;
- preserve benchmark/evaluator boundaries and existing behavior outside this
  scope, without changing the source semantic-truth worktree, other worktrees,
  or master;
- run relevant validation plus the explicitly authorized bounded live smoke;
- update the Product V2 documentation, trajectory evidence, and changelog where
  applicable, then commit only on `product/v2-undo-logs` and stop.

This is a faithful scope summary of the referenced instruction, not a fabricated
session transcript. The referenced file remains the source of the full wording.
