from __future__ import annotations

import copy
import unittest

from benchmark.dev.generate_benchmark import build_outputs
from eval.score import load_json
from eval.score_slice import score_slice


class ScoreSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scenario, cls.expected = build_outputs()
        cls.contract = load_json("benchmark/dev/response-contract-v2.json")

    def test_prefix_view_can_score_a_perfect_selected_candidate(self) -> None:
        query_ids = ["q-subscriptions-current", "q-tasks-state"]
        candidate = {
            "response_contract": self.scenario["response_contract"],
            "scenario_id": self.scenario["scenario_id"],
            "checkpoints": {
                "50": {
                    "checkpoint": 50,
                    "queries": {
                        query_id: {
                            "assertions": [
                                {key: copy.deepcopy(value) for key, value in assertion.items() if key != "state_key"}
                                for assertion in self.expected["checkpoints"]["50"][query_id]["assertions"]
                            ]
                        }
                        for query_id in query_ids
                    },
                }
            },
        }
        result = score_slice(
            self.scenario,
            self.expected,
            candidate,
            self.contract,
            checkpoint=50,
            query_ids=query_ids,
        )
        self.assertEqual(result["primary"]["score"], 1.0)
        self.assertEqual(result["dscr"]["count"], 0)
        self.assertTrue(result["source_integrity"]["valid"])
        self.assertFalse(result["hard_failure"])


if __name__ == "__main__":
    unittest.main()
