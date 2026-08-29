from __future__ import annotations

import contextlib
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from typing import Any

from app.ingestion_engine import IngestionEngine
from app.process_pending import main as process_pending_main
from app.state_store import StateStore, canonical_json


NEUTRAL_CONTRACT: dict[str, Any] = {
    "response_contract": "neutral-deferred-test-v1",
    "unknown_reason": {"allowed_categories": ["not_stated", "conflicting", "missing"]},
    "public_ontology": {"subjects": [], "predicates": []},
    "value_normalization": {"object_field_aliases": {}, "enum_field_aliases": {}},
}


def raw_text(event: dict[str, Any]) -> str:
    payload = event.get("payload", {})
    return payload.get("text", "") if isinstance(payload, dict) else ""


class FakeProvider:
    """Deterministic semantic adapter used only by the product integration test."""

    def __init__(self, *, fail_ids: set[str] | None = None) -> None:
        self.fail_ids = set(fail_ids or set())
        self.calls: list[list[str]] = []
        self.price_event_id: str | None = None
        self.duplicate_event_id: str | None = None
        self.executed_actions = 0

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_snapshot: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_snapshot, contract
        event_ids = [str(event["event_id"]) for event in events]
        self.calls.append(event_ids)
        failing = next((event_id for event_id in event_ids if event_id in self.fail_ids), None)
        if failing is not None:
            raise RuntimeError(f"synthetic provider failure for {failing}")

        observations: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            text = raw_text(event)
            lowered = text.casefold()
            if "pinevault" in lowered and "renewal" in lowered:
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "pinevault",
                        "predicate": "renewal_date",
                        "knowledge_status": "known",
                        "value": "2028-04-17",
                    }
                )
            elif lowered.startswith("lumenledger costs 20"):
                self.price_event_id = event_id
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "lumenledger",
                        "predicate": "monthly_cost",
                        "knowledge_status": "known",
                        "value": {"amount": "20", "currency": "EUR"},
                    }
                )
            elif lowered.startswith("lumenledger will cost 25"):
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "lumenledger",
                        "predicate": "monthly_cost",
                        "knowledge_status": "known",
                        "value": {"amount": "25", "currency": "EUR"},
                        "operation": "correction",
                        "supersedes_event_id": self.price_event_id,
                    }
                )
            elif lowered.startswith("harborshield renewal"):
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "harborshield",
                        "predicate": "renewal_date",
                        "knowledge_status": "unknown",
                        "unknown_reason": "not stated; only a month is known",
                    }
                )
            elif lowered.startswith("prepare a payment"):
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "lumen_transfer",
                        "predicate": "status",
                        "knowledge_status": "known",
                        "value": "proposed",
                    }
                )
            elif lowered.startswith("micanote receipt"):
                operation = "set"
                observation: dict[str, Any] = {
                    "event_id": event_id,
                    "subject": "micanote",
                    "predicate": "purchase_amount",
                    "knowledge_status": "known",
                    "value": {"amount": "14", "currency": "EUR"},
                }
                if self.duplicate_event_id is None:
                    self.duplicate_event_id = event_id
                else:
                    operation = "duplicate"
                    observation["operation"] = operation
                    relationships.append(
                        {
                            "source_event_id": event_id,
                            "target_event_id": self.duplicate_event_id,
                            "relation_type": "exact_duplicate",
                        }
                    )
                observations.append(observation)
        return {"observations": observations, "relationships": relationships}


def neutral_event(event_id: str, sequence: int, text: str) -> dict[str, Any]:
    payload = {"text": text}
    return {
        "event_id": event_id,
        "sequence": sequence,
        "captured_at": f"2028-01-{sequence:02d}T09:00:00+00:00",
        "observed_at": f"2028-01-{sequence:02d}",
        "source_type": "text",
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        "metadata": {"synthetic": True},
    }


class DeferredIngestionTests(unittest.TestCase):
    def engine(self, path: Path, provider: FakeProvider | None, *, batch_size: int = 1) -> IngestionEngine:
        return IngestionEngine(
            path,
            contract=NEUTRAL_CONTRACT,
            provider=provider,
            batch_size=batch_size,
        )

    def test_capture_is_immediate_raw_only_without_provider_then_processes_later(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            with self.engine(db_path, None) as capture_engine:
                saved = capture_engine.capture(
                    "Renewal for PineVault is 2028-04-17.",
                    event_id="neutral-basic-1",
                    captured_at="2028-01-01T09:00:00+00:00",
                    observed_at="2028-01-01",
                )
                self.assertEqual(saved["message"], "Saved.")
                self.assertEqual(saved["processing_status"], "pending")
                self.assertNotIn("semantic_status", capture_engine.store.raw_event("neutral-basic-1")["metadata"])
                raw_before_processing = capture_engine.store.raw_event("neutral-basic-1")
                self.assertEqual(
                    raw_before_processing["payload"]["text"],
                    "Renewal for PineVault is 2028-04-17.",
                )
                self.assertEqual(capture_engine.snapshot()["current_facts"], [])

            provider = FakeProvider()
            with self.engine(db_path, provider) as engine:
                result = engine.process_pending()
                self.assertEqual(result["processed"], 1)
                self.assertEqual(provider.calls, [["neutral-basic-1"]])
                current = engine.snapshot()["current_facts"]
                self.assertEqual(current[0]["subject"], "pinevault")
                self.assertEqual(current[0]["value"], "2028-04-17")
                self.assertEqual(engine.store.raw_event("neutral-basic-1"), raw_before_processing)
                status = engine.processing_status("neutral-basic-1")
                self.assertEqual(status["status"], "processed")
                self.assertEqual(status["attempt_count"], 1)
                self.assertIsNotNone(status["last_successful_at"])
                self.assertEqual(status["extractor_version"], "blackhole-semantic-extractor-v1")

                first_snapshot = engine.snapshot()
                second = engine.process_pending()
                second_snapshot = engine.snapshot()
                self.assertEqual(second["processed"], 0)
                self.assertEqual(second["semantic_effects"], 0)
                self.assertEqual(len(provider.calls), 1)
                self.assertEqual(second_snapshot["current_facts"], first_snapshot["current_facts"])
                self.assertEqual(second_snapshot["history"], first_snapshot["history"])
                self.assertEqual(second_snapshot["relationships"], first_snapshot["relationships"])
                self.assertEqual(second_snapshot["deterministic_counts"], first_snapshot["deterministic_counts"])

                fresh = engine.ensure_state_fresh()
                self.assertTrue(fresh["fresh"])
                self.assertEqual(fresh["processed"], 0)
                self.assertEqual(len(provider.calls), 1)

    def test_correction_preserves_history_and_current_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            provider = FakeProvider()
            with self.engine(db_path, provider) as engine:
                engine.capture("LumenLedger costs 20 EUR.", event_id="neutral-price-1")
                engine.capture("LumenLedger will cost 25 EUR from March.", event_id="neutral-price-2")
                result = engine.process_pending()
                self.assertEqual(result["processed"], 2)
                current = [item for item in engine.snapshot()["current_facts"] if item["subject"] == "lumenledger"]
                self.assertEqual(current[0]["value"]["amount"], "25")
                history = [item for item in engine.snapshot()["history"] if item["subject"] == "lumenledger"]
                self.assertEqual(len(history), 2)
                self.assertEqual(history[0]["value"]["amount"], "20")
                self.assertEqual(history[1]["operation"], "correction")
                self.assertEqual(engine.store.raw_event("neutral-price-1")["payload"]["text"], "LumenLedger costs 20 EUR.")

    def test_pending_events_are_bounded_and_processed_in_sequence_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            provider = FakeProvider()
            with self.engine(db_path, provider, batch_size=2) as engine:
                for index in range(1, 4):
                    engine.capture(
                        f"Renewal for PineVault is 2028-04-{16 + index:02d}.",
                        event_id=f"neutral-order-{index}",
                    )
                result = engine.process_pending()
                self.assertEqual(result["processed"], 3)
                self.assertEqual(provider.calls, [["neutral-order-1", "neutral-order-2"], ["neutral-order-3"]])
                self.assertEqual(
                    [engine.processing_status(f"neutral-order-{index}")["status"] for index in range(1, 4)],
                    ["processed", "processed", "processed"],
                )

    def test_unknown_and_consequential_action_are_explicitly_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            provider = FakeProvider()
            with self.engine(db_path, provider) as engine:
                engine.capture(
                    "HarborShield renewal is somewhere in November; I need to check.",
                    event_id="neutral-unknown-1",
                )
                engine.capture("Prepare a payment to LumenLedger, but do not send it.", event_id="neutral-action-1")
                engine.process_pending()
                facts = engine.snapshot()["current_facts"]
                unknown = next(item for item in facts if item["subject"] == "harborshield")
                self.assertEqual(unknown["knowledge_status"], "unknown")
                self.assertEqual(unknown["unknown_reason"], "not_stated")
                self.assertNotIn("value", unknown)
                action = next(item for item in facts if item["subject"] == "lumen_transfer")
                self.assertEqual(action["value"], "proposed")
                self.assertEqual(provider.executed_actions, 0)

    def test_duplicate_evidence_preserves_two_raw_events_and_one_occurrence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            with self.engine(db_path, FakeProvider()) as engine:
                engine.capture("MicaNote receipt 14 EUR.", event_id="neutral-duplicate-1")
                engine.capture("MicaNote receipt 14 EUR.", event_id="neutral-duplicate-2")
                result = engine.process_pending()
                snapshot = engine.snapshot()
                self.assertEqual(result["processed"], 2)
                self.assertEqual(len(snapshot["event_index"]), 2)
                self.assertEqual(len(snapshot["duplicate_components"]), 1)
                self.assertEqual(snapshot["duplicate_components"][0]["member_count"], 2)
                purchase_facts = [item for item in snapshot["current_facts"] if item["subject"] == "micanote"]
                self.assertEqual(len(purchase_facts), 1)
                self.assertEqual(snapshot["deterministic_counts"]["duplicate_event_count"], 1)
                self.assertEqual(
                    snapshot["duplicate_evidence_stats"]["count_invariants"]["duplicate_component_occurrence_units"],
                    1,
                )

    def test_failure_preserves_previous_state_and_retry_is_chronological(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            provider = FakeProvider(fail_ids={"neutral-failure-2"})
            with self.engine(db_path, provider) as engine:
                engine.capture("Renewal for PineVault is 2028-04-17.", event_id="neutral-valid-1")
                engine.capture("Renewal for PineVault is 2028-04-17.", event_id="neutral-failure-2")
                engine.capture("Renewal for PineVault is 2028-04-17.", event_id="neutral-after-failure-3")
                first = engine.process_pending()
                self.assertEqual(first["processed"], 1)
                self.assertEqual(first["failed"], 1)
                self.assertEqual(engine.processing_status("neutral-failure-2")["status"], "failed")
                failed_status = engine.processing_status("neutral-failure-2")
                self.assertEqual(failed_status["attempt_count"], 1)
                self.assertIn("synthetic provider failure", failed_status["last_error"])
                self.assertEqual(engine.processing_status("neutral-after-failure-3")["status"], "pending")
                self.assertEqual(len(engine.snapshot()["current_facts"]), 1)
                self.assertIsNotNone(engine.store.raw_event("neutral-failure-2"))

                provider.fail_ids.clear()
                retry = engine.retry_failed()
                self.assertEqual(retry["processed"], 1)
                self.assertEqual(engine.processing_status("neutral-failure-2")["attempt_count"], 2)
                tail = engine.process_pending()
                self.assertEqual(tail["processed"], 1)
                self.assertTrue(all(engine.processing_status(event_id)["status"] == "processed" for event_id in (
                    "neutral-valid-1",
                    "neutral-failure-2",
                    "neutral-after-failure-3",
                )))
                self.assertEqual(provider.calls, [
                    ["neutral-valid-1"],
                    ["neutral-failure-2"],
                    ["neutral-failure-2"],
                    ["neutral-after-failure-3"],
                ])

    def test_empty_processing_command_needs_no_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = process_pending_main(["--db", str(Path(directory) / "empty.sqlite")])
            self.assertEqual(code, 0)
            self.assertIn("0 pending captures", output.getvalue())
            self.assertIn("state already fresh", output.getvalue())


if __name__ == "__main__":
    unittest.main()
