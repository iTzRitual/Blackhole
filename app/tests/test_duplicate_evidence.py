from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from app.state_store import StateStore, canonical_json


def raw_capture(event_id: str, sequence: int, text: str) -> dict:
    payload = {"text": text}
    return {
        "event_id": event_id,
        "sequence": sequence,
        "captured_at": f"2026-02-{sequence:02d}T09:00:00+01:00",
        "observed_at": f"2026-02-{sequence:02d}",
        "source_type": "text",
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        "metadata": {"synthetic": True},
    }


def observation(
    event_id: str,
    subject: str,
    predicate: str,
    value: object,
    *,
    operation: str = "set",
    knowledge_status: str = "known",
    supersedes_event_id: str | None = None,
) -> dict:
    item = {
        "event_id": event_id,
        "subject": subject,
        "predicate": predicate,
        "knowledge_status": knowledge_status,
        "operation": operation,
    }
    if knowledge_status == "unknown":
        item["unknown_reason"] = str(value)
    else:
        item["value"] = value
    if supersedes_event_id is not None:
        item["supersedes_event_id"] = supersedes_event_id
    return item


def duplicate(source: str, target: str, relation_type: str = "exact_duplicate") -> dict:
    return {
        "source_event_id": source,
        "target_event_id": target,
        "relation_type": relation_type,
    }


class DuplicateEvidenceTests(unittest.TestCase):
    def test_identical_duplicate_evidence_is_one_fact_with_union_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-a", 1, "A purchase was 20 EUR."),
                        raw_capture("capture-b", 2, "The same purchase was 20 EUR."),
                    ]
                )
                store.add_observations(
                    [
                        observation("capture-a", "merchant_alpha", "amount", {"amount": "20", "currency": "EUR"}),
                        observation(
                            "capture-b",
                            "merchant_alpha",
                            "amount",
                            {"amount": "20", "currency": "EUR"},
                            operation="duplicate",
                        ),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships([duplicate("capture-b", "capture-a")], "neutral-fixture-extractor")

                store.rebuild_projection(duplicate_evidence=True)
                snapshot = store.snapshot()

                facts = [item for item in snapshot["current_facts"] if item["predicate"] == "amount"]
                self.assertEqual(len(facts), 1)
                self.assertEqual(facts[0]["value"]["amount"], "20")
                self.assertEqual(set(facts[0]["source_refs"]), {"capture-a", "capture-b"})
                self.assertEqual(snapshot["duplicate_evidence_stats"]["consolidated_identical_observations"], 1)

    def test_duplicate_can_add_a_nonconflicting_predicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-c", 3, "The agreement is active."),
                        raw_capture("capture-d", 4, "The active agreement renews on June 30."),
                    ]
                )
                store.add_observations(
                    [
                        observation("capture-c", "agreement_beta", "status", "active"),
                        observation("capture-d", "agreement_beta", "status", "active", operation="duplicate"),
                        observation("capture-d", "agreement_beta", "renewal_date", "2026-06-30", operation="duplicate"),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships(
                    [duplicate("capture-d", "capture-c", "normalized_duplicate")],
                    "neutral-fixture-extractor",
                )

                store.rebuild_projection(duplicate_evidence=True)
                facts = {
                    item["predicate"]: item
                    for item in store.snapshot()["current_facts"]
                    if item["subject"] == "agreement_beta"
                }
                self.assertEqual(facts["status"]["value"], "active")
                self.assertEqual(facts["renewal_date"]["value"], "2026-06-30")

    def test_unresolved_duplicate_value_conflict_remains_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-e", 5, "The amount is 20."),
                        raw_capture("capture-f", 6, "A duplicate capture says 25."),
                    ]
                )
                store.add_observations(
                    [
                        observation("capture-e", "merchant_alpha", "amount", 20),
                        observation("capture-f", "merchant_alpha", "amount", 25, operation="duplicate"),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships([duplicate("capture-f", "capture-e")], "neutral-fixture-extractor")

                store.rebuild_projection(duplicate_evidence=True)
                fact = next(item for item in store.snapshot()["current_facts"] if item["predicate"] == "amount")
                self.assertEqual(fact["knowledge_status"], "unknown")
                self.assertEqual(fact["unknown_reason"], "conflicting")
                self.assertNotIn("value", fact)
                self.assertEqual(store.snapshot()["duplicate_evidence_stats"]["conflicts_preserved"], 1)

    def test_similar_not_duplicate_is_not_consolidated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-g", 7, "One service is open."),
                        raw_capture("capture-h", 8, "A similar service is closed."),
                    ]
                )
                store.add_observations(
                    [
                        observation("capture-g", "service_gamma", "status", "open"),
                        observation("capture-h", "service_gamma", "status", "closed"),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships(
                    [
                        {
                            "source_event_id": "capture-h",
                            "target_event_id": "capture-g",
                            "relation_type": "similar_not_duplicate",
                        }
                    ],
                    "neutral-fixture-extractor",
                )

                store.rebuild_projection(duplicate_evidence=True)
                snapshot = store.snapshot()
                self.assertEqual(snapshot["duplicate_components"], [])
                fact = next(item for item in snapshot["current_facts"] if item["predicate"] == "status")
                self.assertEqual(fact["value"], "closed")

    def test_meaningful_change_is_not_consolidated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-i", 9, "The service costs 20."),
                        raw_capture("capture-j", 10, "The service now costs 25."),
                    ]
                )
                store.add_observations(
                    [
                        observation("capture-i", "service_gamma", "amount", 20),
                        observation("capture-j", "service_gamma", "amount", 25),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships(
                    [
                        {
                            "source_event_id": "capture-j",
                            "target_event_id": "capture-i",
                            "relation_type": "meaningful_change",
                            "changed_fields": ["amount"],
                        }
                    ],
                    "neutral-fixture-extractor",
                )

                store.rebuild_projection(duplicate_evidence=True)
                snapshot = store.snapshot()
                self.assertEqual(snapshot["duplicate_components"], [])
                fact = next(item for item in snapshot["current_facts"] if item["predicate"] == "amount")
                self.assertEqual(fact["value"], 25)

    def test_duplicate_chain_has_one_stable_component(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-k", 11, "The task is open."),
                        raw_capture("capture-l", 12, "The same task is open."),
                        raw_capture("capture-m", 13, "Another copy confirms the task is open."),
                    ]
                )
                store.add_observations(
                    [
                        observation("capture-k", "task_delta", "status", "open"),
                        observation("capture-l", "task_delta", "status", "open", operation="duplicate"),
                        observation("capture-m", "task_delta", "status", "open", operation="duplicate"),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships(
                    [
                        duplicate("capture-l", "capture-k", "normalized_duplicate"),
                        duplicate("capture-m", "capture-l", "duplicate"),
                    ],
                    "neutral-fixture-extractor",
                )

                store.rebuild_projection(duplicate_evidence=True)
                snapshot = store.snapshot()
                self.assertEqual(len(snapshot["duplicate_components"]), 1)
                component = snapshot["duplicate_components"][0]
                self.assertEqual(component["canonical_event_id"], "capture-k")
                self.assertEqual(component["member_event_ids"], ["capture-k", "capture-l", "capture-m"])
                fact = next(item for item in snapshot["current_facts"] if item["predicate"] == "status")
                self.assertEqual(set(fact["source_refs"]), {"capture-k", "capture-l", "capture-m"})

                first_projection = (snapshot["current_facts"], snapshot["duplicate_components"])
                store.rebuild_projection(duplicate_evidence=True)
                second_snapshot = store.snapshot()
                self.assertEqual(
                    first_projection,
                    (second_snapshot["current_facts"], second_snapshot["duplicate_components"]),
                )

    def test_unknown_duplicate_evidence_is_not_upgraded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-n", 14, "The amount could not be read."),
                        raw_capture("capture-o", 15, "A duplicate capture reports an amount."),
                    ]
                )
                store.add_observations(
                    [
                        observation(
                            "capture-n",
                            "merchant_alpha",
                            "amount",
                            "unreadable",
                            knowledge_status="unknown",
                        ),
                        observation("capture-o", "merchant_alpha", "amount", 30, operation="duplicate"),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships([duplicate("capture-o", "capture-n")], "neutral-fixture-extractor")

                store.rebuild_projection(duplicate_evidence=True)
                fact = next(item for item in store.snapshot()["current_facts"] if item["predicate"] == "amount")
                self.assertEqual(fact["knowledge_status"], "unknown")
                self.assertNotIn("value", fact)

    def test_explicit_correction_resolves_duplicate_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with StateStore(Path(directory) / "state.sqlite") as store:
                store.insert_raw_events(
                    [
                        raw_capture("capture-p", 16, "The amount is 20."),
                        raw_capture("capture-q", 17, "A corrected duplicate says 25."),
                    ]
                )
                store.add_observations(
                    [
                        observation("capture-p", "merchant_alpha", "amount", 20),
                        observation(
                            "capture-q",
                            "merchant_alpha",
                            "amount",
                            25,
                            operation="correction",
                            supersedes_event_id="capture-p",
                        ),
                    ],
                    "neutral-fixture-extractor",
                )
                store.add_relationships([duplicate("capture-q", "capture-p")], "neutral-fixture-extractor")

                store.rebuild_projection(duplicate_evidence=True)
                fact = next(item for item in store.snapshot()["current_facts"] if item["predicate"] == "amount")
                self.assertEqual(fact["knowledge_status"], "known")
                self.assertEqual(fact["value"], 25)


if __name__ == "__main__":
    unittest.main()
