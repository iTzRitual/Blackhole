# Hackathon video shot list

| Time | Shot | Action / onscreen evidence | Spoken point |
| --- | --- | --- | --- |
| 0:00–0:25 | Title + Capture | Show Blackhole title and empty universal input | Zero-organization inbox; capture before classification |
| 0:25–0:45 | Capture input | Enter a short reminder | One low-friction input |
| 0:45–1:05 | Saved state | Click Save capture; pause on `Saved.` and recent raw capture | Immutable raw capture, no synchronous model call |
| 1:05–1:25 | Attention | Open Attention; show deadline and approval-required cards | Surface only review-worthy items |
| 1:25–1:50 | Memory | Open Memory; scroll through subscription current/history and task state | Longitudinal state and provenance |
| 1:50–2:00 | Uncertainty | Pause on missing period and `Unknown · Not stated` | Missing is not zero or a guess |
| 2:00–2:30 | Ask | Run “What changed recently?” then “What information is incomplete?” | Query-scoped deterministic projections |
| 2:30–2:50 | Architecture | Show architecture flow in `docs/ARCHITECTURE.md` | Raw → observations → rebuildable state → attention |
| 2:50–3:15 | Safety/runtime | Show approval card and provider boundary docs | No consequential action; CLI owns auth |
| 3:15–3:45 | Results | Show `eval/results/final-comparison-v1.json` | Baseline, advanced replay, delta, checkpoints |
| 3:45–4:00 | Caveat | Show relation-detail deferral in changelog/decision log | Honest measured limitation |
| 4:00–4:30 | Reproduction | Show README commands and trajectory directories | Judges can run the local demo and inspect evidence |

## Capture checklist

- Keep the browser at a readable desktop or narrow/mobile viewport.
- Use only the committed synthetic demo seed; do not show personal data.
- Show the `Saved.` feedback, not an invented semantic classification response.
- Show at least one `known` fact, one historical value, one `unknown`, one
  duplicate/change relation, and one approval boundary.
- Do not open or display holdout material.
- Do not claim that the benchmark score is a production or holdout result.
- Do not claim monotonic degradation; show the recorded checkpoint values as
  they are.
