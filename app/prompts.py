"""Prompt construction for Experiment 001's scoped semantic calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "runtime" / "advanced-e001-v1.md"


def base_instruction() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def extraction_contract(contract: dict[str, Any]) -> dict[str, Any]:
    """Keep extraction calls focused on public ontology, not evaluator detail."""

    return {
        "response_contract": contract.get("response_contract"),
        "public_ontology": contract.get("public_ontology", {}),
        "unknown_reason": contract.get("unknown_reason", {}),
        "predicate_value_shapes": contract.get("predicate_value_shapes", {}),
        "value_normalization": {
            "enum_field_aliases": contract.get("value_normalization", {}).get("enum_field_aliases", {}),
            "object_field_aliases": contract.get("value_normalization", {}).get("object_field_aliases", {}),
        },
    }


def extraction_prompt(
    *,
    events: list[dict[str, Any]],
    contract: dict[str, Any],
    prior_snapshot: dict[str, Any],
) -> str:
    return (
        base_instruction()
        + "\n\nTASK: semantic extraction for the new chronological capture batch.\n"
        "Read only the captures in this batch as source evidence. The prior "
        "projection is a hint for linking and supersession, not an oracle. "
        "Return one JSON object with `observations` and `relationships`; do not "
        "answer any user query.\n\n"
        "PUBLIC RESPONSE CONTRACT (ontology only):\n"
        + json.dumps(extraction_contract(contract), ensure_ascii=False, indent=2)
        + "\n\nPRIOR DETERMINISTIC PROJECTION:\n"
        + json.dumps(prior_snapshot, ensure_ascii=False, indent=2)
        + "\n\nNEW CAPTURES:\n"
        + json.dumps(events, ensure_ascii=False, indent=2)
    )


def query_prompt(
    *,
    contract: dict[str, Any],
    query_bundle: dict[str, Any],
    scenario_id: str,
    checkpoint: int,
    query_ids: list[str],
    snapshot: dict[str, Any],
) -> str:
    selected_queries = {
        query_id: query_bundle.get("queries", {}).get(query_id)
        for query_id in query_ids
        if query_id in query_bundle.get("queries", {})
    }
    return (
        base_instruction()
        + "\n\nTASK: project the deterministic Blackhole state into a checkpoint response.\n"
        "This is a fresh scoped call. Use the supplied state and query questions, "
        "not a persistent conversation. Return exactly one JSON object with the "
        "v2 envelope and every supplied query exactly once.\n\n"
        "PUBLIC RESPONSE CONTRACT:\n"
        + json.dumps(contract, ensure_ascii=False, indent=2)
        + "\n\nQUERY BUNDLE:\n"
        + json.dumps(
            {
                "scenario_id": scenario_id,
                "checkpoint": checkpoint,
                "response_contract": query_bundle.get("response_contract"),
                "queries": selected_queries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n\nDETERMINISTIC PROJECTED STATE:\n"
        + json.dumps(snapshot, ensure_ascii=False, indent=2)
    )
