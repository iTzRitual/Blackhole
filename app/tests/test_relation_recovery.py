from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from app.relation_recovery import deterministic_relationships, retrieved_relation_replacements
from app.state_store import StateStore, canonical_json


def event(event_id: str, sequence: int, text: str, *, source_type: str = "text") -> dict:
    payload = {"text": text}
    return {
        "event_id": event_id,
        "sequence": sequence,
        "captured_at": f"2026-01-{sequence:02d}T09:00:00+01:00",
        "observed_at": f"2026-01-{sequence:02d}",
        "source_type": source_type,
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        "metadata": {"synthetic": True},
    }


class RelationRecoveryTests(unittest.TestCase):
    def test_explicit_supersession_is_recovered_without_existing_relation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events([event("capture-a", 1, "A fact"), event("capture-b", 2, "A correction")])
                store.add_observations(
                    [
                        {"event_id": "capture-a", "subject": "neutral_item", "predicate": "amount", "knowledge_status": "known", "value": 10},
                        {"event_id": "capture-b", "subject": "neutral_item", "predicate": "amount", "knowledge_status": "known", "value": 12, "operation": "correction", "supersedes_event_id": "capture-a"},
                    ],
                    "fixture-extractor",
                )
                recovered = deterministic_relationships(store.connection)
                self.assertEqual(
                    recovered,
                    [
                        {
                            "source_event_id": "capture-b",
                            "target_event_id": "capture-a",
                            "relation_type": "correction",
                            "changed_fields": ["amount"],
                        }
                    ],
                )

    def test_identical_raw_payload_requires_duplicate_observation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events([event("capture-a", 1, "same note"), event("capture-b", 2, "same note")])
                store.add_observations(
                    [
                        {"event_id": "capture-a", "subject": "neutral_item", "predicate": "status", "knowledge_status": "known", "value": "open"},
                        {"event_id": "capture-b", "subject": "neutral_item", "predicate": "status", "knowledge_status": "known", "value": "open", "operation": "duplicate"},
                    ],
                    "fixture-extractor",
                )
                recovered = deterministic_relationships(store.connection)
                self.assertEqual(recovered[0]["relation_type"], "exact_duplicate")
                self.assertEqual(recovered[0]["target_event_id"], "capture-a")

    def test_repeated_text_without_duplicate_marking_is_not_silently_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events([event("capture-a", 1, "same note"), event("capture-b", 2, "same note")])
                store.add_observations(
                    [
                        {"event_id": "capture-a", "subject": "neutral_item", "predicate": "status", "knowledge_status": "known", "value": "open"},
                        {"event_id": "capture-b", "subject": "neutral_item", "predicate": "status", "knowledge_status": "known", "value": "open"},
                    ],
                    "fixture-extractor",
                )
                self.assertEqual(deterministic_relationships(store.connection), [])

    def test_retrieval_uses_primary_identifier_and_bounded_raw_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        event("receipt-a", 1, "Harbor Market receipt H-100: 10 EUR."),
                        event("receipt-b", 2, "Harbor Market receipt H-100 uploaded unchanged."),
                        event("receipt-c", 3, "Receipt H-100 is a separate purchase from H-101.", source_type="receipt"),
                        event("receipt-d", 4, "Receipt H-100 uploaded unchanged for backup.", source_type="receipt"),
                    ]
                )
                store.add_relationships(
                    [
                        {"source_event_id": "receipt-b", "target_event_id": "receipt-a", "relation_type": "exact_duplicate", "duplicate_group": "old-group"},
                        {"source_event_id": "receipt-c", "target_event_id": "receipt-a", "relation_type": "similar_not_duplicate", "changed_fields": ["receipt_id"]},
                        {"source_event_id": "receipt-d", "target_event_id": "receipt-a", "relation_type": "normalized_duplicate", "duplicate_group": "old-group"},
                    ],
                    "fixture-extractor",
                )
                result = retrieved_relation_replacements(store.connection, max_candidates=2)
                replacements = {item["source_event_id"]: item for item in result["replacements"]}
                self.assertEqual(replacements["receipt-b"]["relation_type"], "exact_duplicate")
                self.assertEqual(replacements["receipt-b"]["duplicate_group"], "harbor-h-100")
                self.assertEqual(replacements["receipt-c"]["target_event_id"], "receipt-b")
                self.assertEqual(replacements["receipt-c"]["changed_fields"], [])
                self.assertEqual(replacements["receipt-c"]["note"], "different receipt identifier and purchase")
                self.assertEqual(replacements["receipt-d"]["target_event_id"], "receipt-c")
                self.assertLessEqual(
                    max(len(item["candidates"]) for item in result["candidate_sets"]),
                    2,
                )

    def test_replacement_preserves_raw_events_and_rebuilds_derived_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events([event("receipt-a", 1, "Harbor receipt H-1."), event("receipt-b", 2, "Receipt H-1 unchanged.", source_type="receipt")])
                store.add_relationships(
                    [{"source_event_id": "receipt-b", "target_event_id": "receipt-a", "relation_type": "exact_duplicate", "duplicate_group": "old"}],
                    "fixture-extractor",
                )
                replacement = {"source_event_id": "receipt-b", "target_event_id": "receipt-a", "relation_type": "exact_duplicate", "duplicate_group": "new"}
                store.replace_relationships_for_sources([replacement], "fixture-recovery")
                self.assertEqual(store.connection.execute("select count(*) from raw_events").fetchone()[0], 2)
                self.assertEqual(store.snapshot()["relationships"][0]["duplicate_group"], "new")


if __name__ == "__main__":
    unittest.main()
