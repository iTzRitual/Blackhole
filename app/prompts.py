"""Prompt construction for scoped semantic calls.

The benchmark prompt helpers below remain compatibility surfaces for the frozen
V1 runtime.  Product V2 uses the compact instruction separately so ordinary
dogfood calls do not carry benchmark-oriented prompt context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "runtime" / "advanced-e001-v1.md"

PRODUCT_V2_EXTRACTION_INSTRUCTION = """You are Blackhole's Product V2 semantic interpreter.
Treat each supplied capture as immutable evidence. Extract only supported,
open-world observations; never answer a question, invent a value, or make a
guess look known. Return the strict JSON object required by the schema. Put
facts in facts (or observations), links in relationships, and explicit tasks,
deadlines, appointments, or reminders in attention. Every item must reference
its supplied event_id. Use known, inferred, or unknown deliberately; preserve
uncertainty, negation, attribution, contradiction, correction, duplicate, and
meaningful change when the evidence supports them. A correction preserves the
old evidence and only supersedes the grounded competing claim. Preserve useful
entity identity across languages with a stable entity key and a source label.
For a document or image, extract a useful generic identity only when it is
actually visible: document kind, visible reference, issuer or sender,
recipient, service/product/subject, amount and currency, issue or due date,
payment/status, and relevant account or reference. Use one stable document
entity key and a human-readable label for related fields (for example,
"Invoice · REF-123"); keep role labels as concepts or values rather than
separate primary entities. If a field is not readable or not stated, mark it
unknown or the attachment unreadable instead of guessing. Preserve the image
or document source provenance.
When a capture explicitly reports that an open actionable item was completed,
paid, cancelled, rescheduled, or superseded, propose a lifecycle_key and
lifecycle_action and link the related_event_id or supersedes_event_id when
the evidence identifies it. These are proposals only; do not invent a link
from a weak title match and do not claim physical-world proof beyond what the
capture says.
For relative or weekday time, emit structured fields and let the runtime
normalize them from that event's captured_at and timezone; never use the later
processing clock. Preserve coarse or ambiguous dates without fabricating an
exact timestamp. Keep source_refs on claims. Attachments may be marked read
only when the local provider actually read them; otherwise report unsupported
or unreadable. For extraction, answer must be null, source_refs and
evidence_ids must be empty arrays. Do not return extra keys."""


def product_v2_extraction_instruction() -> str:
    """Return the versioned compact Product V2 extraction instruction."""

    return PRODUCT_V2_EXTRACTION_INSTRUCTION


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
