from __future__ import annotations

import hashlib
import json
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.product_v2 import ProductRuntime
from app.product_v2_store import ProductStore, canonical_json
from app.state_store import StateStore


class ProductFakeProvider:
    """Deterministic Product V2 provider seam; never makes a live call."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.time_contexts: list[dict[str, Any]] = []
        self.fail = False
        self.answer_calls = 0
        self.block_started: threading.Event | None = None
        self.block_release: threading.Event | None = None

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, contract
        event_ids = [str(event["event_id"]) for event in events]
        self.calls.append(event_ids)
        self.time_contexts.append(time_context)
        if self.block_started is not None:
            self.block_started.set()
        if self.block_release is not None:
            self.block_release.wait(timeout=5)
        if self.fail:
            raise RuntimeError("provider failure with secret-token-value")
        facts: list[dict[str, Any]] = []
        attention: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", ""))
            lowered = text.casefold()
            if "pocketwave" in lowered and "11" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "PocketWave",
                        "concept": "recurring_cost",
                        "knowledge_status": "known",
                        "value": {"amount": "11", "currency": "EUR", "billing_period": "month"},
                        "operation": "correction",
                    }
                )
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
            elif "kids" in lowered or "dzieci" in lowered:
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "task",
                        "title": "Pick up the kids",
                        "status": "open",
                        "relative_minutes": 10,
                    }
                )
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "kids pickup",
                        "concept": "task",
                        "knowledge_status": "known",
                        "value": "Pick up the kids",
                    }
                )
            elif "basement" in lowered or "piwnicy" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "basement keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "mother's place",
                    }
                )
            elif "car" in lowered or "samochód" in lowered:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "car",
                        "concept": "condition",
                        "knowledge_status": "known",
                        "value": "knocking at the front left",
                    }
                )
            else:
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "inbox note",
                        "concept": "note_from_user",
                        "knowledge_status": "known",
                        "value": text,
                    }
                )
        return {"facts": facts, "attention": attention}

    def answer(self, *, question: str, context: dict[str, Any], time_context: dict[str, Any]) -> dict[str, Any]:
        del question, time_context
        self.answer_calls += 1
        evidence_ids = [
            item["evidence_id"]
            for collection in ("facts", "history", "relationships", "attention")
            for item in context.get(collection, [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]
        return {"answer": "A bounded provider summary.", "evidence_ids": evidence_ids}


def fixed_clock() -> datetime:
    return datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)


class ProductV2Tests(unittest.TestCase):
    def runtime(
        self,
        directory: str,
        provider: ProductFakeProvider | None = None,
        **kwargs: Any,
    ) -> ProductRuntime:
        return ProductRuntime(
            directory,
            provider=provider,
            start_worker=False,
            clock=fixed_clock,
            **kwargs,
        )

    def test_capture_returns_before_background_provider_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            provider.block_started = threading.Event()
            provider.block_release = threading.Event()
            started = time.monotonic()
            with ProductRuntime(
                directory,
                provider=provider,
                clock=fixed_clock,
                start_worker=True,
            ) as runtime:
                saved = runtime.capture("The provider may take its time.")
                elapsed = time.monotonic() - started
                self.assertLess(elapsed, 0.5)
                self.assertTrue(provider.block_started.wait(timeout=1))
                self.assertEqual(runtime.processing_status(saved["event_id"])["status"], "processing")
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 0)
                provider.block_release.set()
                self.assertTrue(runtime.wait_for_idle(timeout=3))
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 1)

    def test_pending_capture_is_processed_and_time_context_is_passed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture(
                    "Odbieram dzieci za 10 minut.",
                    captured_at="2026-08-30T10:00:00+02:00",
                    timezone_name="Europe/Berlin",
                    event_id="v2-time-1",
                )
                result = runtime.process_pending()
                self.assertEqual(result["processed"], 1)
                self.assertEqual(provider.time_contexts[0]["captures"][0]["timezone"], "Europe/Berlin")
                self.assertEqual(provider.time_contexts[0]["captures"][0]["captured_date"], "2026-08-30")
                self.assertEqual(runtime.processing_status("v2-time-1")["status"], "processed")

    def test_provider_failure_preserves_retryable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            provider.fail = True
            with self.runtime(directory, provider) as runtime:
                saved = runtime.capture("This must survive a provider outage.", event_id="v2-failure-1")
                failed = runtime.process_pending()
                self.assertEqual(failed["failed"], 1)
                self.assertEqual(runtime.processing_status(saved["event_id"])["status"], "failed")
                self.assertIsNotNone(runtime.store.raw_event(saved["event_id"]))
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 0)
                failed_answer = runtime.ask("What do I remember?")
                self.assertEqual(failed_answer["mode"], "processing_failed")
                self.assertNotIn("secret-token-value", json.dumps(failed_answer))
                provider.fail = False
                self.assertEqual(runtime.retry_failed()["retried"], 1)
                retried = runtime.process_pending()
                self.assertEqual(retried["processed"], 1)

    def test_stale_processing_lease_is_recovered_and_single_owner_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture("one owner", event_id="v2-lease-1")
                self.assertEqual(len(runtime.store.claim_pending("owner-a")), 1)
                self.assertEqual(runtime.store.claim_pending("owner-b"), [])
                with runtime.store._lock:
                    runtime.store.connection.execute(
                        "UPDATE processing_state SET lease_until = ? WHERE event_id = ?",
                        ("2000-01-01T00:00:00+00:00", "v2-lease-1"),
                    )
                    runtime.store.connection.commit()
                self.assertEqual(runtime.store.recover_stale_processing(), 1)
                self.assertEqual(runtime.processing_status("v2-lease-1")["status"], "pending")
                self.assertEqual(len(runtime.store.claim_pending("owner-b")), 1)

    def test_later_capture_waits_behind_earlier_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture("first", event_id="v2-order-1")
                runtime.capture("second", event_id="v2-order-2")
                self.assertEqual(len(runtime.store.claim_pending("owner-a", limit=1)), 1)
                self.assertEqual(runtime.store.claim_pending("owner-b", limit=2), [])
                runtime.store.commit_semantic(
                    "owner-a",
                    ["v2-order-1"],
                    facts=[],
                    relations=[],
                    attention=[],
                    extractor_version="test-order",
                )
                claimed = runtime.store.claim_pending("owner-b", limit=2)
                self.assertEqual([event["event_id"] for event in claimed], ["v2-order-2"])

    def test_duplicate_processing_does_not_duplicate_semantic_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture("The car started knocking.", event_id="v2-dup-1")
                first = runtime.process_pending()
                second = runtime.process_pending()
                self.assertEqual(first["processed"], 1)
                self.assertEqual(second["processed"], 0)
                self.assertEqual(provider.calls, [["v2-dup-1"]])
                self.assertEqual(runtime.snapshot()["counts"]["fact_history"], 1)

    def test_relative_attention_is_deterministic_and_upcoming_then_overdue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture(
                    "Odbieram dzieci za 10 minut.",
                    event_id="v2-attention-1",
                    captured_at="2026-08-30T10:00:00+02:00",
                    timezone_name="Europe/Berlin",
                )
                runtime.process_pending()
                first = runtime.snapshot()["attention"]
                self.assertEqual(first[0]["due_at"], "2026-08-30T10:10:00+02:00")
                self.assertEqual(first[0]["state"], "upcoming")
                runtime.clock = lambda: datetime(2026, 8, 30, 8, 20, tzinfo=timezone.utc)
                self.assertEqual(runtime.snapshot()["attention"][0]["state"], "overdue")
                asked = runtime.ask("What do I need to do today?")
                self.assertEqual(asked["mode"], "attention")
                self.assertFalse(asked["provider_used"])
                runtime.set_attention_status(first[0]["fingerprint"], "completed", note="done in test")
                self.assertEqual(runtime.snapshot()["attention"][0]["state"], "completed")

    def test_combined_capture_keeps_text_and_attachment_link(self) -> None:
        content = b"combined-product-v2"
        expected_hash = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                saved = runtime.capture(
                    "The receipt is attached.",
                    attachment={"content": content, "filename": "receipt.txt", "mime_type": "text/plain"},
                    event_id="v2-combined-1",
                )
                raw = runtime.store.raw_event("v2-combined-1")
                self.assertEqual(raw["payload"]["text"], "The receipt is attached.")
                self.assertEqual(raw["payload"]["attachments"][0]["sha256"], expected_hash)
                self.assertEqual(saved["attachments"][0]["blob_ref"], f"sha256:{expected_hash}")

    def test_empty_known_value_is_preserved_as_unknown(self) -> None:
        class UnknownProvider:
            def extract(
                self,
                *,
                events: list[dict[str, Any]],
                prior_memory: dict[str, Any],
                time_context: dict[str, Any],
                contract: dict[str, Any],
            ) -> dict[str, Any]:
                del prior_memory, time_context, contract
                return {
                    "facts": [
                        {
                            "event_id": events[0]["event_id"],
                            "entity": "ambiguous item",
                            "concept": "owner",
                            "knowledge_status": "known",
                            "value": "",
                        }
                    ]
                }

        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, UnknownProvider()) as runtime:
                runtime.capture("The owner was not stated.", event_id="v2-unknown-1")
                runtime.process_pending()
                fact = runtime.snapshot()["current_facts"][0]
                self.assertEqual(fact["knowledge_status"], "unknown")
                self.assertNotIn("value", fact)
                self.assertEqual(fact["unknown_reason"], "not_stated")

    def test_attachment_only_capture_uses_integrity_checked_content_addressed_blob(self) -> None:
        content = b"%PDF-Product-V2-test"
        expected_hash = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                saved = runtime.capture(
                    None,
                    attachment={
                        "content": content,
                        "filename": "contract.pdf",
                        "mime_type": "application/pdf",
                    },
                    event_id="v2-attachment-1",
                )
                self.assertEqual(saved["attachments"][0]["sha256"], expected_hash)
                self.assertEqual(saved["attachments"][0]["blob_ref"], f"sha256:{expected_hash}")
                raw = runtime.store.raw_event("v2-attachment-1")
                self.assertNotIn("text", raw["payload"])
                attachment = runtime.snapshot()["attachments"][0]
                self.assertEqual(attachment["byte_length"], len(content))
                self.assertEqual(attachment["processing_status"], "unread")
                actual, metadata = runtime.attachment_bytes(expected_hash)
                self.assertEqual(actual, content)
                self.assertEqual(metadata["mime_type"], "application/pdf")

    def test_retract_is_auditable_and_removes_fact_from_rebuildable_active_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture("The car started knocking.", event_id="v2-retract-1")
                runtime.process_pending()
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 1)
                result = runtime.retract("v2-retract-1")
                self.assertTrue(result["retracted"])
                state = runtime.snapshot()
                self.assertEqual(state["counts"]["facts"], 0)
                self.assertEqual(state["retracted_event_ids"], ["v2-retract-1"])
                self.assertTrue(state["fact_history"][0]["retracted"])
                self.assertIsNotNone(runtime.store.raw_event("v2-retract-1"))
                runtime.store.rebuild()
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 0)

    def test_open_world_fact_and_deterministic_ask_do_not_need_provider_answer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture("The keys to the basement are at my mother's place.", event_id="v2-open-1")
                runtime.process_pending()
                facts = runtime.snapshot()["current_facts"]
                self.assertEqual(facts[0]["concept"], "location")
                self.assertEqual(facts[0]["value"], "mother's place")
                answer = runtime.ask("What do I know about basement keys?")
                self.assertEqual(answer["mode"], "retrieval")
                self.assertFalse(answer["provider_used"])
                self.assertEqual(provider.answer_calls, 0)
                self.assertIn("v2-open-1", answer["source_refs"])

    def test_semantic_ask_uses_bounded_mock_provider_and_source_refs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture("A note about the apartment contract.", event_id="v2-ask-1")
                runtime.process_pending()
                answer = runtime.ask("Please synthesize the context for me.")
                self.assertEqual(answer["mode"], "semantic")
                self.assertTrue(answer["provider_used"])
                self.assertEqual(provider.answer_calls, 1)
                self.assertEqual(answer["source_refs"], ["v2-ask-1"])

    def test_migration_copies_legacy_raw_and_derived_state_without_mutating_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            legacy_path = home / "blackhole.db"
            payload = {"text": "Legacy source remains auditable."}
            event = {
                "event_id": "legacy-1",
                "sequence": 1,
                "captured_at": "2026-08-30T08:00:00+00:00",
                "observed_at": "2026-08-30",
                "source_type": "text",
                "payload": payload,
                "metadata": {},
            }
            with StateStore(legacy_path) as store:
                store.insert_raw_events([event])
                store.add_observations(
                    [
                        {
                            "event_id": "legacy-1",
                            "subject": "legacy object",
                            "predicate": "custom property",
                            "knowledge_status": "known",
                            "value": "kept",
                        }
                    ],
                    "legacy-test",
                )
                original = store.raw_event("legacy-1")
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                state = runtime.snapshot()
                self.assertEqual(state["counts"]["captures"], 1)
                self.assertTrue(any(item["concept"] == "custom_property" for item in state["current_facts"]))
                self.assertEqual(runtime.store.raw_event("legacy-1")["payload"], payload)
                self.assertEqual(runtime.processing_status("legacy-1")["status"], "processed")
            with StateStore(legacy_path) as store:
                self.assertEqual(store.raw_event("legacy-1"), original)


if __name__ == "__main__":
    unittest.main()
