# Runtime trajectory summary

## Run

Bounded live Product V2 validation after the final Ask + Memory + UI hotfix,
using a fresh temporary `BLACKHOLE_HOME`, four synthetic captures, and three
Ask requests. The inputs contain no private data.

## State before

The temporary Home had no captures, memory facts, Attention items, or retries.

## Inputs and provider boundary

The four captures were a museum-pass location, two X consumption occurrences
(2 yesterday and 1 today), and a next-day travel-form reminder. The normal
subscription-first local Codex CLI owned authentication. No provider token was
requested, read, copied, exported, or persisted. The bounded run used 4/4
capture slots and 3/5 Ask slots.

## Observable execution

- All four capture requests returned HTTP 200 and initially reported pending
  processing.
- Processing completed at 4 processed, 0 pending, 0 processing, and 0 failed;
  every event used one attempt, with zero provider failures and zero retries.
- `Where is the museum pass?` returned the current location with only
  `live-location` as its source reference and no provider call.
- `How many X did I consume in total?` returned the deterministic total 3
  across 2 occurrences, referenced only the two X sources, and did not reuse
  the museum-pass topic.
- `What does that mean?` retained the latest X occurrence context, used the
  provider once for semantic interpretation, and returned only the two X
  source references. The prior assistant answer was not treated as evidence.
- Final state contained one current museum-pass location, two known X
  occurrence facts, and one open travel-form Attention item.

## Outcome

The live gate passed its required criteria: topic switching was
current-question-first and the real occurrence memory did not become an
unknown/clarification or false-conflict/history result. The provider’s exact
observed aggregate wording rendered the 2-unit event as `Aug 29` while the
capture text said yesterday; this is recorded as an observed temporal-label
quirk, not hidden or used to alter the frozen benchmark, provider configuration,
or model settings.
