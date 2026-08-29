# Process evidence

This directory contains small, curated process records that help a judge or
maintainer understand repository decisions and handoffs. It is separate from
the coding and runtime trajectory protocol.

Coding trajectories under `trajectories/coding/` document meaningful agent
work. Runtime trajectories under `trajectories/runtime/` document
representative executions. Neither directory may contain a fabricated
transcript; a transcript is included only when the originating environment
provided an authentic export.

Advisory conversations, browser ChatGPT planning, and pasted human guidance
may inform a task, but they are not coding-agent transcripts. When no
authentic export exists, the repository records a faithful prompt summary and
an evidence-based summary instead of reconstructing dialogue or hidden
reasoning.

Curated decision logs or sanitized planning records may be added here when
they clarify a durable process choice. They must not contain credentials,
private user data, holdout expected outputs, evaluator-owned ground truth, or
provider raw output that the implementation agent was not authorized to keep.
