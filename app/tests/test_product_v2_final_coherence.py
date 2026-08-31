from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Any

from app.product_v2 import ProductRuntime, normalize_extraction


BASE_NOW = datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)


class CoherenceProvider:
    """Synthetic semantic seam for the final Product V2 coherence gate."""

    def __init__(self, *, answer_available: bool = True, unsafe_answer: bool = False) -> None:
        self.answer_available = answer_available
        self.unsafe_answer = unsafe_answer
        self.extract_calls = 0
        self.answer_calls = 0
        self.answer_contexts: list[dict[str, Any]] = []

    @staticmethod
    def _document_facts(event_id: str, reference: str) -> list[dict[str, Any]]:
        key = f"invoice:{reference.casefold()}"
        title = f"Invoice · {reference}"
        common = {
            "event_id": event_id,
            "entity": {"key": key, "name": title, "label": title},
            "knowledge_status": "known",
            "document_key": key,
            "document_type": "Invoice",
            "document_reference": reference,
            "document_title": title,
            "lifecycle_key": key,
        }
        return [
            {**common, "concept": "document_type", "value": "invoice"},
            {**common, "concept": "document_reference", "value": reference},
            {**common, "concept": "issuer", "value": "Acme Hosting"},
            {**common, "concept": "service", "value": "Annual hosting"},
            {
                **common,
                "concept": "amount",
                "value": {"amount": "19.00", "currency": "EUR"},
            },
            {
                **common,
                "concept": "due_date",
                "value": "2026-09-01",
                "temporal": {"normalized": "2026-09-01", "precision": "day"},
            },
        ]

    @staticmethod
    def _attention(event_id: str, reference: str) -> dict[str, Any]:
        key = f"invoice:{reference.casefold()}"
        return {
            "event_id": event_id,
            "kind": "deadline",
            "title": "Acme Hosting · annual service",
            "status": "open",
            "knowledge_status": "known",
            "due_at": "2026-09-01T09:00:00+02:00",
            "details": {
                "entity_key": key,
                "lifecycle_key": key,
                "document_reference": reference,
            },
        }

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
        facts: list[dict[str, Any]] = []
        attention: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", ""))
            lowered = text.casefold()
            if "ref-123" in lowered and "due" in lowered:
                facts.extend(self._document_facts(event_id, "REF-123"))
                attention.append(self._attention(event_id, "REF-123"))
            elif "ref-124" in lowered and "due" in lowered:
                facts.extend(self._document_facts(event_id, "REF-124"))
                attention.append(self._attention(event_id, "REF-124"))
            elif "paid ref-123" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": {"key": "invoice:ref-123", "name": "Invoice · REF-123"},
                        "concept": "payment_status",
                        "knowledge_status": "known",
                        "value": "paid",
                        "lifecycle_key": "invoice:ref-123",
                        "lifecycle_action": "paid",
                        "related_event_id": "doc-ref-123",
                        "document_key": "invoice:ref-123",
                        "document_type": "Invoice",
                        "document_reference": "REF-123",
                        "document_title": "Invoice · REF-123",
                    }
                )
            elif "ordinary task" in lowered:
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "task",
                        "title": "Call Acme Hosting",
                        "status": "open",
                        "knowledge_status": "known",
                        "due_at": "2026-08-30T09:00:00+02:00",
                        "details": {
                            "entity_key": "task:call-acme",
                            "lifecycle_key": "task:call-acme",
                        },
                    }
                )
            elif "drank one" in lowered or "drank two" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "water",
                        "concept": "drink",
                        "knowledge_status": "known",
                        "value": {"amount": 1 if "one" in lowered else 2, "unit": "glass"},
                        "claim_type": "occurrence",
                    }
                )
            elif "ordinary current" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "ordinary note",
                        "concept": "status",
                        "knowledge_status": "known",
                        "value": "open",
                    }
                )
            elif "same title one" in lowered:
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "task",
                        "title": "Review account",
                        "status": "open",
                        "details": {"entity_key": "task:one", "lifecycle_key": "task:one"},
                    }
                )
            elif "same title two" in lowered:
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "task",
                        "title": "Review account",
                        "status": "open",
                        "details": {"entity_key": "task:two", "lifecycle_key": "task:two"},
                    }
                )
            elif "finished unrelated" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "unrelated completion",
                        "concept": "status",
                        "knowledge_status": "known",
                        "value": "completed",
                        "lifecycle_action": "completed",
                    }
                )
        return {"facts": facts, "attention": attention}

    @staticmethod
    def _all_candidates(context: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            item
            for collection in ("facts", "history", "relationships", "attention", "attention_history")
            for item in context.get(collection, [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]

    @staticmethod
    def _ids(items: list[dict[str, Any]]) -> list[str]:
        return [item["evidence_id"] for item in items if isinstance(item.get("evidence_id"), str)]

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
        if not self.answer_available:
            return {"answer": "Unsupported provider output.", "evidence_ids": []}
        lowered = question.casefold()
        derived = context.get("derived", {}) if isinstance(context.get("derived"), dict) else {}
        facts = [item for item in context.get("facts", []) if isinstance(item, dict)]
        attention = [item for item in context.get("attention", []) if isinstance(item, dict)]
        completed = [item for item in context.get("attention_history", []) if isinstance(item, dict)]
        if "how many" in lowered or "ile" in lowered:
            total = (derived.get("occurrence_totals") or [{}])[0]
            answer = f"You recorded {total.get('total')} {total.get('unit')} across {total.get('occurrence_count')} instances."
            return {"answer": answer, "evidence_ids": list(total.get("supporting_evidence_ids") or [])}
        if "paid" in lowered or "payment" in lowered:
            selected = [item for item in facts if item.get("concept") == "payment_status"][:1]
            return {"answer": "REF-123 was paid.", "evidence_ids": self._ids(selected)}
        if "did i do" in lowered or "completed" in lowered or "finished" in lowered:
            selected = completed[:5]
            labels = [str(item.get("title") or "completed item") for item in selected]
            return {
                "answer": "Completed today: " + "; ".join(labels) + ".",
                "evidence_ids": self._ids(selected),
            }
        if "attention" in lowered or "need to do" in lowered or "open" in lowered:
            selected = attention[:5]
            return {
                "answer": "Open items: " + "; ".join(str(item.get("title") or "open item") for item in selected) + ".",
                "evidence_ids": self._ids(selected),
            }
        if "mean" in lowered and derived.get("occurrence_totals"):
            total = derived["occurrence_totals"][0]
            return {
                "answer": f"The recorded total is {total.get('total')} {total.get('unit')}.",
                "evidence_ids": list(total.get("supporting_evidence_ids") or []),
            }
        selected = facts[:6] or attention[:3] or completed[:3]
        if not selected:
            return {"answer": "No matching evidence.", "evidence_ids": []}
        if self.unsafe_answer:
            return {
                "answer": "The answer is supported by self:1 and evidence_id.",
                "evidence_ids": self._ids(selected),
            }
        rendered = []
        for item in selected:
            value = item.get("value")
            if isinstance(value, dict):
                value = " ".join(str(part) for part in (value.get("amount"), value.get("currency")) if part is not None)
            rendered.append(f"{item.get('entity_label')}: {value or item.get('title')}")
        return {"answer": "; ".join(rendered) + ".", "evidence_ids": self._ids(selected)}


class ProductV2FinalCoherenceTests(unittest.TestCase):
    @staticmethod
    def runtime(directory: str, provider: CoherenceProvider) -> ProductRuntime:
        return ProductRuntime(
            directory,
            provider=provider,
            start_worker=False,
            batch_size=50,
            clock=lambda: BASE_NOW,
        )

    def test_document_identity_is_useful_and_preserves_raw_attachment_provenance(self) -> None:
        provider = CoherenceProvider()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider) as runtime:
                runtime.capture(
                    "Invoice REF-123 from Acme Hosting for annual service, 19 EUR due tomorrow.",
                    event_id="doc-ref-123",
                    attachment={
                        "content": b"synthetic invoice REF-123",
                        "filename": "synthetic-invoice.txt",
                        "mime_type": "text/plain",
                    },
                )
                self.assertEqual(runtime.process_pending()["processed"], 1)
                state = runtime.snapshot()
                document_facts = [item for item in state["current_facts"] if item["entity_label"] == "Invoice · REF-123"]
                self.assertGreaterEqual(len(document_facts), 4)
                self.assertTrue(all(item["entity_key"] == "invoice_ref_123" for item in document_facts))
                self.assertEqual(state["attachments"][0]["original_filename"], "synthetic-invoice.txt")
                self.assertEqual(runtime.store.raw_event("doc-ref-123")["payload"]["text"], "Invoice REF-123 from Acme Hosting for annual service, 19 EUR due tomorrow.")
                attention = state["attention"]
                self.assertEqual(len(attention), 1)
                self.assertIn("Acme Hosting", attention[0]["title"])
                self.assertIn("REF-123", json.dumps(state, ensure_ascii=False))

    def test_paid_capture_reconciles_matching_attention_and_survives_rebuild_restart(self) -> None:
        provider = CoherenceProvider()
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.runtime(directory, provider)
            runtime.capture("Invoice REF-123 from Acme Hosting for annual service, 19 EUR due tomorrow.", event_id="doc-ref-123")
            runtime.capture("Invoice REF-124 from Acme Hosting for annual service, 19 EUR due tomorrow.", event_id="doc-ref-124")
            self.assertEqual(runtime.process_pending()["processed"], 2)
            runtime.capture("I paid REF-123.", event_id="paid-ref-123")
            self.assertEqual(runtime.process_pending()["processed"], 1)
            state = runtime.snapshot()
            self.assertEqual(state["counts"]["attention"], 1)
            self.assertEqual({item["status"] for item in state["attention"]}, {"completed", "open"})
            completed = next(item for item in state["attention_history"] if item["status"] == "completed")
            self.assertIn("paid-ref-123", completed["source_refs"])
            self.assertTrue(any(item.get("concept") == "payment_status" and item.get("value") == "paid" for item in state["current_facts"]))
            answer = runtime.ask("Was REF-123 paid?")
            self.assertTrue(answer["provider_used"])
            self.assertIn("paid", answer["answer"].casefold())
            self.assertIn("paid-ref-123", answer["source_refs"])
            runtime.store.rebuild()
            runtime.close()

            reopened = self.runtime(directory, provider)
            try:
                rebuilt = reopened.snapshot()
                self.assertEqual(rebuilt["counts"]["attention"], 1)
                self.assertEqual({item["status"] for item in rebuilt["attention_history"]}, {"completed"})
                self.assertTrue(any(item["status"] == "open" and item["source_event_id"] == "doc-ref-124" for item in rebuilt["attention"]))
                self.assertEqual(reopened.store.raw_event("paid-ref-123")["payload"]["text"], "I paid REF-123.")
            finally:
                reopened.close()

    def test_done_is_removed_from_active_attention_but_remains_history_and_is_rebuildable(self) -> None:
        provider = CoherenceProvider()
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.runtime(directory, provider)
            runtime.capture("ordinary task: call Acme Hosting", event_id="ordinary-task")
            self.assertEqual(runtime.process_pending()["processed"], 1)
            before = runtime.snapshot()
            fingerprint = before["attention"][0]["fingerprint"]
            runtime.set_attention_status(fingerprint, "completed", note="Marked done by the user")
            after = runtime.snapshot()
            self.assertEqual(after["counts"]["attention"], 0)
            self.assertEqual(len(after["attention_history"]), 1)
            self.assertEqual(after["attention_history"][0]["status"], "completed")
            self.assertEqual(after["attention_history"][0]["details"].get("lifecycle_note"), "Marked done by the user")
            runtime.store.rebuild()
            runtime.close()
            reopened = self.runtime(directory, provider)
            try:
                self.assertEqual(reopened.snapshot()["counts"]["attention"], 0)
                self.assertEqual(reopened.snapshot()["attention_history"][0]["title"], "Call Acme Hosting")
            finally:
                reopened.close()

    def test_lifecycle_reconciliation_never_matches_by_title_alone(self) -> None:
        provider = CoherenceProvider()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider) as runtime:
                runtime.capture("same title one", event_id="same-one")
                runtime.capture("same title two", event_id="same-two")
                runtime.capture("finished unrelated note", event_id="finished-unrelated")
                self.assertEqual(runtime.process_pending()["processed"], 3)
                state = runtime.snapshot()
                self.assertEqual(len(state["attention"]), 2)
                self.assertTrue(all(item["status"] == "open" for item in state["attention"]))
                self.assertEqual(state["counts"]["attention"], 2)

    def test_required_ready_ask_modes_call_provider_and_receive_bounded_derived_evidence(self) -> None:
        provider = CoherenceProvider()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider) as runtime:
                for event_id, text in (
                    ("doc-ref-123", "Invoice REF-123 from Acme Hosting for annual service, 19 EUR due tomorrow."),
                    ("drink-one", "I drank one glass of water."),
                    ("drink-two", "I drank two glasses of water."),
                    ("ordinary-current", "ordinary current note is open"),
                    ("ordinary-task", "ordinary task: call Acme Hosting"),
                ):
                    runtime.capture(text, event_id=event_id)
                self.assertEqual(runtime.process_pending()["processed"], 5)
                task = next(item for item in runtime.snapshot()["attention"] if item["source_event_id"] == "ordinary-task")
                runtime.set_attention_status(task["fingerprint"], "completed", note="done")
                checks = [
                    ("Where is REF-123?", None),
                    ("How many glasses of water did I drink?", None),
                    ("What did I do today?", None),
                    ("What is the current state of the ordinary note?", None),
                    ("Where is REF-123 now?", None),
                ]
                thread: list[dict[str, str]] = []
                for question, _ in checks:
                    result = runtime.ask(question, thread_context=thread)
                    self.assertTrue(result["provider_used"], question)
                    self.assertFalse(result.get("degraded_fallback", False), question)
                    self.assertNotIn("self:1", result["answer"])
                    thread = [{"role": "user", "text": question}, {"role": "assistant", "text": result["answer"]}]
                followup = runtime.ask("What does that mean?", thread_context=thread)
                self.assertTrue(followup["provider_used"])
                self.assertGreaterEqual(provider.answer_calls, 6)
                for record in provider.answer_contexts:
                    serialized = json.dumps(record["context"], ensure_ascii=False)
                    self.assertNotIn("payload", serialized)
                    self.assertIn("derived", record["context"])
                    self.assertNotIn("self:1", serialized)

    def test_invalid_provider_answer_is_explicitly_degraded(self) -> None:
        provider = CoherenceProvider(answer_available=False)
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider) as runtime:
                runtime.capture("ordinary current note is open", event_id="degraded-note")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                result = runtime.ask("What is the current state of the ordinary note?")
                self.assertFalse(result["provider_used"])
                self.assertTrue(result["degraded_fallback"])
                self.assertEqual(result["provider_status"], "invalid_evidence")

    def test_internal_provider_answer_is_explicitly_degraded(self) -> None:
        provider = CoherenceProvider(unsafe_answer=True)
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider) as runtime:
                runtime.capture("ordinary current note", event_id="ordinary-current")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                result = runtime.ask("What is the ordinary current note?")

        self.assertFalse(result["provider_used"])
        self.assertTrue(result["degraded_fallback"])
        self.assertEqual(result["provider_status"], "unsafe_answer")
        self.assertNotIn("self:1", result["answer"])
        self.assertNotIn("evidence_id", result["answer"])

    def test_document_fields_are_normalized_without_guessing_missing_roles(self) -> None:
        event = {
            "event_id": "normalize-doc",
            "captured_at": "2026-08-30T08:00:00+00:00",
            "timezone": "UTC",
        }
        facts, _relations, _attention, _attachments = normalize_extraction(
            {
                "facts": [
                    {
                        "event_id": "normalize-doc",
                        "entity": "visible invoice text",
                        "concept": "amount",
                        "knowledge_status": "known",
                        "value": {"amount": "19.00", "currency": "EUR"},
                        "document_type": "Invoice",
                        "document_reference": "REF-123",
                        "document_title": "Invoice · REF-123",
                    }
                ]
            },
            events=[event],
            available_ids={"normalize-doc"},
            now=BASE_NOW,
        )
        self.assertEqual(facts[0]["entity_label"], "Invoice · REF-123")
        self.assertEqual(facts[0]["entity_key"], "document_invoice_ref_123")
        self.assertNotIn("issuer", facts[0]["metadata"])

    def test_generic_attention_title_uses_same_capture_document_context(self) -> None:
        event = {
            "event_id": "title-context",
            "captured_at": "2026-08-30T08:00:00+00:00",
            "timezone": "UTC",
        }
        facts, _relations, attention, _attachments = normalize_extraction(
            {
                "facts": [
                    {
                        "event_id": "title-context",
                        "entity": {"key": "document:invoice:REF-123", "name": "Invoice · REF-123"},
                        "concept": "issuer",
                        "knowledge_status": "known",
                        "value": "Acme Hosting",
                        "document_reference": "REF-123",
                    },
                    {
                        "event_id": "title-context",
                        "entity": {"key": "document:invoice:REF-123", "name": "Invoice · REF-123"},
                        "concept": "service",
                        "knowledge_status": "known",
                        "value": "Annual hosting",
                        "document_reference": "REF-123",
                    },
                ],
                "attention": [
                    {
                        "event_id": "title-context",
                        "kind": "deadline",
                        "title": "Invoice payment due",
                        "status": "open",
                        "due_at": "2026-09-01",
                        "details": {"entity_key": "document:invoice:REF-123"},
                    }
                ],
            },
            events=[event],
            available_ids={"title-context"},
            now=BASE_NOW,
        )
        self.assertEqual(len(attention), 1)
        self.assertEqual(attention[0]["title"], "Acme Hosting · Annual hosting · REF-123")


if __name__ == "__main__":
    unittest.main()
