# Summary of initiating instruction

The following is a faithful summary of the human instruction that initiated this task, based on the referenced pasted text file:

> BLACKHOLE — MACOS CROSS-PLATFORM TIMEZONE HOTFIX
>
> THIS IS A RELEASE-BLOCKING CROSS-PLATFORM HOTFIX.
>
> Work DIRECTLY on master in the current Mac clone.
>
> Do NOT create another branch.
> Do NOT create another worktree.
>
> Expected starting master HEAD:
>
> `e7341066fd00e6209b8b51b4087ea75c1609fc3a`
>
> Verify:
>
> - branch = master
> - worktree = clean
> - origin/master = e7341066fd00e6209b8b51b4087ea75c1609fc3a
>
> If not, STOP.
>
> Fix LOCAL TIMEZONE DISCOVERY generically and cross-platform.
>
> Do not touch semantic behavior unrelated to timezone discovery.
>
> Do not modify:
>
> - Product V2 model;
> - reasoning effort;
> - batch size;
> - provider prompt;
> - semantic truth logic;
> - benchmark;
> - evaluator;
> - V1 runtime semantics.
>
> Use standard library only. Preserve an IANA timezone when possible, support fixed-offset `datetime.timezone`, `zoneinfo.ZoneInfo`, Windows aliases, macOS, and Linux, and fall back truthfully to the aware local datetime's current UTC offset.
>
> Add focused platform-independent regression tests covering fixed-offset handling, `ZoneInfo.key`, numeric fallback including negative offsets, explicit timezone precedence, capture without an explicit timezone, and capture-time-relative semantics. Run focused tests first and preserve the benchmark boundaries.

The full source instruction, including the observed failure, suggested resolution order, and validation commands, is at:

`/Users/natan/.codex/attachments/a7173b66-a779-47e3-8663-a7e2e4f5b207/pasted-text-1.txt`
