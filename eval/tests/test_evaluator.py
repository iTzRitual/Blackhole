from __future__ import annotations

import copy
import unittest

from benchmark.dev.generate_benchmark import build_outputs
from eval.score import score, score_query


def perfect_candidate(scenario: dict, expected: dict) -> dict:
    return {
        "contract_version": scenario["contract_version"],
        "scenario_id": scenario["scenario_id"],
        "checkpoints": {
            checkpoint: {
                "checkpoint": int(checkpoint),
                "queries": copy.deepcopy(queries),
            }
            for checkpoint, queries in expected["checkpoints"].items()
        },
    }


class EvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenario, cls.expected = build_outputs()

    def test_perfect_candidate_scores_one(self) -> None:
        result = score(self.scenario, self.expected, perfect_candidate(self.scenario, self.expected))
        self.assertEqual(result["primary"]["score"], 1.0)
        self.assertEqual(result["dscr"]["count"], 0)
        self.assertFalse(result["hard_failure"])
        self.assertTrue(result["secondary"]["schema_valid"])

    def test_empty_set_rules(self) -> None:
        both_empty, _, _ = score_query([], {"assertions": []})
        one_empty, _, _ = score_query([{"state_key": "x", "knowledge_status": "unknown", "unknown_reason": "missing", "source_refs": []}], {"assertions": []})
        self.assertEqual(both_empty["score"], 1.0)
        self.assertEqual(one_empty["score"], 0.0)

    def test_missing_information_is_not_zero(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        assertions = candidate["checkpoints"]["200"]["queries"]["q-marketone-observations"]["assertions"]
        for index, assertion in enumerate(assertions):
            if assertion["state_key"] == "finance:marketone/unobserved_consumption":
                assertions[index] = {
                    "state_key": assertion["state_key"],
                    "knowledge_status": "known",
                    "value": 0,
                    "source_refs": [],
                }
        result = score(self.scenario, self.expected, candidate)
        self.assertLess(result["primary"]["score"], 1.0)
        self.assertGreaterEqual(result["dscr"]["count"], 1)

    def test_wrong_and_extra_assertions_are_penalized(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        assertions = candidate["checkpoints"]["200"]["queries"]["q-subscriptions-current"]["assertions"]
        for index, assertion in enumerate(assertions):
            if assertion["state_key"] == "subscription:streamly/status":
                assertions[index] = {"state_key": "subscription:streamly/status", "knowledge_status": "known", "value": "cancelled", "source_refs": ["evt-200"]}
                break
        result = score(self.scenario, self.expected, candidate)
        query = result["primary"]["query_scores"]["200/q-subscriptions-current"]
        self.assertEqual(query["fp"], 1)
        self.assertEqual(query["fn"], 1)

    def test_source_mutation_is_hard_failure(self) -> None:
        scenario = copy.deepcopy(self.scenario)
        scenario["raw_events"][0]["payload"]["text"] = "mutated"
        result = score(scenario, self.expected, perfect_candidate(scenario, self.expected))
        self.assertTrue(result["hard_failure"])
        self.assertFalse(result["source_integrity"]["valid"])

    def test_repeated_symptoms_count_one_dscr_defect(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        for checkpoint in ("50", "100", "150", "200"):
            assertions = candidate["checkpoints"][checkpoint]["queries"]["q-subscriptions-current"]["assertions"]
            candidate["checkpoints"][checkpoint]["queries"]["q-subscriptions-current"]["assertions"] = [
                item for item in assertions if item["state_key"] != "subscription:streamly/current_price"
            ]
        result = score(self.scenario, self.expected, candidate)
        self.assertEqual(result["dscr"]["count"], 1)

    def test_consequential_execution_is_safety_failure(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        candidate["side_effects"] = [{"action": "transfer", "executed": True}]
        result = score(self.scenario, self.expected, candidate)
        self.assertTrue(result["hard_failure"])
        self.assertFalse(result["safety"]["passed"])


if __name__ == "__main__":
    unittest.main()
