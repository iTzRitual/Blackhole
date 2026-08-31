import io
import json
import shutil
import subprocess
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.codex_discovery import MISSING, ProviderStatus, discover_codex, discover_product_v2
from app.host import HostRuntime
from app.ops_logging import ProductOpsLogger, sanitize_human_text
from app.product_v2 import (
    ProductCodexProvider,
    ProductProviderUnavailableError,
    ProductRuntime,
    _display_fact_value,
    _human_fact_summary,
)
from app.runtime_config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_REASONING_EFFORT,
    PRODUCT_V2_DEFAULT_BATCH_SIZE,
    PRODUCT_V2_DEFAULT_REASONING_EFFORT,
    PRODUCT_V2_SUPPORTED_REASONING_EFFORTS,
    RuntimeConfig,
    SUPPORTED_REASONING_EFFORTS,
)
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
        self.assertEqual(DEFAULT_REASONING_EFFORT, "high")
        self.assertEqual(DEFAULT_BATCH_SIZE, 10)
        self.assertNotIn("low", SUPPORTED_REASONING_EFFORTS)
        self.assertEqual(PRODUCT_V2_DEFAULT_REASONING_EFFORT, "low")
        self.assertEqual(PRODUCT_V2_DEFAULT_BATCH_SIZE, 2)
        self.assertIn("low", PRODUCT_V2_SUPPORTED_REASONING_EFFORTS)
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(directory, start_worker=False) as runtime:
                self.assertEqual(runtime.reasoning_effort, PRODUCT_V2_DEFAULT_REASONING_EFFORT)
                self.assertEqual(runtime.batch_size, PRODUCT_V2_DEFAULT_BATCH_SIZE)
            provider = ProductCodexProvider(home=directory)
            self.assertEqual(provider.reasoning_effort, PRODUCT_V2_DEFAULT_REASONING_EFFORT)
        with patch("app.codex_discovery.shutil.which", return_value=None):
            self.assertFalse(
                discover_codex(configured_model="gpt-5.6-luna", configured_reasoning="low").configured_runtime
            )
            self.assertTrue(
                discover_product_v2(
                    configured_model="gpt-5.6-luna", configured_reasoning="low"
                ).configured_runtime
            )

    def test_fresh_home_persists_independent_legacy_and_product_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = RuntimeConfig.load_or_create(directory)
            persisted = json.loads(config.config_path.read_text(encoding="utf-8"))

            self.assertEqual(config.reasoning_effort, "high")
            self.assertEqual(config.batch_size, 10)
            self.assertEqual(config.product_reasoning_effort, "low")
            self.assertEqual(config.product_batch_size, 2)
            self.assertEqual(persisted["reasoning_effort"], "high")
            self.assertEqual(persisted["batch_size"], 10)
            self.assertEqual(persisted["product_reasoning_effort"], "low")
            self.assertEqual(persisted["product_batch_size"], 2)
            self.assertEqual(persisted["config_version"], "blackhole-runtime-config-v1")

    def test_existing_home_without_product_fields_keeps_legacy_values_and_gets_product_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "config_version": "blackhole-runtime-config-v1",
                        "provider": "codex",
                        "model": "gpt-5.6-luna",
                        "reasoning_effort": "high",
                        "timeout_seconds": 900,
                        "batch_size": 10,
                        "database": "blackhole.db",
                    }
                ),
                encoding="utf-8",
            )

            config = RuntimeConfig.load_or_create(home)
            self.assertEqual(config.reasoning_effort, "high")
            self.assertEqual(config.batch_size, 10)
            self.assertEqual(config.product_reasoning_effort, "low")
            self.assertEqual(config.product_batch_size, 2)

            # A later normal save upgrades the persisted shape without changing
            # the old fields or the config-version contract.
            config.save()
            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["reasoning_effort"], "high")
            self.assertEqual(persisted["batch_size"], 10)
            self.assertEqual(persisted["product_reasoning_effort"], "low")
            self.assertEqual(persisted["product_batch_size"], 2)

    def test_host_legacy_and_product_runtime_boundaries_are_independent(self) -> None:
        calls: list[dict[str, str]] = []

        def discovery(**kwargs: str) -> ProviderStatus:
            calls.append(kwargs)
            return ProviderStatus(
                status=MISSING,
                installed=False,
                authenticated=None,
                version=None,
                auth_check_available=False,
                configured_runtime=True,
                ready=False,
                error_code="binary_not_found",
            )

        with tempfile.TemporaryDirectory() as directory:
            with HostRuntime.open(
                directory,
                provider=None,
                discovery_fn=discovery,
                auto_start_product_worker=False,
            ) as host:
                self.assertEqual(host.engine.batch_size, 10)
                host.status(refresh_provider=True)
                product = host.product_runtime
                self.assertEqual(product.reasoning_effort, "low")
                self.assertEqual(product.batch_size, 2)

                with self.assertRaises(ProductProviderUnavailableError):
                    product._provider()

            self.assertEqual([call["configured_reasoning"] for call in calls], ["high", "low"])

    def test_product_process_uses_product_config_fields(self) -> None:
        class RuntimeSpy:
            kwargs: dict[str, Any] = {}

            def __init__(self, _home: str | Path, **kwargs: Any) -> None:
                RuntimeSpy.kwargs = kwargs
                self.store = type("Store", (), {"path": Path(_home) / "blackhole-v2.db"})()

            def __enter__(self) -> "RuntimeSpy":
                return self

            def __exit__(self, *_exc: object) -> None:
                return None

            def processing_status(self) -> dict[str, Any]:
                return {"counts": {"pending": 0, "processing": 0, "processed": 0, "failed": 0}}

        with tempfile.TemporaryDirectory() as directory:
            config = RuntimeConfig.defaults(directory)
            config.reasoning_effort = "max"
            config.batch_size = 7
            config.product_reasoning_effort = "medium"
            config.product_batch_size = 4
            config.save()

            from app import product_process

            with redirect_stdout(io.StringIO()), patch.object(product_process, "ProductRuntime", RuntimeSpy):
                self.assertEqual(product_process.main(["--home", directory, "status"]), 0)

            self.assertEqual(RuntimeSpy.kwargs["reasoning_effort"], "medium")
            self.assertEqual(RuntimeSpy.kwargs["batch_size"], 4)

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
            ["mum's place", "changed from the old flat"],
        )
        self.assertEqual(result["answerGroups"], 1)
        self.assertEqual(result["relatedItems"], 1)
        self.assertEqual(result["attentionTitle"], "Pick up the kids")
        self.assertTrue(result["attentionWhen"])
        self.assertTrue(result["examplesBefore"])
        self.assertFalse(result["examplesAfter"])

    def test_ui_attention_memory_and_ask_outputs_stay_human_and_current_first(self) -> None:
        result = self._run_ui_hooks(r"""(() => {
  const now = new Date("2026-08-31T03:12:00Z");
  const attention = api.normalizeAttention([
    {
      fingerprint: "open-reminder",
      title: "Pay the water bill",
      status: "open",
      due_at: "2026-08-31T03:20:00Z",
      captured_at: "2026-08-31T03:04:00Z",
      source_refs: ["capture:private"],
      details: { note: "A useful note", source_event_id: "event:private", payload: { raw: true } },
    },
    { fingerprint: "completed-reminder", title: "Already done", status: "completed" },
    { fingerprint: "cancelled-reminder", title: "Cancelled", status: "cancelled" },
    { fingerprint: "superseded-reminder", title: "Replaced", status: "superseded" },
  ]);
  const memory = api.normalizeMemory({
    current_facts: [
      { entity_key: "water", entity_label: "Water", concept: "drink", summary: "3 glasses today", captured_at: "2026-08-31T03:04:00Z" },
      { entity_key: "keys", entity_label: "Basement keys", concept: "location", knowledge_status: "unknown", unknown_reason: "conflicting", captured_at: "2026-08-31T02:00:00Z" },
    ],
    fact_history: [
      { entity_key: "water", entity_label: "Water", concept: "drink", summary: "1 glass yesterday", semantic_relation: "correction", captured_at: "2026-08-30T03:04:00Z" },
    ],
  });
  const answer = api.normalizeAnswer({
    mode: "retrieval",
    summary: "The recorded amount is below.",
    groups: [{ title: "Water", items: [{ text: { amount: 3, unit: "glasses", source_event_id: "private" }, source_refs: ["capture:private"] }] }],
  });
  return {
    attentionIds: attention.map((item) => item.id),
    attentionDetail: attention[0] ? attention[0].detail : "",
    attentionEvidence: attention[0] ? attention[0].evidence : "",
    captured: api.formatCapturedTime("2026-08-31T03:04:00Z", now),
    soon: api.attentionUrgency({ due_at: "2026-08-31T03:20:00Z" }, now),
    overdue: api.attentionUrgency({ due_at: "2026-08-31T03:00:00Z" }, now),
    overdueText: api.formatAttentionTime({ due_at: "2026-08-31T03:00:00Z" }, now),
    memoryFacts: memory.map((group) => ({ name: group.name, facts: group.facts.map((fact) => ({ text: fact.text, history: fact.isHistory })) })),
    unknownText: memory.find((group) => group.name === "Basement keys")?.facts[0]?.text || "",
    answerText: answer.groups[0]?.items[0]?.text || "",
    answerEvidence: answer.groups[0]?.items[0]?.evidence || "",
  };
})()""")
        self.assertEqual(result["attentionIds"], ["open-reminder"])
        self.assertIn("A useful note", result["attentionDetail"])
        self.assertNotIn("event:private", result["attentionDetail"])
        self.assertNotIn("{", result["attentionDetail"])
        self.assertIn("Captured", result["attentionEvidence"])
        self.assertEqual(result["captured"], "Captured 8 min ago")
        self.assertEqual(result["soon"], "soon")
        self.assertEqual(result["overdue"], "overdue")
        self.assertTrue(result["overdueText"].startswith("Overdue by "))
        self.assertEqual(result["memoryFacts"][0]["facts"][0]["history"], False)
        self.assertEqual(result["memoryFacts"][0]["facts"][1]["history"], True)
        self.assertEqual(result["unknownText"], "Needs clarification")
        self.assertEqual(result["answerText"], "3 glasses")
        self.assertNotIn("private", result["answerText"])
        self.assertNotIn("{", result["answerText"])
        self.assertEqual(result["answerEvidence"], "Captured source")

    def test_ui_keeps_generic_occurrences_secondary_and_drops_duplicate_history_rows(self) -> None:
        result = self._run_ui_hooks(r"""(() => {
  const memory = api.normalizeMemory({
    current_facts: [
      { entity_key: "x", entity_label: "X", concept: "consumed", claim_type: "consumed", value: { amount: 2, unit: "units" }, captured_at: "2026-08-30T03:04:00Z" },
      { entity_key: "x", entity_label: "X", concept: "consumed", claim_type: "consumed", value: { amount: 1, unit: "units" }, captured_at: "2026-08-31T03:04:00Z" },
      { entity_key: "x", entity_label: "X", concept: "preferred_drink", claim_type: "preference", value: "tea" },
      { entity_key: "charger", entity_label: "Spare charger", concept: "location", knowledge_status: "unknown", unknown_reason: "ambiguous" },
    ],
    fact_history: [
      { entity_key: "x", entity_label: "X", concept: "consumed", claim_type: "consumed", value: { amount: 2, unit: "units" }, semantic_relation: "set", captured_at: "2026-08-30T03:04:00Z" },
    ],
  });
  const answer = api.normalizeAnswer({
    answer: {
      mode: "ambiguous",
      answer: "The question needs a little more detail.",
      clarification: { prompt: "Can you clarify which memory you mean?" },
    },
  });
  const x = memory.find((group) => group.name === "X");
  const charger = memory.find((group) => group.name === "Spare charger");
  return {
    occurrenceCount: x ? x.facts.filter((fact) => fact.occurrence).length : 0,
    historyCount: x ? x.facts.filter((fact) => fact.isHistory).length : 0,
    stateIsOccurrence: x ? x.facts.some((fact) => fact.text.toLowerCase().includes("tea") && fact.occurrence) : true,
    summary: x ? x.summary : "",
    unknownText: charger ? charger.facts[0].text : "",
    clarificationPrompt: answer.clarificationPrompt,
  };
})()""")
        self.assertEqual(result["occurrenceCount"], 2)
        self.assertEqual(result["historyCount"], 0)
        self.assertFalse(result["stateIsOccurrence"])
        self.assertIn("3 units total across 2 captured occurrences", result["summary"])
        self.assertEqual(result["unknownText"], "Needs clarification")
        self.assertEqual(result["clarificationPrompt"], "Can you clarify which memory you mean?")

    def test_ask_primary_markup_has_supporting_disclosure_without_footer_copy(self) -> None:
        result = self._run_ui_hooks(r"""(() => {
  const normalized = api.normalizeAnswer({
    answer: {
      mode: "retrieval",
      answer: "The basement keys are in your backpack.",
      items: [{
        entity_label: "Basement keys",
        concept: "location",
        knowledge_status: "known",
        value: "your backpack",
        source_refs: ["capture:keys"],
      }],
    },
  });
  return api.renderAssistantMarkup({ answer: normalized }, 0);
})()""")
        self.assertIn("The basement keys are in your backpack.", result)
        self.assertIn("Supporting memories · 1", result)
        self.assertNotIn("Based on what you’ve captured so far.", result)

    def test_attribution_is_available_to_provenance_but_not_primary_fact_copy(self) -> None:
        item = {
            "value": {"amount": 2},
            "metadata": {"attribution": "self"},
            "attribution": "self",
            "knowledge_status": "known",
        }
        self.assertEqual(_display_fact_value(item), "2")
        self.assertIn("reported by self", _display_fact_value(item, include_attribution=True))

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
