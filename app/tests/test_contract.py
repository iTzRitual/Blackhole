from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.contract import PublicContract


ROOT = Path(__file__).resolve().parents[2]


class PublicContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        document = json.loads((ROOT / "benchmark/dev/response-contract-v2.json").read_text(encoding="utf-8"))
        cls.contract = PublicContract(document)

    def test_aliases_and_values_are_canonicalized(self) -> None:
        item = self.contract.sanitize_assertion(
            {
                "subject": "Streamly subscription",
                "predicate": "monthly cost",
                "knowledge_status": "known",
                "value": {"amount_eur": "12.00", "period": "monthly"},
                "source_refs": ["evt-001", "not-an-event"],
            },
            {"evt-001"},
        )
        self.assertEqual(item["subject"], "streamly")
        self.assertEqual(item["predicate"], "current_price")
        self.assertEqual(item["value"], {"amount": "12", "billing_period": "monthly"})
        self.assertEqual(item["source_refs"], ["evt-001"])

    def test_unknown_assertion_drops_value_and_requires_reason(self) -> None:
        item = self.contract.sanitize_assertion(
            {
                "subject": "Jordan",
                "predicate": "entity link",
                "knowledge_status": "unknown",
                "value": "Jordan Lee",
                "unknown_reason": "ambiguous person",
                "source_refs": ["evt-007"],
            },
            {"evt-007"},
        )
        self.assertEqual(item["knowledge_status"], "unknown")
        self.assertEqual(item["unknown_reason"], "ambiguous_person")
        self.assertNotIn("value", item)

    def test_response_contains_only_requested_queries(self) -> None:
        result = self.contract.sanitize_response(
            {
                "queries": {
                    "q-one": {"assertions": [{"subject": "scenario", "predicate": "status", "knowledge_status": "known", "value": "ready", "source_refs": ["evt-001"]}]},
                    "q-extra": {"assertions": []},
                }
            },
            scenario_id="scenario-1",
            checkpoint=1,
            query_ids=["q-one", "q-two"],
            event_ids={"evt-001"},
        )
        self.assertEqual(list(result["queries"]), ["q-one", "q-two"])
        self.assertEqual(result["queries"]["q-two"], {"assertions": []})


if __name__ == "__main__":
    unittest.main()
