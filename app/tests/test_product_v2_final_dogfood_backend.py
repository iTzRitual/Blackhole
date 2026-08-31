from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from typing import Any

from app.product_v2 import ProductRuntime, _display_fact_value


BASE_NOW = datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)


class DogfoodProvider:
    def __init__(self) -> None:
        self.answer_contexts: list[dict[str, Any]] = []
        self.answer_calls = 0

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, time_context, contract
        facts: list[dict[str, Any]] = []
        attention: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", "")).casefold()
            if "replace" in text:
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "task",
                        "title": "Replace the old reminder",
                        "status": "superseded",
                    }
                )
            elif "dentist" in text:
                attention_item = {
                    "event_id": event_id,
                    "kind": "event",
                    "title": "Book dentist",
                    "status": "open",
                    "details": {"lifecycle_key": "dentist-visit"},
                }
                if "still" not in text:
                    attention_item["relative_minutes"] = 10
                attention.append(attention_item)
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "dentist visit",
                        "concept": "appointment",
                        "knowledge_status": "known",
                        "value": "Book dentist",
                        "temporal": {
                            "normalized": "2026-08-30T10:10:00+02:00",
                            "precision": "minute",
                        },
                    }
                )
            elif "water" in text:
                amount = 1 if "one" in text else 2
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "water",
                        "concept": "drink",
                        "knowledge_status": "known",
                        "value": {"amount": amount, "unit": "glass"},
                        "claim_type": "occurrence",
                    }
                )
        return {"facts": facts, "attention": attention}

    def answer(
        self,
        *,
        question: str,
        context: dict[str, Any],
        time_context: dict[str, Any],
    ) -> dict[str, Any]:
        del question, time_context
        self.answer_calls += 1
        self.answer_contexts.append(context)
        ids = [
            item["evidence_id"]
            for collection in ("facts", "history", "relationships", "attention")
            for item in context.get(collection, [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]
        return {"answer": "Here is the structured memory.", "evidence_ids": ids[:2]}


class ProductV2LastDogfoodBackendTests(unittest.TestCase):
    def test_attention_consolidates_raw_and_fact_projections_and_unions_evidence(self) -> None:
        provider = DogfoodProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: BASE_NOW,
            ) as runtime:
                runtime.capture(
                    "Book the dentist in ten minutes.",
                    event_id="attention-raw-fact-1",
                    captured_at="2026-08-30T10:00:00+02:00",
                    timezone_name="Europe/Berlin",
                )
                runtime.capture(
                    "Dentist visit is still the thing to handle.",
                    event_id="attention-raw-fact-2",
                    captured_at="2026-08-30T10:01:00+02:00",
                    timezone_name="Europe/Berlin",
                )
                self.assertEqual(runtime.process_pending()["processed"], 2)
                state = runtime.snapshot()
                self.assertEqual(len(state["attention"]), 1)
                item = state["attention"][0]
                self.assertEqual(item["due_at"], "2026-08-30T10:10:00+02:00")
                self.assertEqual(set(item["source_refs"]), {"attention-raw-fact-1", "attention-raw-fact-2"})
                self.assertEqual(item["captured_at"], "2026-08-30T10:01:00+02:00")

                runtime.set_attention_status(item["fingerprint"], "completed", note="done")
                completed = runtime.snapshot()
                self.assertEqual(len(completed["attention"]), 1)
                self.assertEqual(completed["attention"][0]["status"], "completed")
                self.assertEqual(completed["counts"]["attention"], 0)

    def test_superseded_attention_is_removed_from_default_projection(self) -> None:
        provider = DogfoodProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(directory, provider=provider, start_worker=False, clock=lambda: BASE_NOW) as runtime:
                runtime.capture("Replace the old reminder.", event_id="superseded-attention")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                state = runtime.snapshot()
                self.assertEqual(state["attention"], [])
                self.assertEqual(state["counts"]["attention"], 0)

    def test_occurrence_claims_coexist_and_totals_are_deterministic(self) -> None:
        provider = DogfoodProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(directory, provider=provider, start_worker=False, clock=lambda: BASE_NOW) as runtime:
                runtime.capture("I drank one water.", event_id="drink-today", captured_at="2026-08-30T07:00:00+00:00")
                runtime.capture("I drank two water.", event_id="drink-yesterday", captured_at="2026-08-29T07:00:00+00:00")
                self.assertEqual(runtime.process_pending()["processed"], 2)
                current = runtime.snapshot()["current_facts"]
                self.assertEqual(len(current), 2)
                self.assertTrue(all(item["metadata"].get("semantic_state") == "occurrence" for item in current))
                answer = runtime.ask("How many did I drink?")
                self.assertEqual(answer["mode"], "occurrence_totals")
                self.assertIn("3 glass", answer["answer"])
                self.assertFalse(answer["provider_used"])

    def test_bounded_ask_thread_resolves_referents_without_becoming_evidence(self) -> None:
        provider = DogfoodProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(directory, provider=provider, start_worker=False, clock=lambda: BASE_NOW) as runtime:
                runtime.capture("I drank one water.", event_id="thread-water")
                runtime.process_pending()
                first = runtime.ask("Explain water")
                self.assertTrue(first["provider_used"])
                prior = [
                    {"role": "user", "text": "What did we discuss?"},
                    {"role": "assistant", "text": "We discussed your water drinking record."},
                ] + [{"role": "user", "text": f"extra {index}"} for index in range(6)]
                second = runtime.ask("What does that mean?", thread_context=prior)
                self.assertTrue(second["provider_used"])
                thread = provider.answer_contexts[-1]["thread"]
                self.assertEqual(len(thread), 8)
                self.assertTrue(all(set(item) == {"role", "text"} for item in thread))
                self.assertFalse(any("evidence_id" in item for item in thread))
                self.assertTrue(any(item["role"] == "assistant" for item in thread))

    def test_structured_unknown_and_values_are_human_without_transport_objects(self) -> None:
        unknown = _display_fact_value(
            {
                "knowledge_status": "unknown",
                "unknown_reason": "conflicting",
                "conflicting_values": [
                    {"value": {"amount": "9", "currency": "EUR"}},
                    {"value": {"amount": "11", "currency": "EUR"}},
                ],
            }
        )
        structured = _display_fact_value(
            {"knowledge_status": "known", "value": {"amount": 3, "unit": "glasses", "source_event_id": "secret"}}
        )
        self.assertIn("Needs clarification", unknown)
        self.assertIn("9 EUR", unknown)
        self.assertIn("11 EUR", unknown)
        self.assertEqual(structured, "3 glasses")
        for value in (unknown, structured):
            self.assertNotIn("source_event_id", value)
            self.assertNotIn("{" , value)
            self.assertNotIn("}", value)


if __name__ == "__main__":
    unittest.main()
