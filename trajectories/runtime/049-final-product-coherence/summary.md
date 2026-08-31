# Final product coherence live runtime trajectory

## Input received

A fresh synthetic Home was used for the final live run. The synthetic document
was an invoice with reference `REF-123`, issuer `Acme Hosting`, service annual
hosting, amount `19.00 EUR`, due date `2026-09-01`, and an attachment named
`synthetic-invoice-ref-123.txt`. Follow-up synthetic captures created an
ordinary support-call task, recorded payment of `REF-123`, and recorded two
ordinary water-consumption observations. No private invoice or user content
was used.

## State before execution

The Home was empty. Product V2 readiness discovered the already-installed
authenticated `codex-cli 0.151.0` as READY. Blackhole did not read, copy,
export, or persist provider credentials.

## Agent instructions and boundary

The runtime used the final versioned Product V2 extraction/Ask contract:
deterministic code owns retrieval, temporal normalization, arithmetic,
occurrence aggregation, lifecycle validation, provenance, and bounded evidence;
the provider may interpret/render only supplied structured candidates and must
select evidence IDs. Provider failure or unsafe output must be visible as a
degraded fallback. The run was capped at six captures and eight Ask requests;
no tuning or retry loop was added.

## Tools invoked and observable results

- Capture 1: synthetic invoice document; HTTP return `39ms`, saved immediately,
  then processed successfully. Memory exposed `Invoice · REF-123`, Acme
  Hosting, annual hosting, `19.00 EUR`, and the due date with attachment
  provenance.
- Capture 2: ordinary support-call task; HTTP return `8ms`, saved and
  processed successfully. Attention showed the document deadline and the
  support-call task with useful service context.
- Capture 3: `I paid invoice REF-123 to Acme Hosting.`; HTTP return `36ms`,
  saved and processed successfully. The explicit payment lifecycle key closed
  only the matching document Attention. The unrelated support-call task stayed
  open. Active Attention count was one; terminal lifecycle count was two.
- Four Ask requests were made in total, within the eight-request cap. The
  provider-backed answers included who issued the invoice, what was done today,
  and whether `REF-123` was paid. The post-restart/API measured Ask latencies
  were `11,706ms` and `11,514ms`; `provider_used=true` and
  `degraded_fallback=false` were observed on the final factual answers.
- The ordinary support-call task was then completed through the visible Done
  action. Active Attention became empty and the two completed lifecycle entries
  remained inspectable in Memory/history after page reload and rebuild/restart.
- Browser review at `390×844` showed the centered processing notice, useful
  document Memory, and natural Ask responses. At `1280×900`, the remaining Done
  button center was `554.859375px` and the footer center was `554.359375px`
  (within `0.5px`); computed button `margin-top` was `0px`. The mobile action
  row and button centers both measured `187.5px`.

## Retries or verification

Two earlier fresh live attempts were discarded: the first clicked Done before
the payment check, and the second was restarted to validate the ordered
payment-first flow after observing a less useful Attention title. The final
run above was the bounded evidence run. It completed all five captures with no
provider failure or processing retry. The temporary server was stopped after
the final state was captured.

## Resulting state and final user-visible outcome

The final state had five saved synthetic captures, one attachment, document
identity for `Invoice · REF-123`, no active Attention after explicit completion,
and two terminal Attention history entries. The final Ask and Memory surfaces
were human-readable, evidence-backed, and restart-persistent. No internal
evidence IDs, raw transport syntax, or private data were exposed in the
user-visible answers.

## Evidence

Machine-readable summary: `eval/results/product-v2-final-coherence.json`.
The full deterministic acceptance result is
`eval/results/product-v2-integrated-acceptance.json`. This runtime trajectory
contains no holdout answers, private data, provider tokens, or benchmark oracle
material.
