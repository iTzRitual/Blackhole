from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.response_projector import ResponseProjector


ROOT = Path(__file__).resolve().parents[2]


class ResponseProjectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        contract = json.loads((ROOT / "benchmark/dev/response-contract-v2.json").read_text(encoding="utf-8"))
        query_bundle = json.loads((ROOT / "benchmark/dev/query-bundle-v2.json").read_text(encoding="utf-8"))
        cls.projector = ResponseProjector(contract, query_bundle)

    def test_price_change_relation_promotes_new_price_and_decomposes_fields(self) -> None:
        snapshot = {
            "current_facts": [
                {"subject": "streamly", "predicate": "status", "knowledge_status": "known", "value": "active", "source_refs": ["evt-001"]},
                {"subject": "streamly", "predicate": "current_price", "knowledge_status": "known", "value": {"amount": "12", "currency": "EUR", "billing_period": "month"}, "source_refs": ["evt-001"]},
            ],
            "history": [
                {"event_id": "evt-001", "subject": "streamly", "predicate": "current_price", "knowledge_status": "known", "value": {"amount": "12", "currency": "EUR", "billing_period": "month"}, "source_refs": ["evt-001"]},
                {"event_id": "evt-021", "subject": "streamly", "predicate": "historical_price", "knowledge_status": "known", "value": {"amount": "14", "currency": "EUR", "billing_period": "month"}, "source_refs": ["evt-021"]},
            ],
            "relationships": [{"source_event_id": "evt-021", "target_event_id": "evt-001", "relation_type": "meaningful_change", "changed_fields": ["current_price"]}],
        }
        current = self.projector.project(snapshot, query_ids=["q-subscriptions-current"])["q-subscriptions-current"]["assertions"]
        values = {(item["predicate"], json.dumps(item.get("value"), sort_keys=True)) for item in current}
        self.assertIn(("current_price", json.dumps({"amount": "14", "currency": "EUR", "billing_period": "month"}, sort_keys=True)), values)
        self.assertIn(("currency", json.dumps("EUR")), values)
        self.assertIn(("billing_period", json.dumps("month")), values)

    def test_duplicate_group_count_uses_components_without_group_labels(self) -> None:
        snapshot = {
            "current_facts": [],
            "history": [],
            "relationships": [
                {"source_event_id": "evt-002", "target_event_id": "evt-001", "relation_type": "exact_duplicate", "changed_fields": []},
                {"source_event_id": "evt-004", "target_event_id": "evt-003", "relation_type": "normalized_duplicate", "changed_fields": []},
                {"source_event_id": "evt-005", "target_event_id": "evt-001", "relation_type": "meaningful_change", "changed_fields": ["amount"]},
            ],
        }
        assertions = self.projector.project(snapshot, query_ids=["q-duplicates-changes"])["q-duplicates-changes"]["assertions"]
        counts = {item["predicate"]: item["value"] for item in assertions if item["subject"] == "scenario"}
        self.assertEqual(counts["duplicate_event_count"], 2)
        self.assertEqual(counts["duplicate_group_count"], 2)
        self.assertEqual(counts["meaningful_change_event_count"], 1)


if __name__ == "__main__":
    unittest.main()
