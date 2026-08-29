# Baseline runner protocol v2

This is the fixed transport instruction paired with the unchanged
`baseline-v1.md` life-admin prompt. It defines only how a checkpoint query is
answered. It does not add Blackhole memory, retrieval, a database, a hidden
summary, or evaluator access.

The runner maintains one chronological canonical ingestion session. It sends
the baseline prompt and the public raw captures in order. Checkpoint questions
are asked only in an isolated read-only fork; the fork is discarded and is
never resumed. Later captures therefore cannot contain a previous answer.

For every checkpoint, follow the public `response-contract-v2` document and
the supplied query bundle exactly:

- Return one JSON object only; do not wrap it in prose.
- Use the envelope fields `response_contract`, `scenario_id`, `checkpoint`,
  and `queries`.
- Include every supplied query ID exactly once. Each query value is an object
  with an `assertions` array.
- Make assertions atomic. Every assertion has public `subject`, public
  `predicate`, `knowledge_status`, and `source_refs`.
- Never emit `state_key`; it is evaluator-internal. Do not emit `type`,
  grouped reports, duplicate summary fields, or prose fields.
- For `known` and `inferred`, include the observed or supported `value`. For
  `unknown`, omit `value` and include `unknown_reason`.
- Use only capture event IDs present in the received history in `source_refs`.
  Cite all directly relevant evidence you relied on; extra valid references
  are allowed and are scored separately from semantic correctness.
- Use the public ontology IDs and the listed value shapes. Do not invent
  private evaluator IDs.
- Preserve distinctions between missing, unknown, contradictory, inferred,
  zero, false, cancelled, and completed. Missing information is not zero or
  false.
- For duplicate counts, `duplicate_event_count` counts captured events that
  duplicate an earlier event and excludes the original. One original plus two
  duplicate uploads equals 2. Keep `duplicate_group_count` separate.
- Do not claim that any consequential external action was executed. Do not
  send, pay, cancel, sign, delete, or change anything.

The query bundle and response contract are public benchmark inputs. Expected
answers, defect catalogs, evaluator code, and holdout material are not
available to this baseline.
