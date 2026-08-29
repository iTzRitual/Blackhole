from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.state_store import StateStore, canonical_json


def raw_event(event_id: str, sequence: int, text: str) -> dict:
    payload = {"text": text}
    return {
        "event_id": event_id,
        "sequence": sequence,
        "captured_at": f"2026-01-{sequence:02d}T09:00:00+01:00",
        "observed_at": f"2026-01-{sequence:02d}",
        "source_type": "text",
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        "metadata": {"synthetic": True},
    }


class StateStoreTests(unittest.TestCase):
    def test_raw_events_are_immutable_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = raw_event("evt-001", 1, "A captured fact")
            with StateStore(Path(directory) / "state.sqlite") as store:
                self.assertEqual(store.insert_raw_events([event]), 1)
                self.assertEqual(store.insert_raw_events([event]), 0)
                with self.assertRaises(sqlite3.IntegrityError):
                    store.connection.execute("UPDATE raw_events SET source_type = 'changed'")
                with self.assertRaises(sqlite3.IntegrityError):
                    store.connection.execute("DELETE FROM raw_events")
                conflicting = dict(event)
                conflicting["payload"] = {"text": "A different fact"}
                with self.assertRaises(ValueError):
                    store.insert_raw_events([conflicting])

    def test_projection_supersedes_current_value_but_keeps_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            events = [
                raw_event("evt-001", 1, "The service costs 10 EUR."),
                raw_event("evt-002", 2, "The service now costs 12 EUR."),
                raw_event("evt-003", 3, "Correction: it costs 11 EUR."),
            ]
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(events)
                store.add_observations(
                    [
                        {"event_id": "evt-001", "subject": "service", "predicate": "current_price", "knowledge_status": "known", "value": {"amount": "10", "currency": "EUR"}},
                        {"event_id": "evt-002", "subject": "service", "predicate": "current_price", "knowledge_status": "known", "value": {"amount": "12", "currency": "EUR"}, "operation": "supersede", "supersedes_event_id": "evt-001"},
                        {"event_id": "evt-003", "subject": "service", "predicate": "current_price", "knowledge_status": "known", "value": {"amount": "11", "currency": "EUR"}, "operation": "correction", "supersedes_event_id": "evt-002"},
                    ],
                    "test-extractor",
                )
                store.rebuild_projection()
                snapshot = store.snapshot()
                current = [item for item in snapshot["current_facts"] if item["predicate"] == "current_price"]
                self.assertEqual(current[0]["value"]["amount"], "11")
                self.assertEqual(len(snapshot["history"]), 3)

    def test_unresolved_contradiction_projects_to_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            events = [raw_event("evt-001", 1, "The amount is 10."), raw_event("evt-002", 2, "Another note says 12.")]
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(events)
                store.add_observations(
                    [
                        {"event_id": "evt-001", "subject": "service", "predicate": "amount", "knowledge_status": "known", "value": 10},
                        {"event_id": "evt-002", "subject": "service", "predicate": "amount", "knowledge_status": "known", "value": 12, "operation": "contradiction", "supersedes_event_id": "evt-001"},
                    ],
                    "test-extractor",
                )
                store.rebuild_projection()
                current = store.snapshot()["current_facts"]
                self.assertEqual(current[0]["knowledge_status"], "unknown")
                self.assertEqual(current[0]["unknown_reason"], "conflicting")
                self.assertEqual(set(current[0]["source_refs"]), {"evt-001", "evt-002"})

    def test_duplicate_events_are_counted_and_not_current_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            events = [raw_event("evt-001", 1, "The amount is 10."), raw_event("evt-002", 2, "The same amount is repeated.")]
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(events)
                store.add_observations(
                    [
                        {"event_id": "evt-001", "subject": "service", "predicate": "amount", "knowledge_status": "known", "value": 10},
                        {"event_id": "evt-002", "subject": "service", "predicate": "amount", "knowledge_status": "known", "value": 10, "operation": "duplicate"},
                    ],
                    "test-extractor",
                )
                store.add_relationships(
                    [{"source_event_id": "evt-002", "target_event_id": "evt-001", "relation_type": "exact_duplicate", "duplicate_group": "group-1"}],
                    "test-extractor",
                )
                store.rebuild_projection()
                snapshot = store.snapshot()
                self.assertEqual(len(snapshot["current_facts"]), 1)
                self.assertEqual(snapshot["current_facts"][0]["source_refs"], ["evt-001"])
                self.assertEqual(snapshot["deterministic_counts"]["duplicate_event_count"], 1)
                self.assertEqual(snapshot["deterministic_counts"]["duplicate_group_count"], 1)

    def test_projection_is_rebuildable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = raw_event("evt-001", 1, "The service is active.")
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events([event])
                store.add_observations(
                    [{"event_id": "evt-001", "subject": "service", "predicate": "status", "knowledge_status": "known", "value": "active"}],
                    "test-extractor",
                )
                store.rebuild_projection()
                first = store.snapshot()
                store.rebuild_projection()
                second = store.snapshot()
                self.assertEqual(first["current_facts"], second["current_facts"])
                self.assertEqual(first["history"], second["history"])
                self.assertEqual(first["relationships"], second["relationships"])


if __name__ == "__main__":
    unittest.main()
