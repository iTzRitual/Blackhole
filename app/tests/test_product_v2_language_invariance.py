from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Any

from app.ask_planner import detect_question_language, plan_ask, word_tokens
from app.product_v2 import ProductRuntime


def fixed_clock() -> datetime:
    return datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)


def fact(
    event_id: str,
    key: str,
    label: str,
    concept: str,
    value: Any = None,
    *,
    operation: str = "set",
    supersedes_event_id: str | None = None,
    unknown_reason: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "event_id": event_id,
        "entity": {"key": key, "name": label, "label": label},
        "concept": concept,
        "knowledge_status": "unknown" if unknown_reason else "known",
        "operation": operation,
        "source_refs": [event_id],
    }
    if unknown_reason:
        item["unknown_reason"] = unknown_reason
    else:
        item["value"] = value
    if supersedes_event_id:
        item["supersedes_event_id"] = supersedes_event_id
    return item


CAPTURES = (
    ("language-pl-basement", "Klucze do piwnicy są u mamy."),
    ("language-en-charger", "The spare charger is in the blue suitcase."),
    ("language-es-garage", "Las llaves del garaje están con Marta."),
    ("language-de-folder", "Der rote Ordner liegt im Arbeitszimmer."),
    ("language-fr-paul", "Paul aime le café sans sucre."),
    ("language-mixed-meeting", "Meeting z Markiem moved to Donnerstag 16:00."),
    ("language-pl-car", "Samochód zaczął stukać z przodu po lewej."),
    ("language-pl-deadline", "Odbieram dzieci za 10 minut."),
    ("language-en-pocket-old", "PocketWave costs 9 EUR monthly."),
    ("language-en-pocket-new", "PocketWave now costs 11 EUR monthly."),
    ("language-en-wifi-old", "The home Wi-Fi password is BlueRiver7."),
    ("language-en-wifi-new", "Correction: the home Wi-Fi password is GreenRiver9."),
    ("language-de-house", "Der Eigentümer des Hauses wurde nicht genannt."),
    ("language-fr-contract", "Le contrat de location exige un préavis de 30 jours."),
)


SEMANTICS: dict[str, list[dict[str, Any]]] = {
    "language-pl-basement": [fact("language-pl-basement", "basement_keys", "Klucze do piwnicy", "location", "mum's place")],
    "language-en-charger": [fact("language-en-charger", "spare_charger", "spare charger", "location", "blue suitcase")],
    "language-es-garage": [fact("language-es-garage", "garage_keys", "llaves del garaje", "holder", "Marta")],
    "language-de-folder": [fact("language-de-folder", "red_folder", "roter Ordner", "location", "the study")],
    "language-fr-paul": [fact("language-fr-paul", "paul", "Paul", "preference", "coffee without sugar")],
    "language-mixed-meeting": [
        fact("language-mixed-meeting", "marek_meeting", "Meeting with Marek", "appointment", "2026-09-03T16:00:00+02:00"),
    ],
    "language-pl-car": [fact("language-pl-car", "car", "Samochód", "condition", "knocking at the front left")],
    "language-pl-deadline": [
        fact("language-pl-deadline", "children_pickup", "Pick up the children", "task", "Pick up the children"),
    ],
    "language-en-pocket-old": [
        fact("language-en-pocket-old", "pocketwave", "PocketWave", "recurring_cost", {"amount": "9", "currency": "EUR", "billing_period": "month"}),
    ],
    "language-en-pocket-new": [
        fact(
            "language-en-pocket-new",
            "pocketwave",
            "PocketWave",
            "recurring_cost",
            {"amount": "11", "currency": "EUR", "billing_period": "month"},
            operation="correction",
            supersedes_event_id="language-en-pocket-old",
        ),
    ],
    "language-en-wifi-old": [fact("language-en-wifi-old", "home_wifi", "home Wi-Fi", "password", "BlueRiver7")],
    "language-en-wifi-new": [
        fact(
            "language-en-wifi-new",
            "home_wifi",
            "home Wi-Fi",
            "password",
            "GreenRiver9",
            operation="correction",
            supersedes_event_id="language-en-wifi-old",
        ),
    ],
    "language-de-house": [fact("language-de-house", "house", "Haus", "owner", unknown_reason="not_stated")],
    "language-fr-contract": [fact("language-fr-contract", "rental_contract", "contrat de location", "meaning", "landlord must give 30 days notice")],
}


ATTENTION = {
    "language-mixed-meeting": {
        "event_id": "language-mixed-meeting",
        "kind": "appointment",
        "title": "Meeting with Marek",
        "status": "open",
        "starts_at": "2026-09-03T16:00:00+02:00",
    },
    "language-pl-deadline": {
        "event_id": "language-pl-deadline",
        "kind": "task",
        "title": "Pick up the children",
        "status": "open",
        "relative_minutes": 10,
    },
}


def _source_for_key(key: str) -> str:
    for event_id, items in SEMANTICS.items():
        if any(item["entity"]["key"] == key for item in items):
            return event_id
    raise AssertionError(f"unknown semantic key: {key}")


# This is a deterministic provider fixture, not a production language table.
# It models the provider's responsibility to turn arbitrary-language source
# text into a stable semantic key and to synthesize a response from bounded
# structured candidates. The runtime is tested for how it routes and stores
# those results, not for a live model's language quality.
class LanguageMatrixProvider:
    def __init__(self) -> None:
        self.extract_calls = 0
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
        self.extract_calls += 1
        facts = [item for event in events for item in SEMANTICS.get(str(event["event_id"]), [])]
        attention = [ATTENTION[event["event_id"]] for event in events if event["event_id"] in ATTENTION]
        return {"facts": facts, "attention": attention}

    def answer(
        self,
        *,
        question: str,
        context: dict[str, Any],
        time_context: dict[str, Any],
    ) -> dict[str, Any]:
        self.answer_calls += 1
        self.answer_contexts.append(json.loads(json.dumps({"question": question, "context": context, "time_context": time_context}, ensure_ascii=False)))
        target = ANSWERS.get(question)
        if target is None:
            return {"answer": "No supporting evidence matches that question.", "source_refs": []}
        language, key, value = target
        source_overrides = {
            "¿Cuánto pago por la suscripción?": "language-en-pocket-new",
            "Was kostet mein Abo?": "language-en-pocket-new",
            "Combien paie-je pour l'abonnement?": "language-en-pocket-new",
            "Jaka była poprzednia cena PocketWave?": "language-en-pocket-old",
            "¿Cuál era el precio anterior de PocketWave?": "language-en-pocket-old",
            "Qu'est-ce qui a changé pour le mot de passe Wi-Fi?": "language-en-wifi-old",
        }
        source_id = source_overrides.get(question, _source_for_key(key))
        return {"answer": f"[{language}] {value}", "source_refs": [source_id]}


ANSWERS: dict[str, tuple[str, str, str]] = {
    "¿Dónde están las llaves del sótano?": ("ES", "basement_keys", "mum's place"),
    "Wo sind die Kellerschlüssel?": ("DE", "basement_keys", "mum's place"),
    "Où sont les clés de la cave?": ("FR", "basement_keys", "mum's place"),
    "¿Dónde está el cargador de repuesto?": ("ES", "spare_charger", "blue suitcase"),
    "Wo ist das Ersatzladegerät?": ("DE", "spare_charger", "blue suitcase"),
    "Où est le chargeur de secours?": ("FR", "spare_charger", "blue suitcase"),
    "¿Quién tiene las llaves del garaje?": ("ES", "garage_keys", "Marta"),
    "Wer hat die Garagenschlüssel?": ("DE", "garage_keys", "Marta"),
    "Gdzie jest czerwony segregator?": ("PL", "red_folder", "the study"),
    "Wo liegt der rote Ordner?": ("DE", "red_folder", "the study"),
    "Où est le dossier rouge?": ("FR", "red_folder", "the study"),
    "Qu'est-ce que Paul aime?": ("FR", "paul", "coffee without sugar"),
    "Was mag Paul?": ("DE", "paul", "coffee without sugar"),
    "¿Qué le gusta a Paul?": ("ES", "paul", "coffee without sugar"),
    "Kiedy mam spotkanie z Markiem?": ("PL", "marek_meeting", "2026-09-03T16:00:00+02:00"),
    "Wann ist mein Meeting mit Marek?": ("DE", "marek_meeting", "2026-09-03T16:00:00+02:00"),
    "¿Cuándo es mi reunión con Marek?": ("ES", "marek_meeting", "2026-09-03T16:00:00+02:00"),
    "Quand est mon rendez-vous avec Marek?": ("FR", "marek_meeting", "2026-09-03T16:00:00+02:00"),
    "Was ist mit dem Auto passiert?": ("DE", "car", "knocking at the front left"),
    "¿Qué pasó con el coche?": ("ES", "car", "knocking at the front left"),
    "Co się stało z czerwonym segregatorem?": ("PL", "red_folder", "the study"),
    "¿Qué tengo que hacer pronto?": ("ES", "children_pickup", "Pick up the children"),
    "Was muss ich bald erledigen?": ("DE", "children_pickup", "Pick up the children"),
    "Combien paie-je pour l'abonnement?": ("FR", "pocketwave", "11 EUR"),
    "¿Cuánto pago por la suscripción?": ("ES", "pocketwave", "11 EUR"),
    "Was kostet mein Abo?": ("DE", "pocketwave", "11 EUR"),
    "Jaka była poprzednia cena PocketWave?": ("PL", "pocketwave", "9 EUR"),
    "¿Cuál era el precio anterior de PocketWave?": ("ES", "pocketwave", "9 EUR"),
    "Qu'est-ce qui a changé pour le mot de passe Wi-Fi?": ("FR", "home_wifi", "BlueRiver7 → GreenRiver9"),
    "Wer besitzt das Haus?": ("DE", "house", "unknown"),
    "Kto jest właścicielem domu?": ("PL", "house", "unknown"),
    "What does the rental contract mean?": ("EN", "rental_contract", "landlord must give 30 days notice"),
    "Co oznacza umowa najmu?": ("PL", "rental_contract", "landlord must give 30 days notice"),
    "Que signifie le contrat de location?": ("FR", "rental_contract", "landlord must give 30 days notice"),
    "地下室の鍵はどこですか？": ("JA", "basement_keys", "mum's place"),
    "Ключі від підвалу де?": ("UK", "basement_keys", "mum's place"),
}


MATRIX_CASES = (
    # Location and cross-language entity resolution.
    ("same-pl", "Gdzie są klucze do piwnicy?", "mum's place", "language-pl-basement", "pl", False),
    ("pl-to-en", "Where are the basement keys?", "mum's place", "language-pl-basement", "en", False),
    ("pl-to-es", "¿Dónde están las llaves del sótano?", "mum's place", "language-pl-basement", "same_as_question", True),
    ("pl-to-de", "Wo sind die Kellerschlüssel?", "mum's place", "language-pl-basement", "same_as_question", True),
    ("pl-to-fr", "Où sont les clés de la cave?", "mum's place", "language-pl-basement", "same_as_question", True),
    ("uk-to-en", "Where are the basement keys?", "mum's place", "language-pl-basement", "en", False),
    ("same-en-charger", "Where is the spare charger?", "blue suitcase", "language-en-charger", "en", False),
    ("en-to-pl", "Gdzie jest zapasowa ładowarka?", "blue suitcase", "language-en-charger", "pl", False),
    ("en-to-es", "¿Dónde está el cargador de repuesto?", "blue suitcase", "language-en-charger", "same_as_question", True),
    ("en-to-de", "Wo ist das Ersatzladegerät?", "blue suitcase", "language-en-charger", "same_as_question", True),
    ("en-to-fr", "Où est le chargeur de secours?", "blue suitcase", "language-en-charger", "same_as_question", True),
    ("es-to-en", "Who has the garage keys?", "Marta", "language-es-garage", "en", False),
    ("es-to-de", "Wer hat die Garagenschlüssel?", "Marta", "language-es-garage", "same_as_question", True),
    ("de-to-pl", "Gdzie jest czerwony segregator?", "the study", "language-de-folder", "pl", True),
    ("de-to-en", "Where is the red folder?", "the study", "language-de-folder", "en", False),
    ("de-to-fr", "Où est le dossier rouge?", "the study", "language-de-folder", "same_as_question", True),
    # People, preference, observations, and mixed-language input.
    ("fr-to-en-paul", "What does Paul like?", "coffee without sugar", "language-fr-paul", "en", False),
    ("fr-to-pl-paul", "Co lubi Paul?", "coffee without sugar", "language-fr-paul", "pl", False),
    ("fr-to-de-paul", "Was mag Paul?", "coffee without sugar", "language-fr-paul", "same_as_question", True),
    ("fr-to-es-paul", "¿Qué le gusta a Paul?", "coffee without sugar", "language-fr-paul", "same_as_question", True),
    ("mixed-to-pl", "Kiedy mam spotkanie z Markiem?", "2026-09-03T16:00:00+02:00", "language-mixed-meeting", "pl", False),
    ("mixed-to-en", "When is my meeting with Marek?", "2026-09-03T16:00:00+02:00", "language-mixed-meeting", "en", False),
    ("mixed-to-de", "Wann ist mein Meeting mit Marek?", "2026-09-03T16:00:00+02:00", "language-mixed-meeting", "same_as_question", True),
    ("mixed-to-es", "¿Cuándo es mi reunión con Marek?", "2026-09-03T16:00:00+02:00", "language-mixed-meeting", "same_as_question", True),
    ("mixed-to-fr", "Quand est mon rendez-vous avec Marek?", "2026-09-03T16:00:00+02:00", "language-mixed-meeting", "same_as_question", True),
    ("pl-car-to-en", "What did I say about the car?", "knocking at the front left", "language-pl-car", "en", False),
    ("pl-car-same", "Co mówiłem o samochodzie?", "knocking at the front left", "language-pl-car", "pl", False),
    ("pl-car-to-de", "Was ist mit dem Auto passiert?", "knocking at the front left", "language-pl-car", "same_as_question", True),
    ("pl-car-to-es", "¿Qué pasó con el coche?", "knocking at the front left", "language-pl-car", "same_as_question", True),
    # Attention and deterministic values.
    ("attention-pl", "Co mam niedługo do zrobienia?", "Pick up the children", "language-pl-deadline", "pl", False),
    ("attention-en", "What do I need to do soon?", "Pick up the children", "language-pl-deadline", "en", False),
    ("attention-es", "¿Qué tengo que hacer pronto?", "Pick up the children", "language-pl-deadline", "same_as_question", True),
    ("attention-de", "Was muss ich bald erledigen?", "Pick up the children", "language-pl-deadline", "same_as_question", True),
    ("cost-en", "What am I paying for?", "11 EUR", "language-en-pocket-new", "en", False),
    ("cost-pl", "Za co płacę co miesiąc?", "11 EUR", "language-en-pocket-new", "pl", False),
    ("cost-es", "¿Cuánto pago por la suscripción?", "11 EUR", "language-en-pocket-new", "same_as_question", True),
    ("cost-de", "Was kostet mein Abo?", "11 EUR", "language-en-pocket-new", "same_as_question", True),
    ("cost-fr", "Combien paie-je pour l'abonnement?", "11 EUR", "language-en-pocket-new", "same_as_question", True),
    ("current-en", "What is the current PocketWave price?", "11 EUR", "language-en-pocket-new", "en", False),
    ("current-pl", "Jaka jest obecna cena PocketWave?", "11 EUR", "language-en-pocket-new", "pl", False),
    ("previous-en", "What was the previous PocketWave price?", "9 EUR", "language-en-pocket-old", "en", False),
    ("previous-pl", "Jaka była poprzednia cena PocketWave?", "9 EUR", "language-en-pocket-old", "pl", False),
    ("previous-es", "¿Cuál era el precio anterior de PocketWave?", "9 EUR", "language-en-pocket-old", "same_as_question", True),
    # Corrections, uncertainty, and documents.
    ("wifi-en", "What changed about the Wi-Fi password?", "GreenRiver9", "language-en-wifi-new", "en", False),
    ("wifi-pl", "Co zmieniło się w Wi-Fi?", "GreenRiver9", "language-en-wifi-new", "pl", False),
    ("wifi-fr", "Qu'est-ce qui a changé pour le mot de passe Wi-Fi?", "BlueRiver7", "language-en-wifi-old", "same_as_question", True),
    ("owner-en", "Who owns the house?", "unknown", "language-de-house", "en", False),
    ("owner-pl", "Kto jest właścicielem domu?", "unknown", "language-de-house", "pl", True),
    ("owner-de", "Wer besitzt das Haus?", "unknown", "language-de-house", "same_as_question", True),
    ("document-en", "What does the rental contract mean?", "30 days notice", "language-fr-contract", "en", True),
    ("document-pl", "Co oznacza umowa najmu?", "30 days notice", "language-fr-contract", "pl", True),
    ("document-fr", "Que signifie le contrat de location?", "30 days notice", "language-fr-contract", "same_as_question", True),
    # Non-Latin smoke cases and an explicit unsupported question.
    ("japanese", "地下室の鍵はどこですか？", "mum's place", "language-pl-basement", "same_as_question", True),
    ("ukrainian", "Ключі від підвалу де?", "mum's place", "language-pl-basement", "same_as_question", True),
)


class ProductV2LanguageInvarianceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.provider = LanguageMatrixProvider()
        self.runtime = ProductRuntime(
            self.directory.name,
            provider=self.provider,
            start_worker=False,
            batch_size=50,
            clock=fixed_clock,
        )
        for event_id, text in CAPTURES:
            self.runtime.capture(text, event_id=event_id)
        result = self.runtime.process_pending()
        self.assertEqual(result["processed"], len(CAPTURES))

    def tearDown(self) -> None:
        self.runtime.close()
        self.directory.cleanup()

    def test_matrix_has_at_least_40_cases_and_covers_required_languages_and_domains(self) -> None:
        self.assertGreaterEqual(len(MATRIX_CASES), 40)
        questions = [question for _case_id, question, *_rest in MATRIX_CASES]
        self.assertTrue(any(detect_question_language(question) == "pl" for question in questions))
        self.assertTrue(any(detect_question_language(question) == "en" for question in questions))
        self.assertTrue(any(question.startswith("¿") for question in questions))
        self.assertTrue(any(question.startswith("Wo ") for question in questions))
        self.assertTrue(any(question.startswith("Où") or question.startswith("Qu") for question in questions))
        self.assertTrue(any(any("地下" in token or "Ключі" in token for token in word_tokens(question)) for question in questions))
        self.assertTrue(any(case_id.startswith("cost") for case_id, *_rest in MATRIX_CASES))
        self.assertTrue(any(case_id.startswith("wifi") for case_id, *_rest in MATRIX_CASES))
        self.assertTrue(any(case_id.startswith("owner") for case_id, *_rest in MATRIX_CASES))
        self.assertTrue(any(case_id.startswith("document") for case_id, *_rest in MATRIX_CASES))

    def test_cross_language_matrix_retrieves_semantic_target_and_preserves_answer_language(self) -> None:
        for case_id, question, expected_value, source_id, answer_language, provider_expected in MATRIX_CASES:
            with self.subTest(case_id=case_id, question=question):
                before_calls = self.provider.answer_calls
                result = self.runtime.ask(question)
                self.assertNotIn(result["mode"], {"no_match", "no_data"})
                rendered = json.dumps(result, ensure_ascii=False).casefold()
                self.assertIn(expected_value.casefold(), rendered)
                self.assertIn(source_id, result["source_refs"])
                self.assertEqual(result["answer_language"], answer_language)
                self.assertEqual(self.provider.answer_calls, before_calls + int(provider_expected))

    def test_unknown_language_uses_general_fallback_with_bounded_structured_memory(self) -> None:
        result = self.runtime.ask("地下室の鍵はどこですか？")
        self.assertEqual(result["mode"], "semantic")
        self.assertTrue(result["provider_used"])
        self.assertEqual(result["answer_language"], "same_as_question")
        context = self.provider.answer_contexts[-1]["context"]
        self.assertEqual(context["plan"]["intent"], "generic")
        self.assertTrue(context["plan"]["semantic_fallback"])
        self.assertLessEqual(len(context["facts"]), 40)
        self.assertLessEqual(len(context["history"]), 20)
        self.assertLessEqual(len(context["relationships"]), 20)
        self.assertLessEqual(len(context["attention"]), 20)
        self.assertNotIn("payload", json.dumps(context, ensure_ascii=False))
        self.assertNotIn("Klucze do piwnicy są u mamy.", json.dumps(context, ensure_ascii=False))

    def test_unknown_or_mixed_language_never_takes_an_unrelated_fixed_intent(self) -> None:
        for question in (
            "¿Cuánto pago por la suscripción?",
            "Was muss ich bald erledigen?",
            "Qu'est-ce qui a changé pour le mot de passe Wi-Fi?",
            "Meeting z Markiem kiedy?",
            "地下室の鍵はどこですか？",
        ):
            with self.subTest(question=question):
                plan = plan_ask(question)
                self.assertEqual(plan.intent, "generic")
                self.assertTrue(plan.requires_synthesis)
                self.assertTrue(plan.semantic_fallback)

    def test_raw_unicode_capture_is_unchanged_and_semantic_key_is_language_neutral(self) -> None:
        raw = next(event for event in self.runtime.store.raw_events() if event["event_id"] == "language-pl-basement")
        self.assertEqual(raw["payload"]["text"], "Klucze do piwnicy są u mamy.")
        snapshot = self.runtime.snapshot()
        basement = next(item for item in snapshot["current_facts"] if item["entity_key"] == "basement_keys")
        self.assertEqual(basement["entity_label"], "Klucze do piwnicy")
        self.assertEqual(basement["value"], "mum's place")
        self.assertIn("language-pl-basement", basement["source_refs"])

    def test_lexical_gap_in_a_known_fast_path_language_reaches_semantic_fallback(self) -> None:
        plan = plan_ask("Gdzie jest czerwony segregator?")
        self.assertEqual(plan.language, "pl")
        self.assertEqual(plan.intent, "generic")
        self.assertTrue(plan.semantic_fallback)
        result = self.runtime.ask("Gdzie jest czerwony segregator?")
        self.assertEqual(result["mode"], "semantic")
        self.assertTrue(result["provider_used"])
        self.assertIn("the study", result["answer"])

    def test_unsupported_known_language_question_remains_no_match(self) -> None:
        before_calls = self.provider.answer_calls
        result = self.runtime.ask("Where is my dentist?")
        self.assertEqual(result["mode"], "no_match")
        self.assertEqual(result["status"], "no_match")
        self.assertFalse(result["provider_used"])
        self.assertEqual(self.provider.answer_calls, before_calls)


if __name__ == "__main__":
    unittest.main()
