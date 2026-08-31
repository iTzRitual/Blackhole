from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ask_planner import plan_ask
from app.product_v2 import ProductRuntime
from app.web_app import create_server


def fixed_clock() -> datetime:
    return datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)


class AskCorpusProvider:
    """Deterministic semantic seam for a broad Product V2 Ask corpus."""

    def __init__(self) -> None:
        self.answer_calls = 0
        self.answer_contexts: list[dict[str, Any]] = []

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
        previous_pocketwave = next(
            (
                str(event["event_id"])
                for event in events
                if "pocketwave" in str(event.get("payload", {}).get("text", "")).casefold()
                and "9" in str(event.get("payload", {}).get("text", ""))
            ),
            None,
        )
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", ""))
            lowered = text.casefold()
            if "pocketwave" in lowered and "11" in lowered:
                fact: dict[str, Any] = {
                    "event_id": event_id,
                    "entity": "PocketWave",
                    "concept": "recurring_cost",
                    "knowledge_status": "known",
                    "value": {"amount": "11", "currency": "EUR", "billing_period": "month"},
                    "operation": "correction",
                }
                if previous_pocketwave:
                    fact["supersedes_event_id"] = previous_pocketwave
                facts.append(fact)
            elif "pocketwave" in lowered and "9" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "PocketWave",
                        "concept": "recurring_cost",
                        "knowledge_status": "known",
                        "value": {"amount": "9", "currency": "EUR", "billing_period": "month"},
                    }
                )
            elif "basement" in lowered or "piwnic" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "basement keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "mother's place",
                    }
                )
            elif "garage keys" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "garage keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "the drawer",
                    }
                )
            elif "kuba" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "Kuba",
                        "concept": "preference",
                        "knowledge_status": "known",
                        "value": "green pasta from Lidl",
                    }
                )
            elif "car" in lowered or "samoch" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "car",
                        "concept": "condition",
                        "knowledge_status": "known",
                        "value": "knocking at the front left",
                    }
                )
            elif "boiler" in lowered or "piec" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "boiler",
                        "concept": "condition",
                        "knowledge_status": "known",
                        "value": "needs inspection",
                    }
                )
            elif "rental contract" in lowered or "document najmu" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "rental contract",
                        "concept": "meaning",
                        "knowledge_status": "known",
                        "value": "the landlord must give 30 days notice",
                    }
                )
            elif "owner" in lowered and "not stated" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "house",
                        "concept": "owner",
                        "knowledge_status": "unknown",
                        "unknown_reason": "not_stated",
                    }
                )
            elif "parking permit" in lowered:
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "deadline",
                        "title": "Parking permit renewal",
                        "status": "open",
                        "due_at": "2026-09-12T09:00:00+02:00",
                    }
                )
            elif "children" in lowered or "dzieci" in lowered:
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "task",
                        "title": "Pick up the children",
                        "status": "open",
                        "relative_minutes": 10,
                    }
                )
        return {"facts": facts, "attention": attention}

    def answer(self, *, question: str, context: dict[str, Any], time_context: dict[str, Any]) -> dict[str, Any]:
        del time_context
        self.answer_calls += 1
        self.answer_contexts.append(json.loads(json.dumps(context, ensure_ascii=False)))
        lowered = question.casefold()
        derived = context.get("derived", {}) if isinstance(context.get("derived"), dict) else {}
        candidates = [
            item
            for collection in (
                "facts",
                "history",
                "relationships",
                "attention",
                "attention_history",
            )
            for item in context.get(collection, [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]

        def pick(predicate: Any, *, limit: int = 10) -> list[dict[str, Any]]:
            return [item for item in candidates if predicate(item)][:limit]

        if "parking" in lowered:
            selected = pick(lambda item: "parking" in str(item.get("title", "")).casefold())
            answer = "The parking permit renewal is due on September 12."
        elif any(token in lowered for token in ("attention", "urgent", "today", "soon", "week", "coming", "upcoming", "niedługo", "pilne", "zrobić")):
            attention = [item for item in context.get("attention", []) if isinstance(item, dict)]
            if "week" in lowered or "coming" in lowered or "upcoming" in lowered:
                selected = [item for item in attention if "parking" not in str(item.get("title", "")).casefold()][:1]
            else:
                selected = attention[:1] if attention else []
            if selected:
                answer = "; ".join(str(item.get("title") or "open item") for item in selected) + "."
            else:
                return {"answer": "No matching actionable item is recorded.", "evidence_ids": []}
        elif "changed" in lowered or "recently" in lowered or "zmieni" in lowered or "popraw" in lowered or "previous value" in lowered:
            if "wi-fi" in lowered or "wifi" in lowered:
                selected = pick(lambda item: item.get("entity_key") == "home_wifi")
                answer = "The Wi-Fi password changed from BlueRiver7 to GreenRiver9."
            elif "previous value" in lowered:
                selected = pick(lambda item: item.get("entity_key") == "pocketwave")
                answer = "The previous PocketWave price was 9 EUR; the current price is 11 EUR."
            else:
                selected = pick(lambda item: item.get("entity_key") == "pocketwave")
                answer = "PocketWave changed from 9 EUR to 11 EUR."
        elif any(token in lowered for token in ("pay", "płac", "price", "cena", "cost", "koszt")):
            if any(token in lowered for token in ("history", "previous", "poprzed", "changed", "zmieni")):
                selected = pick(lambda item: item.get("entity_key") == "pocketwave")
            else:
                selected = pick(
                    lambda item: item.get("entity_key") == "pocketwave"
                    and item.get("current", item.get("metadata", {}).get("semantic_state") == "current")
                ) or pick(lambda item: item.get("entity_key") == "pocketwave", limit=1)
            if "previous" in lowered or "poprzed" in lowered:
                selected = [item for item in selected if item.get("value", {}).get("amount") == "9"] or selected[:1]
                answer = "The previous PocketWave price was 9 EUR."
            elif "changed" in lowered or "zmieni" in lowered or "history" in lowered:
                answer = "PocketWave changed from 9 EUR to 11 EUR."
            else:
                answer = "PocketWave costs 11 EUR per month."
        elif "last mention" in lowered or "ostat" in lowered:
            selected = pick(lambda item: item.get("entity_key") == "pocketwave", limit=1)
            answer = "PocketWave was last mentioned in the latest recorded note."
        elif "semantic" in lowered or "oznacza" in lowered:
            selected = pick(lambda item: item.get("entity_key") == "rental_contract", limit=1)
            answer = "A semantic explanation of the rental contract is available in the recorded note."
        elif "owner" in lowered or "owns" in lowered or "właśc" in lowered:
            selected = pick(lambda item: item.get("entity_key") == "house", limit=1)
            answer = "The owner of the house is unknown; it was not stated."
        elif "what do i know" in lowered or "co wiem" in lowered:
            selected = [item for item in context.get("facts", []) if isinstance(item, dict)]
            labels = []
            for item in selected:
                value = item.get("value")
                rendered = value if isinstance(value, str) else str(value or "")
                labels.append(f"{item.get('entity_label')}: {rendered}".strip(": "))
            answer = "; ".join(labels) + "."
        else:
            selected = pick(lambda item: True, limit=1)
            if not selected:
                return {"answer": "No matching recorded memory.", "evidence_ids": []}
            item = selected[0]
            value = item.get("value")
            rendered = value if isinstance(value, str) else str(value or "")
            answer = f"{item.get('entity_label')}: {rendered}."

        evidence_ids = [item["evidence_id"] for item in selected if isinstance(item.get("evidence_id"), str)]
        return {"answer": answer, "evidence_ids": evidence_ids}


class TopicSwitchProvider:
    """Deterministic fixture for the final live topic/follow-up path."""

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
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", ""))
            lowered = text.casefold()
            captured_at = str(event.get("captured_at") or "2026-08-30T08:00:00+00:00")
            if "basement keys" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "basement keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "backpack",
                    }
                )
            elif "consumed" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "X",
                        "concept": "consumed",
                        "knowledge_status": "known",
                        "value": {"amount": 2 if "yesterday" in lowered else 1, "unit": "unit"},
                        "claim_type": "consumed",
                        "temporal": {"normalized": captured_at, "precision": "day"},
                    }
                )
        return {"facts": facts}

    def answer(self, *, question: str, context: dict[str, Any], time_context: dict[str, Any]) -> dict[str, Any]:
        del time_context
        self.answer_calls += 1
        self.answer_contexts.append(json.loads(json.dumps(context, ensure_ascii=False)))
        lowered = question.casefold()
        if "basement" in lowered:
            selected = [
                item
                for item in context.get("facts", [])
                if isinstance(item, dict) and item.get("entity_key") == "basement_keys"
            ][:1]
            return {
                "answer": "The basement keys are in the backpack.",
                "evidence_ids": [item["evidence_id"] for item in selected],
            }
        derived = context.get("derived", {}) if isinstance(context.get("derived"), dict) else {}
        totals = derived.get("occurrence_totals", [])
        ids = list(totals[0].get("supporting_evidence_ids") or []) if totals else []
        return {"answer": "The preceding total is 3 units.", "evidence_ids": ids}


CAPTURES = (
    ("ask-keys", "Klucze do piwnicy są u mamy."),
    ("ask-garage", "The garage keys are in the drawer."),
    ("ask-kuba", "Kuba lubi zielony makaron z Lidla."),
    ("ask-car", "Samochód zaczął stukać z przodu po lewej."),
    ("ask-boiler", "The boiler needs inspection."),
    ("ask-document", "The rental contract says the landlord must give 30 days notice."),
    ("ask-house", "The owner of the house was not stated."),
    ("ask-pocket-old", "PocketWave costs 9 EUR monthly."),
    ("ask-pocket-new", "PocketWave now costs 11 EUR monthly."),
    ("ask-parking", "The parking permit is due on September 12."),
    ("ask-children", "Odbieram dzieci za 10 minut."),
)


# This is intentionally broader than the original live wording.  Each row
# exercises an ordinary natural-language request over the same open-world
# memory and records what must be included or excluded from the answer.
ASK_ROUTING_CASES = (
    {"category": "open_world", "question": "Gdzie są klucze do piwnicy?", "mode": "retrieval", "include": ("mother's place",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "Where are the basement keys?", "mode": "retrieval", "include": ("mother's place",), "exclude": ("Pick up",)},
    {"category": "unknown", "question": "Where are the keys?", "mode": "ambiguous", "include": ("ambiguous", "garage keys", "basement keys"), "exclude": ()},
    {"category": "open_world", "question": "Co wiem o Kubie?", "mode": "retrieval", "include": ("green pasta",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "What do I know about Kuba?", "mode": "retrieval", "include": ("green pasta",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "Co mówiłem o samochodzie?", "mode": "retrieval", "include": ("knocking",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "What did I say about the car?", "mode": "retrieval", "include": ("knocking",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "What do I need to know about the boiler?", "mode": "retrieval", "include": ("needs inspection",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "What did I do about the car?", "mode": "retrieval", "include": ("knocking",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "What does the rental document say?", "mode": "retrieval", "include": ("30 days",), "exclude": ("Pick up",)},
    {"category": "open_world", "question": "Co oznacza dokument najmu?", "mode": "semantic", "include": ("semantic explanation",), "exclude": ("Pick up",)},
    {"category": "attention", "question": "What do I need to do today?", "mode": "attention", "include": ("Pick up",), "exclude": ("basement keys",)},
    {"category": "attention", "question": "Co mam niedługo do zrobienia?", "mode": "attention", "include": ("Pick up",), "exclude": ("basement keys",)},
    {"category": "attention", "question": "Do I have anything urgent?", "mode": "attention", "include": ("Pick up",), "exclude": ("basement keys",)},
    {"category": "attention", "question": "What needs my attention?", "mode": "attention", "include": ("Pick up",), "exclude": ("basement keys",)},
    {"category": "attention", "question": "What is coming up this week?", "mode": "attention", "include": ("Pick up",), "exclude": ("Parking permit",)},
    {"category": "attention", "question": "When is the parking permit due?", "mode": "attention", "include": ("Parking permit",), "exclude": ("Pick up",)},
    {"category": "attention", "question": "Co jest pilne?", "mode": "attention", "include": ("Pick up",), "exclude": ("basement keys",)},
    {"category": "attention", "question": "What do I need to do about the boiler?", "mode": "attention", "include": ("needs inspection",), "exclude": ("Pick up",)},
    {"category": "money", "question": "What am I paying for?", "mode": "costs", "include": ("11 EUR",), "exclude": ("Pick up",)},
    {"category": "money", "question": "Za co płacę co miesiąc?", "mode": "costs", "include": ("11 EUR",), "exclude": ("Pick up",)},
    {"category": "money", "question": "How much do I pay for PocketWave?", "mode": "costs", "include": ("11 EUR",), "exclude": ("Pick up",)},
    {"category": "money", "question": "What is the current PocketWave price?", "mode": "costs", "include": ("11 EUR",), "exclude": ("Pick up",)},
    {"category": "money", "question": "What is the PocketWave price history?", "mode": "costs", "include": ("9 EUR", "11 EUR"), "exclude": ("Pick up",)},
    {"category": "changes", "question": "What changed recently?", "mode": "changes", "include": ("9 EUR", "11 EUR"), "exclude": ("Pick up",)},
    {"category": "changes", "question": "What changed about PocketWave?", "mode": "changes", "include": ("9 EUR", "11 EUR"), "exclude": ("Pick up",)},
    {"category": "changes", "question": "What was the previous PocketWave price?", "mode": "changes", "include": ("9 EUR",), "exclude": ("Pick up",)},
    {"category": "changes", "question": "Co zostało poprawione w PocketWave?", "mode": "changes", "include": ("9 EUR", "11 EUR"), "exclude": ("Pick up",)},
    {"category": "changes", "question": "What was the previous value?", "mode": "changes", "include": ("9 EUR", "11 EUR"), "exclude": ("Pick up",)},
    {"category": "history", "question": "When did I last mention PocketWave?", "mode": "last_mention", "include": ("PocketWave", "ask-pocket-new"), "exclude": ("Pick up",)},
    {"category": "unknown", "question": "Who owns the house?", "mode": "retrieval", "include": ("unknown", "not_stated"), "exclude": ("Pick up",)},
    {"category": "unknown", "question": "Where is the spare charger?", "mode": "no_match", "include": (), "exclude": ("Pick up",)},
    {"category": "unknown", "question": "What do I know about my dentist?", "mode": "no_match", "include": (), "exclude": ("Pick up",)},
    {"category": "unknown", "question": "What do I know about Jan?", "mode": "no_match", "include": (), "exclude": ("Pick up",)},
    {"category": "collision", "question": "Do the keys belong to the basement?", "mode": "retrieval", "include": ("mother's place",), "exclude": ("Pick up",)},
    {"category": "collision", "question": "Where do I keep the spare charger?", "mode": "no_match", "include": (), "exclude": ("Pick up",)},
    {"category": "broad", "question": "What do I know?", "mode": "retrieval", "include": ("basement keys", "Kuba", "car"), "exclude": ()},
)


class ProductV2AskRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.provider = AskCorpusProvider()
        self.runtime = ProductRuntime(
            self.directory.name,
            provider=self.provider,
            start_worker=False,
            clock=fixed_clock,
        )
        for event_id, text in CAPTURES:
            self.runtime.capture(text, event_id=event_id)
        result = self.runtime.process_pending()
        self.assertEqual(result["processed"], len(CAPTURES))

    def tearDown(self) -> None:
        self.runtime.close()
        self.directory.cleanup()

    def test_corpus_has_at_least_25_diverse_questions_and_routes_without_cross_talk(self) -> None:
        self.assertGreaterEqual(len(ASK_ROUTING_CASES), 25)
        for case in ASK_ROUTING_CASES:
            with self.subTest(category=case["category"], question=case["question"]):
                result = self.runtime.ask(case["question"])
                self.assertEqual(result["mode"], case["mode"])
                rendered = json.dumps(result, ensure_ascii=False).casefold()
                for needle in case["include"]:
                    self.assertIn(needle.casefold(), rendered)
                for needle in case["exclude"]:
                    self.assertNotIn(needle.casefold(), rendered)

    def test_planner_uses_semantic_whole_terms_not_the_polish_preposition_do(self) -> None:
        self.assertEqual(plan_ask("Gdzie są klucze do piwnicy?").intent, "generic")
        self.assertEqual(plan_ask("What do I need to do today?").intent, "attention")
        self.assertEqual(plan_ask("What do I need to know about the boiler?").intent, "generic")
        self.assertEqual(plan_ask("What changed about PocketWave?").intent, "changes")
        self.assertEqual(plan_ask("Co się ostatnio zmieniło?").intent, "changes")
        self.assertEqual(plan_ask("Co mam niedługo do zrobienia?").intent, "attention")
        self.assertEqual(plan_ask("Co mam zrobić w ciągu najbliższych 15 minut?").intent, "attention")
        self.assertEqual(plan_ask("When did I last mention PocketWave?").intent, "last_mention")
        self.assertFalse(plan_ask("What do I know?").referential)
        self.assertFalse(plan_ask("What do I need to know?").referential)
        self.assertTrue(plan_ask("What does that mean?").referential)

    def test_unmapped_money_modifier_uses_semantic_synthesis(self) -> None:
        plan = plan_ask("Ile kosztuje PocketWave i czy cena się zmieniała?")
        self.assertEqual(plan.intent, "costs")
        self.assertTrue(plan.semantic_fallback)
        self.assertTrue(plan.requires_synthesis)
        result = self.runtime.ask("Ile kosztuje PocketWave i czy cena się zmieniała?")
        self.assertEqual(result["mode"], "semantic")
        self.assertTrue(result["provider_used"])
        self.assertIn("ask-pocket-old", result["source_refs"])
        self.assertIn("ask-pocket-new", result["source_refs"])

    def test_provider_context_contains_only_retrieved_memory(self) -> None:
        result = self.runtime.ask("Explain what I know about the boiler.")
        self.assertEqual(result["mode"], "semantic")
        self.assertEqual(self.provider.answer_calls, 1)
        context = self.provider.answer_contexts[-1]
        self.assertEqual([item["entity_label"] for item in context["facts"]], ["boiler"])
        self.assertEqual(context["attention"], [])
        self.assertNotIn("ask-children", result["source_refs"])
        self.assertIn("ask-boiler", result["source_refs"])

    def test_current_topic_wins_and_referential_followup_uses_latest_topic_only(self) -> None:
        provider = TopicSwitchProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=fixed_clock,
            ) as runtime:
                runtime.capture(
                    "The basement keys are in the backpack.",
                    event_id="topic-keys",
                    captured_at="2026-08-30T08:00:00+00:00",
                )
                runtime.capture(
                    "I consumed 2 units yesterday.",
                    event_id="topic-consumed-yesterday",
                    captured_at="2026-08-29T08:00:00+00:00",
                )
                runtime.capture(
                    "I consumed 1 unit today.",
                    event_id="topic-consumed-today",
                    captured_at="2026-08-30T08:00:00+00:00",
                )
                self.assertEqual(runtime.process_pending()["processed"], 3)

                location = runtime.ask("Where are the basement keys?")
                self.assertEqual(location["mode"], "retrieval")
                self.assertEqual(location["answer"], "The basement keys are in the backpack.")
                self.assertNotIn("relevant memory", location["answer"].casefold())
                self.assertNotRegex(location["answer"], r"\d{4}-\d{2}-\d{2}T")

                aggregate = runtime.ask("How many X did I consume in total?")
                self.assertEqual(aggregate["mode"], "occurrence_totals")
                self.assertIn("3 unit", aggregate["answer"])
                self.assertNotIn("basement", json.dumps(aggregate, ensure_ascii=False).casefold())
                self.assertEqual(
                    set(aggregate["source_refs"]),
                    {"topic-consumed-yesterday", "topic-consumed-today"},
                )

                before_followup = runtime.snapshot()
                thread = [
                    {"role": "user", "text": location["question"]},
                    {"role": "assistant", "text": location["answer"]},
                    {"role": "user", "text": aggregate["question"]},
                    {"role": "assistant", "text": aggregate["answer"]},
                ]
                followup = runtime.ask("What does that mean?", thread_context=thread)
                self.assertTrue(followup["provider_used"])
                self.assertEqual(followup["answer"], "The preceding total is 3 units.")
                self.assertEqual(
                    set(followup["source_refs"]),
                    {"topic-consumed-yesterday", "topic-consumed-today"},
                )
                context = provider.answer_contexts[-1]
                self.assertEqual(
                    {item["entity_label"] for item in context["facts"]},
                    {"X"},
                )
                self.assertTrue(all("evidence_id" not in item for item in context["thread"]))

                new_thread = runtime.ask("How many X did I consume in total?")
                self.assertEqual(new_thread["answer"], aggregate["answer"])
                self.assertTrue(new_thread["provider_used"])
                after_followup = runtime.snapshot()
                for section in ("current_facts", "fact_history", "relationships", "attention"):
                    self.assertEqual(after_followup[section], before_followup[section])

    def test_no_data_no_match_unknown_and_retraction_are_distinct(self) -> None:
        empty_directory = tempfile.TemporaryDirectory()
        empty_provider = AskCorpusProvider()
        empty_runtime = ProductRuntime(
            empty_directory.name,
            provider=empty_provider,
            start_worker=False,
            clock=fixed_clock,
        )
        try:
            no_data = empty_runtime.ask("Where are the keys?")
            self.assertEqual(no_data["mode"], "no_data")
            self.assertEqual(no_data["status"], "no_data")
            self.assertFalse(no_data["provider_used"])
        finally:
            empty_runtime.close()
            empty_directory.cleanup()

        no_match = self.runtime.ask("Where is the spare charger?")
        self.assertEqual(no_match["mode"], "no_match")
        self.assertEqual(no_match["status"], "no_match")
        self.assertFalse(no_match["provider_used"])
        ambiguous = self.runtime.ask("Where are the keys?")
        self.assertEqual(ambiguous["mode"], "ambiguous")
        self.assertIn("Where are the keys?", ambiguous["clarification"]["prompt"])
        unknown = self.runtime.ask("Who owns the house?")
        self.assertEqual(unknown["mode"], "retrieval")
        self.assertIn("unknown", unknown["answer"].casefold())
        self.runtime.retract("ask-keys")
        retracted = self.runtime.ask("Where are the basement keys?")
        self.assertEqual(retracted["mode"], "no_match")
        self.assertNotIn("ask-keys", retracted["source_refs"])


class ProductV2AskRoutingHttpTests(unittest.TestCase):
    @staticmethod
    def request(
        base_url: str,
        path: str,
        *,
        method: str = "GET",
        body: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.loads(error.read().decode("utf-8"))

    def test_mocked_http_ask_answers_open_world_memory_and_attention(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = AskCorpusProvider()
            server = create_server("127.0.0.1", 0, home=Path(directory), provider=provider)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                for event_id, text in CAPTURES:
                    status, saved = self.request(
                        base_url,
                        "/api/v2/capture",
                        method="POST",
                        body={"event_id": event_id, "text": text},
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(saved["saved"])
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    _status, processing = self.request(base_url, "/api/v2/processing")
                    counts = processing["processing"]["counts"]
                    if int(counts["processed"]) == len(CAPTURES) and not counts["pending"] and not counts["processing"]:
                        break
                    time.sleep(0.02)
                self.assertEqual(int(counts["processed"]), len(CAPTURES))

                checks = (
                    ("Gdzie są klucze do piwnicy?", "mother's place", "Pick up"),
                    ("Co wiem o Kubie?", "green pasta", "Pick up"),
                    ("Co mówiłem o samochodzie?", "knocking", "Pick up"),
                    ("Co mam niedługo do zrobienia?", "Pick up", "basement keys"),
                    ("Where are the basement keys?", "mother's place", "Pick up"),
                    ("What do I know about Kuba?", "green pasta", "Pick up"),
                )
                for question, expected, unrelated in checks:
                    status, payload = self.request(
                        base_url,
                        "/api/v2/ask",
                        method="POST",
                        body={"question": question},
                    )
                    self.assertEqual(status, 200)
                    answer = payload["answer"]
                    self.assertIn(expected.casefold(), json.dumps(answer, ensure_ascii=False).casefold())
                    self.assertNotIn(unrelated.casefold(), json.dumps(answer, ensure_ascii=False).casefold())
                self.assertEqual(provider.answer_calls, 6)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
