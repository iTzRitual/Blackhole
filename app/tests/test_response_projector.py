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

    def test_entity_link_only_edges_are_not_capture_duplicate_evidence(self) -> None:
        snapshot = {
            "current_facts": [],
            "history": [
                {"event_id": "evt-link-1", "subject": "capture:evt-link-1", "predicate": "entity_link"},
                {"event_id": "evt-link-2", "subject": "capture:evt-link-2", "predicate": "entity_link"},
            ],
            "relationships": [
                {"source_event_id": "evt-link-2", "target_event_id": "evt-link-1", "relation_type": "exact_duplicate"}
            ],
        }
        assertions = self.projector.project(snapshot, query_ids=["q-duplicates-changes"])["q-duplicates-changes"]["assertions"]
        counts = {item["predicate"]: item["value"] for item in assertions if item["subject"] == "scenario"}
        self.assertEqual(counts["duplicate_event_count"], 0)
        self.assertEqual(counts["duplicate_group_count"], 0)

    def test_subscription_projection_uses_public_kind_not_subject_name(self) -> None:
        projector = ResponseProjector(
            {"public_ontology": {"subjects": [{"id": "alpha_plan", "kind": "subscription"}]}},
            {"queries": {"active": {"question": "Which subscriptions are currently active?"}}},
        )
        snapshot = {
            "current_facts": [
                {
                    "subject": "alpha_plan",
                    "predicate": "status",
                    "knowledge_status": "known",
                    "value": "active",
                    "source_refs": ["evt-001"],
                },
                {
                    "subject": "alpha_plan",
                    "predicate": "current_price",
                    "knowledge_status": "known",
                    "value": {"amount": "8", "currency": "EUR", "billing_period": "month"},
                    "source_refs": ["evt-001"],
                },
            ],
            "history": [],
        }
        assertions = projector.project(snapshot, query_ids=["active"])["active"]["assertions"]
        self.assertEqual({item["subject"] for item in assertions}, {"alpha_plan"})
        self.assertIn("current_price", {item["predicate"] for item in assertions})

    def test_recent_changes_support_generic_insurance_contract_and_observation_subjects(self) -> None:
        projector = ResponseProjector(
            {
                "public_ontology": {
                    "subjects": [
                        {"id": "alpha_observation", "kind": "observation"},
                        {"id": "alpha_insurance", "kind": "insurance"},
                        {"id": "alpha_contract", "kind": "contract"},
                    ]
                }
            },
            {"queries": {"changes": {"question": "Which corrections, contradictions, replacements, and material changes are recorded?"}}},
        )
        snapshot = {
            "current_facts": [],
            "history": [
                {"event_id": "evt-001", "sequence": 1, "subject": "alpha_observation", "predicate": "deadline", "knowledge_status": "known", "value": "2026-01-01", "operation": "set"},
                {"event_id": "evt-002", "sequence": 2, "subject": "alpha_observation", "predicate": "deadline", "knowledge_status": "known", "value": "2026-01-02", "operation": "contradiction"},
                {"event_id": "evt-003", "sequence": 3, "subject": "alpha_insurance", "predicate": "policy_id", "knowledge_status": "known", "value": "P-1", "operation": "set"},
                {"event_id": "evt-003", "sequence": 3, "subject": "alpha_insurance", "predicate": "effective_date", "knowledge_status": "known", "value": "2026-01-01", "operation": "set"},
                {"event_id": "evt-004", "sequence": 4, "subject": "alpha_insurance", "predicate": "policy_id", "knowledge_status": "known", "value": "P-2", "operation": "set"},
                {"event_id": "evt-004", "sequence": 4, "subject": "alpha_insurance", "predicate": "effective_date", "knowledge_status": "known", "value": "2026-02-01", "operation": "set"},
                {"event_id": "evt-005", "sequence": 5, "subject": "alpha_contract", "predicate": "executed", "knowledge_status": "known", "value": False, "operation": "set"},
                {"event_id": "evt-006", "sequence": 6, "subject": "alpha_contract", "predicate": "executed", "knowledge_status": "known", "value": True, "operation": "set"},
                {"event_id": "evt-006", "sequence": 6, "subject": "alpha_contract", "predicate": "status", "knowledge_status": "known", "value": "signed", "operation": "set"},
            ],
        }
        assertions = projector.project(snapshot, query_ids=["changes"])["changes"]["assertions"]
        relation_types = {item["value"]["relation_type"] for item in assertions}
        self.assertEqual(relation_types, {"contradiction", "policy_replacement", "contract_replacement"})


if __name__ == "__main__":
    unittest.main()
