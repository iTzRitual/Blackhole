from __future__ import annotations

import copy
import tempfile
import unittest
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from typing import Any

from app.product_v2 import ProductRuntime


def fixed_clock() -> datetime:
    return datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)


def fact(
    event_id: str,
    entity_key: str,
    label: str,
    concept: str,
    value: Any,
    *,
    operation: str = "set",
    supersedes_event_id: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "event_id": event_id,
        "entity": {"key": entity_key, "name": label, "label": label},
        "concept": concept,
        "knowledge_status": "known",
        "value": value,
        "operation": operation,
        "source_refs": [event_id],
    }
    if supersedes_event_id is not None:
        item["supersedes_event_id"] = supersedes_event_id
    return item


def attention(
    event_id: str,
    title: str,
    *,
    due_at: str,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "kind": "deadline",
        "title": title,
        "status": "open",
        "knowledge_status": "known",
        "due_at": due_at,
        "source_refs": [event_id],
    }


def evidence_ids_for_source(
    context: dict[str, Any],
    source_id: str,
    *,
    collections: Iterable[str] = ("facts", "history", "relationships", "attention"),
) -> list[str]:
    selected: list[str] = []
    for collection in collections:
        for item in context.get(collection, []):
            if not isinstance(item, dict) or source_id not in item.get("source_refs", []):
                continue
            evidence_id = item.get("evidence_id")
            if isinstance(evidence_id, str) and evidence_id not in selected:
                selected.append(evidence_id)
    return selected


def all_context_source_refs(context: dict[str, Any]) -> list[str]:
    return sorted(
        {
            source_ref
            for collection in (
                "facts",
                "candidate_facts",
                "history",
                "candidate_history",
                "relationships",
                "candidate_relationships",
                "attention",
                "candidate_attention",
            )
            for item in context.get(collection, [])
            if isinstance(item, dict)
            for source_ref in item.get("source_refs", [])
            if isinstance(source_ref, str)
        }
    )


class ProvenanceFixtureProvider:
    """Deterministic provider seam for candidate/support provenance tests."""

    def __init__(
        self,
        *,
        facts_by_event: dict[str, list[dict[str, Any]]],
        attention_by_event: dict[str, list[dict[str, Any]]] | None = None,
        selector: Callable[[str, dict[str, Any]], list[Any]] | None = None,
        answer_text: str = "The selected memory supports this answer.",
    ) -> None:
        self.facts_by_event = facts_by_event
        self.attention_by_event = attention_by_event or {}
        self.selector = selector
        self.answer_text = answer_text
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
        facts = [
            copy.deepcopy(item)
            for event in events
            for item in self.facts_by_event.get(str(event["event_id"]), [])
        ]
        attention_items = [
            copy.deepcopy(item)
            for event in events
            for item in self.attention_by_event.get(str(event["event_id"]), [])
        ]
        return {"facts": facts, "attention": attention_items}

    def answer(
        self,
        *,
        question: str,
        context: dict[str, Any],
        time_context: dict[str, Any],
    ) -> dict[str, Any]:
        del time_context
        self.answer_calls += 1
        self.answer_contexts.append(copy.deepcopy({"question": question, "context": context}))
        selected = self.selector(question, context) if self.selector else []
        # Deliberately return the legacy broad source list too. The runtime
        # must use evidence_ids, not this candidate-pool-derived field.
        return {
            "answer": self.answer_text,
            "source_refs": all_context_source_refs(context),
            "evidence_ids": selected,
        }


class ProductV2ProvenanceTests(unittest.TestCase):
    @staticmethod
    def runtime(directory: str, provider: ProvenanceFixtureProvider) -> ProductRuntime:
        return ProductRuntime(
            directory,
            provider=provider,
            start_worker=False,
            batch_size=50,
            clock=fixed_clock,
        )

    @staticmethod
    def capture_all(runtime: ProductRuntime, *events: tuple[str, str]) -> None:
        for event_id, text in events:
            runtime.capture(text, event_id=event_id)
        result = runtime.process_pending()
        assert result["processed"] == len(events)

    @staticmethod
    def first_source_evidence(source_id: str, collections: Iterable[str] = ("facts",)) -> Callable[[str, dict[str, Any]], list[Any]]:
        def select(_question: str, context: dict[str, Any]) -> list[Any]:
            return evidence_ids_for_source(context, source_id, collections=collections)[:1]

        return select

    def test_retrieval_candidates_are_not_automatically_answer_evidence(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-keys": [fact("prov-keys", "basement_keys", "basement keys", "location", "mum's place")],
                "prov-charger": [fact("prov-charger", "spare_charger", "spare charger", "location", "blue suitcase")],
                "prov-paul": [fact("prov-paul", "paul", "Paul", "preference", "coffee without sugar")],
            },
            selector=self.first_source_evidence("prov-keys"),
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(
                runtime,
                ("prov-keys", "Klucze do piwnicy są u mamy."),
                ("prov-charger", "The spare charger is in the blue suitcase."),
                ("prov-paul", "Paul aime le café sans sucre."),
            )
            result = runtime.ask("¿Dónde están las llaves del sótano?")

        self.assertEqual(result["mode"], "semantic")
        self.assertEqual(result["source_refs"], ["prov-keys"])
        self.assertNotIn("prov-charger", result["source_refs"])
        self.assertNotIn("prov-paul", result["source_refs"])
        self.assertNotIn("evidence_id", result["items"][0])
        context = provider.answer_contexts[0]["context"]
        self.assertGreaterEqual(len(context["facts"]), 3)

    def test_cross_language_fallback_keeps_bounded_unrelated_candidates_out_of_provenance(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-polish": [fact("prov-polish", "basement_keys", "Klucze do piwnicy", "location", "mum's place")],
                "prov-german": [fact("prov-german", "red_folder", "roter Ordner", "location", "the study")],
                "prov-french": [fact("prov-french", "paul", "Paul", "preference", "coffee without sugar")],
            },
            selector=self.first_source_evidence("prov-polish"),
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(
                runtime,
                ("prov-polish", "Klucze do piwnicy są u mamy."),
                ("prov-german", "Der rote Ordner liegt im Arbeitszimmer."),
                ("prov-french", "Paul aime le café sans sucre."),
            )
            result = runtime.ask("地下室の鍵はどこですか？")

        self.assertEqual(result["source_refs"], ["prov-polish"])
        self.assertNotIn("prov-german", result["source_refs"])
        self.assertNotIn("prov-french", result["source_refs"])
        context = provider.answer_contexts[0]["context"]
        self.assertTrue(context["plan"]["semantic_fallback"])
        self.assertGreaterEqual(len(context["candidate_facts"]), 3)

    def test_mixed_language_ask_does_not_overcite_the_fallback_pool(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-meeting": [fact("prov-meeting", "marek_meeting", "Meeting with Marek", "appointment", "Donnerstag 16:00")],
                "prov-car": [fact("prov-car", "car", "car", "condition", "knocking at the front left")],
                "prov-wifi": [fact("prov-wifi", "home_wifi", "home Wi-Fi", "password", "GreenRiver9")],
            },
            selector=self.first_source_evidence("prov-meeting"),
            answer_text="Spotkanie z Markiem jest w Donnerstag o 16:00.",
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(
                runtime,
                ("prov-meeting", "Meeting z Markiem moved to Donnerstag 16:00."),
                ("prov-car", "Samochód zaczął stukać z przodu po lewej."),
                ("prov-wifi", "Correction: the home Wi-Fi password is GreenRiver9."),
            )
            result = runtime.ask("Kiedy jest rendez-vous z Markiem?")

        self.assertEqual(result["mode"], "semantic")
        self.assertEqual(result["source_refs"], ["prov-meeting"])
        self.assertNotIn("prov-car", result["source_refs"])
        self.assertNotIn("prov-wifi", result["source_refs"])

    def test_source_metadata_evidence_maps_to_its_event_reference(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-source": [fact("prov-source", "meeting", "meeting", "appointment", "Thursday 16:00")],
            },
            selector=lambda _question, context: [
                item["evidence_id"]
                for item in context.get("sources", [])
                if isinstance(item, dict) and item.get("event_id") == "prov-source"
            ],
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(runtime, ("prov-source", "Meeting is Thursday at 16:00."))
            result = runtime.ask("地下室の鍵はどこですか？")

        self.assertEqual(result["mode"], "semantic")
        self.assertEqual(result["source_refs"], ["prov-source"])
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["event_id"], "prov-source")
        self.assertNotIn("evidence_id", result["items"][0])

    def test_current_and_historical_value_keep_both_material_sources(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-price-old": [
                    fact(
                        "prov-price-old",
                        "pocketwave",
                        "PocketWave",
                        "recurring_cost",
                        {"amount": "9", "currency": "EUR", "billing_period": "month"},
                    )
                ],
                "prov-price-new": [
                    fact(
                        "prov-price-new",
                        "pocketwave",
                        "PocketWave",
                        "recurring_cost",
                        {"amount": "11", "currency": "EUR", "billing_period": "month"},
                        operation="correction",
                        supersedes_event_id="prov-price-old",
                    )
                ],
            }
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(runtime, ("prov-price-old", "PocketWave costs 9 EUR monthly."))
            self.capture_all(runtime, ("prov-price-new", "Correction: PocketWave now costs 11 EUR monthly."))
            current = runtime.ask("What is the current PocketWave price?")
            history = runtime.ask("What is the PocketWave price history?")

        self.assertEqual(current["source_refs"], ["prov-price-new"])
        self.assertNotIn("prov-price-old", current["source_refs"])
        self.assertIn("9 EUR", history["answer"])
        self.assertIn("11 EUR", history["answer"])
        self.assertEqual(set(history["source_refs"]), {"prov-price-old", "prov-price-new"})

    def test_contradiction_cites_both_sources_when_answer_reports_uncertainty(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-suitcase-a": [fact("prov-suitcase-a", "blue_suitcase", "blue suitcase", "location", "the hallway")],
                "prov-suitcase-b": [
                    fact(
                        "prov-suitcase-b",
                        "blue_suitcase",
                        "blue suitcase",
                        "location",
                        "the car",
                        operation="contradiction",
                    )
                ],
            }
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(
                runtime,
                ("prov-suitcase-a", "The blue suitcase is in the hallway."),
                ("prov-suitcase-b", "Actually the blue suitcase is in the car."),
            )
            result = runtime.ask("Where is the blue suitcase?")

        self.assertEqual(result["mode"], "retrieval")
        self.assertIn("unknown", result["answer"])
        self.assertEqual(set(result["source_refs"]), {"prov-suitcase-a", "prov-suitcase-b"})

    def test_correction_current_answer_is_narrow_but_history_mentions_prior_source(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-width-old": [fact("prov-width-old", "storage_unit", "storage unit", "width", "2 metres")],
                "prov-width-new": [
                    fact(
                        "prov-width-new",
                        "storage_unit",
                        "storage unit",
                        "width",
                        "2.4 metres",
                        operation="correction",
                        supersedes_event_id="prov-width-old",
                    )
                ],
            }
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(runtime, ("prov-width-old", "The storage unit is 2 metres wide."))
            self.capture_all(runtime, ("prov-width-new", "Correction: the storage unit is 2.4 metres wide, not 2 metres."))
            current = runtime.ask("What is the storage unit width?")
            changes = runtime.ask("What changed about the storage unit's width?")

        self.assertEqual(current["source_refs"], ["prov-width-new"])
        self.assertNotIn("prov-width-old", current["source_refs"])
        self.assertEqual(set(changes["source_refs"]), {"prov-width-old", "prov-width-new"})

    def test_unsupported_question_has_no_irrelevant_citations(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-known": [fact("prov-known", "basement_keys", "basement keys", "location", "mum's place")],
            }
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(runtime, ("prov-known", "The basement keys are at Mum's place."))
            result = runtime.ask("Where is my dentist?")

        self.assertEqual(result["mode"], "no_match")
        self.assertEqual(result["source_refs"], [])
        self.assertEqual(provider.answer_calls, 0)

    def test_attention_deterministic_answer_cites_only_the_attention_source(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-unrelated": [fact("prov-unrelated", "car", "car", "condition", "needs service")],
            },
            attention_by_event={
                "prov-parking": [
                    attention(
                        "prov-parking",
                        "Parking permit renewal",
                        due_at="2026-09-12T09:00:00+02:00",
                    )
                ]
            },
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(
                runtime,
                ("prov-unrelated", "The car needs service."),
                ("prov-parking", "The parking permit is due on September 12."),
            )
            result = runtime.ask("When is the parking permit due?")

        self.assertEqual(result["mode"], "attention")
        self.assertEqual(result["source_refs"], ["prov-parking"])
        self.assertNotIn("prov-unrelated", result["source_refs"])
        self.assertEqual(provider.answer_calls, 0)

    def test_entity_retrieval_cites_only_the_matching_entity(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-paul": [fact("prov-paul", "paul", "Paul", "preference", "coffee without sugar")],
                "prov-kuba": [fact("prov-kuba", "kuba", "Kuba", "preference", "green pasta")],
            }
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(
                runtime,
                ("prov-paul", "Paul aime le café sans sucre."),
                ("prov-kuba", "Kuba lubi zielony makaron."),
            )
            result = runtime.ask("What does Paul like?")

        self.assertEqual(result["mode"], "retrieval")
        self.assertEqual(result["source_refs"], ["prov-paul"])
        self.assertNotIn("prov-kuba", result["source_refs"])

    def test_invalid_provider_evidence_id_is_ignored_without_fabricated_provenance(self) -> None:
        provider = ProvenanceFixtureProvider(
            facts_by_event={
                "prov-real": [fact("prov-real", "basement_keys", "basement keys", "location", "mum's place")],
                "prov-unrelated": [fact("prov-unrelated", "car", "car", "condition", "needs service")],
            },
            selector=lambda _question, _context: ["invented:evidence-id"],
        )
        with tempfile.TemporaryDirectory() as directory, self.runtime(directory, provider) as runtime:
            self.capture_all(
                runtime,
                ("prov-real", "The basement keys are at Mum's place."),
                ("prov-unrelated", "The car needs service."),
            )
            result = runtime.ask("地下室の鍵はどこですか？")

        self.assertEqual(result["mode"], "no_match")
        self.assertEqual(result["status"], "no_match")
        self.assertEqual(result["source_refs"], [])
        self.assertEqual(result["items"], [])
        self.assertNotIn("invented:evidence-id", result["source_refs"])


if __name__ == "__main__":
    unittest.main()
