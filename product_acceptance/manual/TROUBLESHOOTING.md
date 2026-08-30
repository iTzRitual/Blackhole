# Technical troubleshooting appendix

This appendix is for the person running the local test, not for the main
dogfood participant. It contains no credential-handling instructions.

## Safe startup checks

From the repository root, the current local product can be checked with:

```text
python -m app.host init
python -m app.host doctor
python -m app.web_app --host 127.0.0.1 --port 8080
```

`doctor` should be treated as a readiness report, not as proof that semantic
processing succeeded. A missing provider must not prevent raw capture.

## Symptom guide

| Symptom | Safe interpretation | Check |
| --- | --- | --- |
| Capture never says saved | Capture durability problem | Confirm the local Host is running and inspect the response in the browser's visible UI; do not retry blindly if the UI did not tell you whether it saved |
| Capture saves but understanding is delayed | Expected deferred processing | Check processing status; wait or use the normal retry action |
| Provider unavailable | Retryable processing condition | Confirm the raw capture remains present and that retry is available; do not paste tokens or edit credential files |
| Attachment rejected | Transport or format limitation | Confirm filename/MIME and whether the raw attachment was retained or a clear recoverable error was shown |
| Ask has no evidence | Trust failure unless the answer explicitly says there is no supporting source | Re-run the same question after processing; record the exact response |
| Attention shows a future thought as urgent | False-positive attention | Compare with the visible capture and record the item/time shown |
| State disappears after restart | Persistence/recovery failure | Stop the test, preserve the local home for investigation, and record the last visible state |

## Running the deterministic harness

The mock path does not need a Host, Codex, network access, or credentials:

```text
python -m unittest product_acceptance.harness.test_harness -v
python -m product_acceptance.harness.run --adapter mock --report eval/results/product-v2-dogfood-mock.json
```

To probe one explicitly running local Host through HTTP:

```text
python -m product_acceptance.harness.run --adapter http --base-url http://127.0.0.1:8080 --case-id CAP-001
```

The HTTP harness does not reset the target or restart its process. Use a clean
disposable local home and run one focused case when isolation matters. A 404 on
an optional V2 surface becomes `NOT TESTED`; a response that exists but fails a
user-visible expectation becomes `FAIL`.

## Evidence handling

Keep the generated JSON report, case revision, Host revision, and visible error
messages together. Redact private content before sharing. Never include
provider tokens, credential files, raw private documents, or holdout expected
outputs in a report or trajectory.
