# Runtime trajectory summary: Experiment 001 full final projector replay

This is the final non-official 200-event milestone replay. It reused the four
recorded public semantic extraction outputs from `experiment-001-full-v1` and
applied the v2 rebuildable state projection plus final deterministic projector,
including duplicate-plus-meaningful connected-group counting. It made no new
provider calls; the semantic provider cost belongs to the recorded v1 run.

Against the unchanged public Gate A evaluator and `response-contract-v2`, the
result scored LQA-0M `0.7492295899` with checkpoint scores
`0.7962962963 / 0.7523071836 / 0.7064078283 / 0.7419070513`, DSCR `72`, and
`TP=279, FP=69, FN=96`. Schema validity, safety, and source integrity all
passed. The candidate, result, projected state, prompts, and raw replayed
extractions are retained. No expected output or holdout material was exposed
to the application runtime.
