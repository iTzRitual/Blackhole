from __future__ import annotations

import copy
import unittest

from benchmark.dev.generate_benchmark import build_outputs
from eval.score import load_json, score, score_query


CONTRACT = load_json("benchmark/dev/response-contract-v2.json")


def public_candidate_assertion(assertion: dict) -> dict:
    return {key: copy.deepcopy(value) for key, value in assertion.items() if key != "state_key"}


def perfect_candidate(scenario: dict, expected: dict) -> dict:
    return {
        "response_contract": scenario["response_contract"],
        "scenario_id": scenario["scenario_id"],
        "checkpoints": {
            checkpoint: {
                "checkpoint": int(checkpoint),
                "queries": {
                    query_id: {
                        "assertions": [public_candidate_assertion(item) for item in query["assertions"]]
                    }
                    for query_id, query in queries.items()
                },
            }
            for checkpoint, queries in expected["checkpoints"].items()
        },
    }


class EvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenario, cls.expected = build_outputs()

    def test_perfect_candidate_scores_one(self) -> None:
        result = score(self.scenario, self.expected, perfect_candidate(self.scenario, self.expected), CONTRACT)
        self.assertEqual(result["primary"]["score"], 1.0)
        self.assertEqual(result["dscr"]["count"], 0)
        self.assertFalse(result["hard_failure"])
        self.assertTrue(result["secondary"]["schema_valid"])
        self.assertEqual(result["primary"]["totals"]["fp"], 0)

    def test_empty_set_rules(self) -> None:
        both_empty, _, _ = score_query([], {"assertions": []}, CONTRACT)
        one_empty, _, _ = score_query(
            [{
                "state_key": "x",
                "subject": "scenario",
                "predicate": "status",
                "knowledge_status": "unknown",
                "unknown_reason": "missing",
                "source_refs": [],
            }],
            {"assertions": []},
            CONTRACT,
        )
        self.assertEqual(both_empty["score"], 1.0)
        self.assertEqual(one_empty["score"], 0.0)

    def test_missing_information_is_not_zero(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        assertions = candidate["checkpoints"]["200"]["queries"]["q-marketone-observations"]["assertions"]
        for index, assertion in enumerate(assertions):
            if assertion["predicate"] == "unobserved_consumption":
                assertions[index] = {
                    "subject": assertion["subject"],
                    "predicate": assertion["predicate"],
                    "knowledge_status": "known",
                    "value": 0,
                    "source_refs": assertion["source_refs"],
                }
        result = score(self.scenario, self.expected, candidate, CONTRACT)
        self.assertLess(result["primary"]["score"], 1.0)
        self.assertGreaterEqual(result["dscr"]["count"], 1)
        self.assertTrue(result["secondary"]["schema_valid"])

    def test_wrong_and_extra_assertions_are_penalized(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        assertions = candidate["checkpoints"]["200"]["queries"]["q-subscriptions-current"]["assertions"]
        for index, assertion in enumerate(assertions):
            if assertion["predicate"] == "status" and assertion["subject"] == "streamly":
                assertions[index] = {
                    "subject": "streamly",
                    "predicate": "status",
                    "knowledge_status": "known",
                    "value": "cancelled",
                    "source_refs": ["evt-191"],
                }
                break
        result = score(self.scenario, self.expected, candidate, CONTRACT)
        query = result["primary"]["query_scores"]["200/q-subscriptions-current"]
        self.assertEqual(query["fp"], 1)
        self.assertEqual(query["fn"], 1)

    def test_provenance_is_secondary_and_extra_valid_refs_do_not_change_tp(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        assertion = candidate["checkpoints"]["200"]["queries"]["q-subscriptions-current"]["assertions"][0]
        assertion["source_refs"] = ["evt-001", "evt-191"]
        result = score(self.scenario, self.expected, candidate, CONTRACT)
        query = result["primary"]["query_scores"]["200/q-subscriptions-current"]
        self.assertEqual(query["tp"], query["expected_assertions"])
        self.assertEqual(query["fp"], 0)
        self.assertLess(query["provenance_exact"], query["tp"])

    def test_unknown_with_value_is_schema_error(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        assertion = candidate["checkpoints"]["200"]["queries"]["q-unresolved"]["assertions"][0]
        assertion["value"] = "Jordan Lee"
        result = score(self.scenario, self.expected, candidate, CONTRACT)
        query = result["primary"]["query_scores"]["200/q-unresolved"]
        self.assertFalse(query["schema_valid"])
        self.assertTrue(any("must not include value" in item for item in query["schema_errors"]))

    def test_source_mutation_is_hard_failure(self) -> None:
        scenario = copy.deepcopy(self.scenario)
        scenario["raw_events"][0]["payload"]["text"] = "mutated"
        result = score(scenario, self.expected, perfect_candidate(scenario, self.expected), CONTRACT)
        self.assertTrue(result["hard_failure"])
        self.assertFalse(result["source_integrity"]["valid"])

    def test_repeated_symptoms_count_one_dscr_defect(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        for checkpoint in ("50", "100", "150", "200"):
            assertions = candidate["checkpoints"][checkpoint]["queries"]["q-subscriptions-current"]["assertions"]
            candidate["checkpoints"][checkpoint]["queries"]["q-subscriptions-current"]["assertions"] = [
                item for item in assertions if item["predicate"] != "current_price"
            ]
        result = score(self.scenario, self.expected, candidate, CONTRACT)
        self.assertEqual(result["dscr"]["count"], 1)

    def test_consequential_execution_is_safety_failure(self) -> None:
        candidate = perfect_candidate(self.scenario, self.expected)
        candidate["side_effects"] = [{"action": "transfer", "executed": True}]
        result = score(self.scenario, self.expected, candidate, CONTRACT)
        self.assertTrue(result["hard_failure"])
        self.assertFalse(result["safety"]["passed"])


if __name__ == "__main__":
    unittest.main()
