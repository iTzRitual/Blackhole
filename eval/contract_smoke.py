"""Run a non-scored response-contract-v2 parser/canonicalizer smoke test.

The smoke fixture is intentionally separate from the 200-event development
case. It exercises raw model text parsing, public semantic canonicalization,
unknown-without-value validation, temporal values, duplicate counting, and a
task lifecycle without using benchmark ground truth.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baseline.run_baseline import parse_json_document
from eval.score import canonical_json, load_json, score


CONTRACT_PATH = ROOT / "benchmark" / "dev" / "response-contract-v2.json"
RESULT_PATH = ROOT / "eval" / "results" / "contract-smoke.json"


def smoke_contract() -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    contract["public_ontology"]["subjects"].extend([
        {"id": "cloudbox", "kind": "subscription", "aliases": ["CloudBox", "cloud box"]},
    ])
    return contract


def smoke_events() -> list[dict[str, Any]]:
    payloads = [
        {"text": "CloudBox subscription is 9.00 EUR per month."},
        {"text": "CloudBox subscription price changed to 11.00 EUR per month."},
        {"text": "CloudBox subscription price changed to 11.00 EUR per month."},
        {"text": "Return the library book by 2026-09-10."},
        {"text": "The library book was returned. No MarketOne consumption observation was recorded."},
    ]
    events: list[dict[str, Any]] = []
    for index, payload in enumerate(payloads, start=1):
        event_id = f"evt-{index:03d}"
        events.append({
            "event_id": event_id,
            "captured_at": f"2026-09-{index:02d}T09:00:00+02:00",
            "payload": payload,
            "payload_sha256": hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        })
    return events


def smoke_expected(events: list[dict[str, Any]]) -> dict[str, Any]:
    refs = [event["event_id"] for event in events]
    return {
        "response_contract": "response-contract-v2",
        "contract_version": "smoke-contract-v1",
        "scenario_id": "response-contract-smoke",
        "event_count": len(events),
        "raw_event_hashes": {event["event_id"]: event["payload_sha256"] for event in events},
        "checkpoints": {
            "5": {
                "q-smoke": {
                    "assertions": [
                        {
                            "state_key": "smoke:cloudbox/current_price",
                            "subject": "cloudbox",
                            "predicate": "current_price",
                            "knowledge_status": "known",
                            "value": {"amount": "11.00", "currency": "EUR", "billing_period": "month"},
                            "source_refs": ["evt-002"],
                        },
                        {
                            "state_key": "smoke:cloudbox/historical_price",
                            "subject": "cloudbox",
                            "predicate": "historical_price",
                            "knowledge_status": "known",
                            "value": {"amount": "9.00", "currency": "EUR", "billing_period": "month"},
                            "source_refs": ["evt-001"],
                        },
                        {
                            "state_key": "smoke:library-return/status",
                            "subject": "library_return_1",
                            "predicate": "status",
                            "knowledge_status": "known",
                            "value": "completed",
                            "source_refs": ["evt-004", "evt-005"],
                        },
                        {
                            "state_key": "smoke:scenario/duplicate_event_count",
                            "subject": "scenario",
                            "predicate": "duplicate_event_count",
                            "knowledge_status": "known",
                            "value": 1,
                            "source_refs": ["evt-003"],
                        },
                        {
                            "state_key": "smoke:capture-003/relationship",
                            "subject": "capture:evt-003",
                            "predicate": "relationship",
                            "knowledge_status": "known",
                            "value": {
                                "relation_type": "exact_duplicate",
                                "source_event_id": "evt-003",
                                "target_event_id": "evt-002",
                            },
                            "source_refs": ["evt-002", "evt-003"],
                        },
                        {
                            "state_key": "smoke:marketone/unobserved_consumption",
                            "subject": "marketone",
                            "predicate": "unobserved_consumption",
                            "knowledge_status": "unknown",
                            "unknown_reason": "no_consumption_observation",
                            "source_refs": ["evt-005"],
                        },
                    ]
                }
            }
        },
        "defect_catalog": [],
    }


def correct_model_text() -> str:
    return """```json
{
  "response_contract": "response-contract-v2",
  "scenario_id": "response-contract-smoke",
  "checkpoint": 5,
  "queries": {
    "q-smoke": {
      "assertions": [
        {"subject": "CloudBox", "predicate": "current cost", "knowledge_status": "known", "value": {"amount_eur": "11.0", "currency_code": "EUR", "period": "month"}, "source_refs": ["evt-002"]},
        {"subject": "cloud box", "predicate": "price history", "knowledge_status": "known", "value": {"amount_eur": 9, "currency": "eur", "billing_period": "month"}, "source_refs": ["evt-001"]},
        {"subject": "library return", "predicate": "lifecycle", "knowledge_status": "known", "value": "COMPLETED", "source_refs": ["evt-004", "evt-005"]},
        {"subject": "timeline", "predicate": "duplicate capture count", "knowledge_status": "known", "value": 1, "source_refs": ["evt-003"]},
        {"subject": "evt_003", "predicate": "relation", "knowledge_status": "known", "value": {"relation": "exact duplicate", "source": "evt-003", "target": "evt-002"}, "source_refs": ["evt-002", "evt-003"]},
        {"subject": "MarketOne", "predicate": "unobserved consumption", "knowledge_status": "unknown", "unknown_reason": "No MarketOne consumption observation was recorded.", "source_refs": ["evt-005"]}
      ]
    }
  }
}
```"""


def run_smoke() -> dict[str, Any]:
    contract = smoke_contract()
    events = smoke_events()
    scenario = {
        "response_contract": "response-contract-v2",
        "contract_version": "smoke-contract-v1",
        "scenario_id": "response-contract-smoke",
        "raw_events": events,
        "checkpoints": [5],
    }
    expected = smoke_expected(events)
    parsed, parse_error = parse_json_document(correct_model_text())
    if parsed is None:
        raise AssertionError(f"correct smoke output did not parse: {parse_error}")
    correct = score(scenario, expected, {"response_contract": parsed.get("response_contract"), "scenario_id": parsed.get("scenario_id"), "checkpoints": {"5": {"queries": parsed["queries"]}}}, contract)

    malformed = copy.deepcopy(parsed)
    malformed["queries"]["q-smoke"]["assertions"][-1]["value"] = 0
    malformed_candidate = {
        "response_contract": malformed.get("response_contract"),
        "scenario_id": malformed.get("scenario_id"),
        "checkpoints": {"5": {"queries": malformed["queries"]}},
    }
    malformed_result = score(scenario, expected, malformed_candidate, contract)
    return {
        "status": "non-scored-contract-smoke",
        "parser": {"correct_output_parsed": parse_error is None, "parse_error": parse_error},
        "correct": {
            "semantic_score": correct["primary"]["score"],
            "schema_valid": correct["secondary"]["schema_valid"],
            "totals": correct["primary"]["totals"],
        },
        "malformed": {
            "schema_valid": malformed_result["secondary"]["schema_valid"],
            "schema_errors": malformed_result["secondary"]["schema_errors"],
            "malformed_assertion_count": sum(
                item["malformed_assertions"] for item in malformed_result["primary"]["query_scores"].values()
            ),
        },
    }


def main() -> int:
    result = run_smoke()
    if result["correct"]["semantic_score"] != 1.0 or not result["correct"]["schema_valid"]:
        raise SystemExit(json.dumps(result, indent=2))
    if result["malformed"]["schema_valid"] or result["malformed"]["malformed_assertion_count"] == 0:
        raise SystemExit(json.dumps(result, indent=2))
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
