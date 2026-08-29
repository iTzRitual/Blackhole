# Fixed calibration query bundle

This is the non-scored calibration query bundle used at the end of each
50/100/200/400-event prefix. It is deliberately simple and independent from
the final benchmark query set. The same wording and output shape must be used
for every prefix.

The model must return only one JSON object with these top-level keys:

```json
{
  "current": {"s01": {}, "s02": {}, "s03": {}, "s04": {}, "s05": {}, "s06": {}, "s07": {}, "s08": {}, "s09": {}, "s10": {}},
  "previous": {"s01": {}, "s02": {}, "s03": {}, "s04": {}, "s05": {}, "s06": {}, "s07": {}, "s08": {}, "s09": {}, "s10": {}},
  "missing": {"s01": {}, "s02": {}, "s03": {}, "s04": {}, "s05": {}, "s06": {}, "s07": {}, "s08": {}, "s09": {}, "s10": {}},
  "relations": {}
}
```

## Fixed questions

1. What is the current value and knowledge status for each storyline?
2. What was the immediately preceding observed value and knowledge status for
   each storyline?
3. For each storyline, report that its intentionally unobserved secondary
   field is `unknown` with reason `missing`. Do not invent a field name or
   treat absence as zero or false.
4. How many correction, contradiction, ambiguous-link, and duplicate events
   are present?

## Response semantics

- `current` and `previous` contain one entry for each storyline. A known or
  inferred entry has `value` and `knowledge_status`. An unknown entry omits
  `value` and includes `knowledge_status: "unknown"` and an
  `unknown_reason`.
- `missing` contains one entry per storyline with
  `field: "secondary_field"`, `knowledge_status: "unknown"`, and
  `unknown_reason: "missing"`.
- `relations` contains only `correction_count`, `contradiction_count`,
  `ambiguous_link_count`, and `duplicate_count`.
- No prose, Markdown fences, unsupported assertions, or extra keys are
  allowed.

The calibration oracle stores the expected values for this bundle. Because the
bundle is non-scored and calibration-only, its oracle is visible to the
calibration controller but must not be supplied to the baseline process.
