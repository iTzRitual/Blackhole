"""Score a labeled development prefix with the unchanged deterministic scorer.

This wrapper does not alter ``eval.score``. It creates an in-memory prefix view
of the public scenario, expected output, and candidate, then delegates all
semantic scoring to the frozen evaluator. It is intended for FAST DEV
diagnostics only, never for holdout material or the official 200-event score.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from eval.score import load_json, score


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "benchmark" / "dev" / "response-contract-v2.json"


def score_slice(
    scenario: dict[str, Any],
    expected: dict[str, Any],
    candidate: dict[str, Any],
    response_contract: dict[str, Any],
    *,
    checkpoint: int,
    query_ids: list[str],
) -> dict[str, Any]:
    """Score one public prefix and selected public queries deterministically."""

    scenario_view = copy.deepcopy(scenario)
    expected_view = copy.deepcopy(expected)
    candidate_view = copy.deepcopy(candidate)
    checkpoint_key = str(checkpoint)
    scenario_view["raw_events"] = scenario_view.get("raw_events", [])[:checkpoint]
    scenario_view["checkpoints"] = [checkpoint]
    expected_view["event_count"] = checkpoint
    expected_view["raw_event_hashes"] = {
        event["event_id"]: event.get("payload_sha256")
        for event in scenario_view["raw_events"]
    }
    expected_checkpoint = expected_view.get("checkpoints", {}).get(checkpoint_key, {})
    if isinstance(expected_checkpoint, dict) and "queries" in expected_checkpoint:
        expected_queries = expected_checkpoint["queries"]
    else:
        expected_queries = expected_checkpoint if isinstance(expected_checkpoint, dict) else {}
    expected_view["checkpoints"] = {
        checkpoint_key: {
            "checkpoint": checkpoint,
            "queries": {query_id: expected_queries[query_id] for query_id in query_ids if query_id in expected_queries},
        }
    }
    candidate_checkpoint = candidate_view.get("checkpoints", {}).get(checkpoint_key, {})
    candidate_queries = candidate_checkpoint.get("queries", {}) if isinstance(candidate_checkpoint, dict) else {}
    candidate_view["checkpoints"] = {
        checkpoint_key: {
            "checkpoint": checkpoint,
            "queries": {query_id: candidate_queries[query_id] for query_id in query_ids if query_id in candidate_queries},
        }
    }
    result = score(scenario_view, expected_view, candidate_view, response_contract)
    result["slice"] = {
        "label": "DEV FAST / NOT OFFICIAL SCORE",
        "checkpoint": checkpoint,
        "event_count": checkpoint,
        "query_ids": query_ids,
        "official": False,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--response-contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checkpoint", type=int, default=50)
    parser.add_argument("--query-ids", required=True, help="comma-separated public query IDs")
    args = parser.parse_args()
    query_ids = [item.strip() for item in args.query_ids.split(",") if item.strip()]
    result = score_slice(
        load_json(args.scenario),
        load_json(args.expected),
        load_json(args.candidate),
        load_json(args.response_contract),
        checkpoint=args.checkpoint,
        query_ids=query_ids,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"lqa_0m": result["primary"]["score"], "dscr": result["dscr"]["count"], "hard_failure": result["hard_failure"], "slice": result["slice"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
