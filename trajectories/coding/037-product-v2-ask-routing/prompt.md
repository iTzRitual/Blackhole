# Human task authorization

The initiating user message was:

> /goal Referenced pasted text files:
> - pasted text file: C:\Users\natan\.codex\attachments\422328c1-0c54-4734-90c9-653dc95340cd\pasted-text-1.txt. Read this file before continuing.

The referenced file was read before implementation. It authorizes the
following work (summary of the referenced instruction, not a fabricated
transcript):

- Work only in a new isolated worktree at
  `C:\Users\natan\OneDrive\Dokumenty\ChatGPT\Blackhole-v2-ask-fix`, on
  branch `product/v2-ask-fix`, based exactly on
  `33185aaefac93882e898e9d47e7d9405daab7b84`.
- Do not modify the provider-fix source worktree or other protected worktrees,
  do not access V1 oracle/scoring worktrees, and do not reopen the repaired
  provider adapter except for a regression directly caused by Ask integration.
- Audit the complete Product V2 Ask path and fix the general routing failure:
  arbitrary ordinary questions should retrieve relevant Product V2 memory,
  retain justified deterministic fast paths, use bounded semantic planning or
  synthesis when needed, support Polish and English, distinguish no-data and
  no-match states, preserve provenance/current-vs-superseded/uncertainty/
  retractions/corrections, and never route on accidental short substrings or
  phrase-specific wording.
- Add at least 25 diverse multilingual Ask-routing regressions plus mocked
  HTTP end-to-end coverage; run the specified Product V2, UI, acceptance,
  historical, evaluator, compile, syntax, qualification, and structural
  checks without weakening existing tests.
- A fresh temporary `BLACKHOLE_HOME` live smoke is authorized, with at most 4
  captures and the 6 specified Ask questions. Do not change implementation
  between live questions or tune to individual wording. Record outcomes
  honestly, including partial failure if a structural issue remains.
- Create the coding trajectory files, update the Product V2 dogfood document,
  commit only to `product/v2-ask-fix`, and return the required Product V2 Ask
  Routing Gate with base/final SHAs, root cause, architecture, test/evaluation
  counts, live outcomes, provider/retry counts, limitations, and explicit
  boundary confirmations.

The complete source instruction remains available at the referenced attachment
path above; this record intentionally distinguishes the faithful initiating
message from this summary.
