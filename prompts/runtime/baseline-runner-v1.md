# Baseline runner protocol v1

This document is the fixed harness protocol paired with the frozen
`baseline-v1.md` prompt. It does not add Blackhole memory, retrieval, entity
resolution, a database, or a hidden summary.

The runner creates one persistent Codex CLI canonical ingestion session. The
canonical session receives the baseline prompt and chronological batches of the
public raw captures. A batch contains one JSON object per capture in sequence
order; batching is only a transport optimization and does not alter the capture
content or order. The canonical session is never asked a substantive query.

At events 50, 100, 150, and 200, the runner forks the canonical session. It
sends the fixed public query bundle only to that fork, records the structured
response, and never resumes that fork. The canonical parent then receives the
next capture batch. This prevents a checkpoint question or answer from becoming
part of later ingestion history.

The provider receives no development expected output, defect catalog, evaluator
code, Blackhole database, repository rules, or hidden state. The CLI runs from a
fresh empty temporary workspace with read-only sandboxing inherited by resumed
and forked sessions. The runner records provider metadata, usage, duration,
retries, and errors, but does not read or persist provider credentials.
