import io
import json
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ops_logging import ProductOpsLogger, sanitize_human_text
from app.product_v2 import ProductRuntime, _human_fact_summary
from app.runtime_config import DEFAULT_BATCH_SIZE, DEFAULT_REASONING_EFFORT, SUPPORTED_REASONING_EFFORTS
from app.tests.test_product_v2 import ProductFakeProvider


REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO_ROOT / "app" / "web"


class DelayedRetryProvider:
    def __init__(self) -> None:
        self.fail_once = True
        self.calls: list[list[str]] = []
        self.time_contexts: list[dict[str, Any]] = []

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, contract
        self.calls.append([str(event["event_id"]) for event in events])
        self.time_contexts.append(time_context)
        # Model a slow provider without making the deterministic test costly.
        time.sleep(0.02)
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("temporary provider outage")
        event_id = str(events[0]["event_id"])
        return {
            "facts": [],
            "attention": [
                {
                    "event_id": event_id,
                    "kind": "task",
                    "title": "Pick up the kids",
                    "status": "open",
                    "relative_minutes": 10,
                }
            ],
        }


class RelevanceProvider:
    """Fixture provider that records the bounded linking context."""

    def __init__(self) -> None:
        self.prior_memories: list[dict[str, Any]] = []

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del time_context, contract
        self.prior_memories.append(prior_memory)
        facts: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", ""))
            lowered = text.casefold()
            if "basement keys" in lowered and "drawer" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "Basement keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "the drawer",
                        "operation": "correction",
                    }
                )
            elif "basement keys" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "Basement keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "Mum's place",
                    }
                )
            else:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "Noise " + event_id,
                        "concept": "detail",
                        "knowledge_status": "known",
                        "value": "ordinary value",
                    }
                )
        return {"facts": facts}


class ProductV2FinalDogfoodTests(unittest.TestCase):
    def _run_ui_hooks(self, expression: str) -> Any:
        node = shutil.which("node")
        if not node:
            self.skipTest("node is required for executable UI contract coverage")
        script = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(process.argv[1], "utf8");
const window = {
  __BLACKHOLE_V2_TEST__: true,
  location: { search: "", hash: "" },
  navigator: {},
  matchMedia: () => ({ matches: false }),
  localStorage: { getItem: () => null, setItem: () => {} },
};
const sandbox = { window, URLSearchParams, Intl, Date, console, setTimeout, clearTimeout };
vm.runInNewContext(source, sandbox, { filename: process.argv[1] });
const api = window.BlackholeV2;
const result = %s;
process.stdout.write(JSON.stringify(result));
""" % expression
        completed = subprocess.run(
            [node, "-e", script, str(WEB_ROOT / "app.js")],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(completed.stdout, completed.stderr)
        return json.loads(completed.stdout)

    def test_capture_time_survives_processing_delay_retry_and_rebuild(self) -> None:
        provider = DelayedRetryProvider()
        processing_now = datetime(2026, 8, 30, 20, 52, 41, tzinfo=timezone.utc)
        captured_at = "2026-08-30T22:52:41+02:00"
        expected_due = "2026-08-30T23:02:41+02:00"
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: processing_now,
            ) as runtime:
                runtime.capture(
                    "Odbieram dzieci za 10 minut.",
                    captured_at=captured_at,
                    timezone_name="Europe/Berlin",
                    event_id="final-time-1",
                )
                failed = runtime.process_pending()
                self.assertEqual(failed["failed"], 1)
                self.assertEqual(runtime.processing_status("final-time-1")["status"], "failed")

                self.assertEqual(runtime.retry_failed("final-time-1")["retried"], 1)
                processed = runtime.process_pending()
                self.assertEqual(processed["processed"], 1)
                self.assertEqual(provider.calls, [["final-time-1"], ["final-time-1"]])
                self.assertEqual(provider.time_contexts[0]["captures"][0]["captured_at"], captured_at)

                attention = runtime.snapshot()["attention"]
                self.assertEqual(len(attention), 1)
                self.assertEqual(attention[0]["due_at"], expected_due)

                runtime.store.rebuild()
                rebuilt = runtime.snapshot()["attention"]
                self.assertEqual(rebuilt[0]["due_at"], expected_due)

    def test_extraction_context_keeps_old_matching_entity_beyond_recency_limit(self) -> None:
        provider = RelevanceProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc),
            ) as runtime:
                runtime.capture("The basement keys are at Mum's place.", event_id="context-target")
                for index in range(45):
                    runtime.capture(f"Unrelated structured detail {index}.", event_id=f"context-noise-{index:02d}")
                self.assertEqual(runtime.process_pending()["processed"], 46)

                runtime.capture(
                    "Correction: the basement keys are now in the drawer.",
                    event_id="context-correction",
                )
                self.assertEqual(runtime.process_pending()["processed"], 1)
                prior = provider.prior_memories[-1]
                prior_facts = [
                    item
                    for item in prior.get("current_facts", [])
                    if isinstance(item, dict)
                ]
                self.assertTrue(
                    any(
                        item.get("entity_key") == "basement_keys"
                        and item.get("value") == "Mum's place"
                        for item in prior_facts
                    )
                )
                snapshot = runtime.snapshot()
                current = [
                    item
                    for item in snapshot["current_facts"]
                    if item.get("entity_key") == "basement_keys"
                ]
                self.assertEqual(len(current), 1)
                self.assertEqual(current[0]["value"], "the drawer")
                self.assertTrue(
                    any(
                        item.get("entity_key") == "basement_keys"
                        and item.get("value") == "Mum's place"
                        for item in snapshot["fact_history"]
                    )
                )
                runtime.store.rebuild()
                rebuilt = runtime.snapshot()
                self.assertEqual(
                    next(item for item in rebuilt["current_facts"] if item.get("entity_key") == "basement_keys")["value"],
                    "the drawer",
                )

    def test_product_runtime_uses_conservative_product_defaults(self) -> None:
        self.assertEqual(DEFAULT_REASONING_EFFORT, "low")
        self.assertEqual(DEFAULT_BATCH_SIZE, 2)
        self.assertIn("low", SUPPORTED_REASONING_EFFORTS)

    def test_attention_and_disclosure_contract_is_human_and_stable(self) -> None:
        result = self._run_ui_hooks(r"""(() => {
  const makeRoot = (id, open = false) => {
    const details = {
      dataset: { disclosureId: id },
      open,
      listeners: {},
      addEventListener(name, callback) { this.listeners[name] = callback; },
      emit(name) { if (this.listeners[name]) this.listeners[name](); },
    };
    return { details, querySelectorAll() { return [details]; } };
  };
  const controller = api.createDisclosureState();
  const first = makeRoot("attention:pickup");
  controller.bind(first);
  first.details.open = true;
  first.details.emit("toggle");
  const refreshed = makeRoot("attention:pickup");
  controller.restore(refreshed);
  return {
    overdue: api.formatAttentionTime({ due_at: "2026-08-30T09:50:00Z" }, new Date("2026-08-30T10:00:00Z")),
    upcoming: api.formatAttentionTime({ due_at: "2026-08-30T10:10:00Z" }, new Date("2026-08-30T10:00:00Z")),
    restored: refreshed.details.open,
    stored: controller.has("attention:pickup"),
  };
})()""")
        self.assertTrue(result["overdue"].startswith("Overdue by "))
        self.assertIn("in 10 min", result["upcoming"])
        self.assertTrue(result["restored"])
        self.assertTrue(result["stored"])

    def test_ui_presentation_is_defensive_and_keeps_history_contextual(self) -> None:
        result = self._run_ui_hooks(r"""(() => {
  const memory = api.normalizeMemory({
    current_facts: [{ entity_key: "basement_keys", entity_label: "Basement keys", concept: "location", value: "Mum's place", source_refs: ["event-current"] }],
    fact_history: [
      { entity_key: "basement_keys", entity_label: "Basement keys", concept: "location", value: "the old flat", semantic_relation: "correction", source_refs: ["event-old"] },
      { entity_key: "orphan", concept: "location", value: "should be omitted", source_refs: ["event-orphan"] },
    ],
  });
  const answer = api.normalizeAnswer({
    mode: "retrieval",
    summary: "The keys are at Mum's place.",
    groups: [{ title: "Related memories", items: [{ text: "Basement keys", evidence: ["event-current"] }] }],
  });
  const attention = api.normalizeAttention([{ title: "Pick up the kids", due_at: "2026-08-30T10:10:00Z", status: "open" }]);
  return {
    objectFallback: api.displayText("[object Object]", ""),
    undefinedFallback: api.displayText(undefined, ""),
    nullFallback: api.displayText(null, ""),
    memoryGroups: memory.length,
    memoryFacts: memory[0] ? memory[0].facts.map((fact) => fact.text) : [],
    answerGroups: answer.groups.length,
    relatedItems: answer.groups[0] ? answer.groups[0].items.length : 0,
    attentionTitle: attention[0] ? attention[0].title : "",
    attentionWhen: attention[0] ? attention[0].when : "",
    examplesBefore: api.shouldShowAskExamples([]),
    examplesAfter: api.shouldShowAskExamples([{ role: "user", text: "Where are the keys?" }]),
  };
})()""")
        self.assertEqual(result["objectFallback"], "")
        self.assertEqual(result["undefinedFallback"], "")
        self.assertEqual(result["nullFallback"], "")
        self.assertEqual(result["memoryGroups"], 1)
        self.assertEqual(
            [item.casefold() for item in result["memoryFacts"]],
            ["at mum's place", "changed from at the old flat"],
        )
        self.assertEqual(result["answerGroups"], 1)
        self.assertEqual(result["relatedItems"], 1)
        self.assertEqual(result["attentionTitle"], "Pick up the kids")
        self.assertTrue(result["attentionWhen"])
        self.assertTrue(result["examplesBefore"])
        self.assertFalse(result["examplesAfter"])

    def test_raw_language_is_preserved_and_deterministic_ask_stays_provider_free(self) -> None:
        provider = ProductFakeProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc),
            ) as runtime:
                runtime.capture("Klucze do piwnicy są u mamy.", event_id="language-1")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                before = time.monotonic()
                answer = runtime.ask("Gdzie są klucze do piwnicy?")
                elapsed = time.monotonic() - before
                raw = runtime.store.raw_event("language-1")
                self.assertEqual(raw["payload"]["text"], "Klucze do piwnicy są u mamy.")
                self.assertEqual(provider.answer_calls, 0)
                self.assertLess(elapsed, 0.2)
                self.assertEqual(answer["provider_used"], False)
                self.assertEqual(answer["answer_language"], "pl")

    def test_human_operational_logs_are_readable_bounded_and_private(self) -> None:
        stream = io.StringIO()
        logger = ProductOpsLogger(stream=stream)
        logger.human("Learned · Basement keys → Mum's place")
        logger.human("token=secret-token-value\n" + ("x" * 500))
        logger.human("WiFi password → hunter2")
        rendered = stream.getvalue()
        self.assertIn("Learned · Basement keys", rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertNotIn("secret-token-value", rendered)
        self.assertNotIn("hunter2", rendered)
        self.assertLessEqual(max(len(line) for line in rendered.splitlines()), 240)
        self.assertLessEqual(len(sanitize_human_text("x" * 1000)), 220)

        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "WiFi", "concept": "password", "value": "hunter2"}
            ),
            "Private value captured",
        )
        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "Door", "concept": "access_code", "value": "492817"}
            ),
            "Private value captured",
        )
        self.assertEqual(
            _human_fact_summary(
                {
                    "entity_label": "Home network",
                    "concept": "setting",
                    "value": "configured",
                    "metadata": {"private_token": "never log this"},
                }
            ),
            "Private value captured",
        )
        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "Settings", "concept": "detail", "value": "password is hunter2"}
            ),
            "Private value captured",
        )
        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "Inbox", "concept": "note_from_user", "value": "raw capture"}
            ),
            "Inbox → captured",
        )
        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "Payload", "concept": "observation", "value": {"raw": "private"}}
            ),
            "Payload → captured",
        )
        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "Blob", "concept": "observation", "value": "A" * 128}
            ),
            "Blob → captured",
        )
        self.assertEqual(
            _human_fact_summary(
                {
                    "entity_label": "Echo",
                    "concept": "detail",
                    "value": "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen",
                }
            ),
            "Echo → captured value",
        )
        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "Basement keys", "concept": "location", "value": "Mum's place"}
            ),
            "Basement keys → Mum's place",
        )
        self.assertEqual(
            _human_fact_summary(
                {"entity_label": "PocketWave", "concept": "cost", "value": {"amount": 9, "currency": "EUR"}}
            ),
            "PocketWave → 9 EUR",
        )

        provider = ProductFakeProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc),
                ops_logger=logger,
            ) as runtime:
                runtime.capture("PRIVATE_RAW_CAPTURE_VALUE", event_id="logs-1")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                runtime.ask("Where are the basement keys?")
            rendered = stream.getvalue()
        self.assertIn("Saved capture · text", rendered)
        self.assertIn("Understanding", rendered)
        self.assertIn("Learned", rendered)
        self.assertIn("Ready ·", rendered)
        self.assertIn("Ask · deterministic retrieval", rendered)
        self.assertNotIn("PRIVATE_RAW_CAPTURE_VALUE", rendered)


if __name__ == "__main__":
    unittest.main()
