"""Shared public-contract normalization for semantic ingestion.

The benchmark runner and the deferred product runtime use the same boundary:
providers propose public observations and relationships, then deterministic
normalization validates event scope, ontology identity, values, and provenance.
This module intentionally does not import benchmark expected output or an
evaluator.
"""

from __future__ import annotations

from typing import Any

from app.contract import (
    PublicContract,
    canonical_predicate,
    canonical_subject,
    canonical_unknown_reason,
    canonical_value,
    normalize_text,
)


def normalize_observation(
    item: Any,
    *,
    public_contract: PublicContract,
    batch_event_ids: set[str],
    available_event_ids: set[str],
) -> dict[str, Any] | None:
    """Normalize one provider observation into the StateStore input shape."""

    if not isinstance(item, dict):
        return None
    event_id = item.get("event_id")
    if not isinstance(event_id, str) or event_id not in batch_event_ids:
        return None
    subject = canonical_subject(item.get("subject"), public_contract.document)
    predicate = canonical_predicate(item.get("predicate"), public_contract.document)
    status = normalize_text(item.get("knowledge_status", "")) if isinstance(item.get("knowledge_status"), str) else ""
    if subject is None or predicate is None or status not in {"known", "inferred", "unknown"}:
        return None
    refs_value = item.get("source_refs", [event_id])
    refs = sorted({ref for ref in refs_value if isinstance(ref, str) and ref in available_event_ids}) if isinstance(refs_value, list) else []
    if event_id not in refs:
        refs.append(event_id)
        refs.sort()
    result: dict[str, Any] = {
        "event_id": event_id,
        "subject": subject,
        "predicate": predicate,
        "knowledge_status": status,
        "operation": normalize_text(item.get("operation", "set")) if isinstance(item.get("operation", "set"), str) else "set",
        "source_refs": refs,
    }
    if result["operation"] not in {"set", "supersede", "correction", "contradiction", "duplicate"}:
        result["operation"] = "set"
    if status == "unknown":
        if "unknown_reason" not in item:
            return None
        result["unknown_reason"] = canonical_unknown_reason(item["unknown_reason"], public_contract.document)
    else:
        if "value" not in item:
            return None
        result["value"] = canonical_value(item["value"], public_contract.document, predicate)
    supersedes = item.get("supersedes_event_id")
    if isinstance(supersedes, str) and supersedes in available_event_ids:
        result["supersedes_event_id"] = supersedes
    return result


def normalize_relationship(
    item: Any,
    *,
    public_contract: PublicContract,
    batch_event_ids: set[str],
    available_event_ids: set[str],
) -> dict[str, Any] | None:
    """Normalize one provider relationship into the StateStore input shape."""

    if not isinstance(item, dict):
        return None
    source = item.get("source_event_id")
    target = item.get("target_event_id")
    relation_type = item.get("relation_type")
    if not isinstance(source, str) or source not in batch_event_ids or not isinstance(relation_type, str):
        return None
    if not isinstance(target, str) or target not in available_event_ids:
        target = None
    changed_fields = item.get("changed_fields", [])
    if not isinstance(changed_fields, list):
        changed_fields = []
    result: dict[str, Any] = {
        "source_event_id": source,
        "target_event_id": target,
        "relation_type": normalize_text(relation_type).replace(" ", "_"),
        "changed_fields": [str(value) for value in changed_fields if isinstance(value, str)],
    }
    if isinstance(item.get("duplicate_group"), str):
        result["duplicate_group"] = item["duplicate_group"]
    if isinstance(item.get("note"), str):
        result["note"] = item["note"]
    return result


def normalize_extraction(
    parsed: Any,
    *,
    public_contract: PublicContract,
    batch_event_ids: set[str],
    available_event_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize a provider extraction response without expected-output access."""

    if not isinstance(parsed, dict):
        return [], []
    raw_observations = parsed.get("observations", [])
    raw_relationships = parsed.get("relationships", [])
    observations = [
        normalized
        for item in raw_observations if isinstance(raw_observations, list)
        for normalized in [
            normalize_observation(
                item,
                public_contract=public_contract,
                batch_event_ids=batch_event_ids,
                available_event_ids=available_event_ids,
            )
        ]
        if normalized is not None
    ]
    relationships = [
        normalized
        for item in raw_relationships if isinstance(raw_relationships, list)
        for normalized in [
            normalize_relationship(
                item,
                public_contract=public_contract,
                batch_event_ids=batch_event_ids,
                available_event_ids=available_event_ids,
            )
        ]
        if normalized is not None
    ]
    return observations, relationships


__all__ = ["normalize_extraction", "normalize_observation", "normalize_relationship"]
