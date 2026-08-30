# Initiating task

This is a summary of the attached human authorization, not a fabricated
transcript. The task is to implement a narrow Product V2 Ask provenance
precision fix in a new isolated worktree based exactly on the current HEAD of
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-language-invariance`,
on branch `product/v2-provenance-fix` at
`C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-provenance-fix`.

The required behavior is to keep bounded retrieval candidates separate from
answer-supporting evidence. Ask answers must cite only evidence materially
used in the rendered answer, while preserving all material support for current
values, history, corrections, conflicts, uncertainty, and deterministic
answers. Provider-selected evidence must be explicit and validated against
the retrieved candidate set; invented or unknown IDs must never become
provenance. Add focused provenance tests, preserve language-invariance and
provider-schema behavior, run the authorized fresh-Home live validation and
the specified full regression, update the trajectory/product documentation,
and commit only the isolated branch. Do not modify the source worktree,
master, V1 oracle/scoring worktrees, benchmark ground truth, or G01/G02/G03.
