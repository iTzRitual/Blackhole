"""Conservative, deterministic recovery of missing state relationships.

This module is intentionally smaller than semantic relation reconciliation. It
uses only append-only SQLite inputs already accepted by the runner. It does
not read benchmark expectations, query answers, or provider credentials.
Later retrieval-assisted behavior is kept separate so that the deterministic
variant can be evaluated on its own first.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from typing import Any

from app.state_store import canonical_json


DETERMINISTIC_RECOVERY_VERSION = "experiment-003-deterministic-recovery-v1"
_TASK_SOURCE_TYPES = {"task", "task-note", "todo", "reminder"}
_KNOWN_RELATION_TYPES = {
    "exact_duplicate",
    "normalized_duplicate",
    "duplicate",
    "similar_not_duplicate",
    "meaningful_change",
    "contradiction",
    "correction",
}
_RECEIPT_RELATION_TYPES = {
    "exact_duplicate",
    "normalized_duplicate",
    "duplicate",
    "similar_not_duplicate",
    "meaningful_change",
}
_IDENTIFIER_PATTERN = re.compile(r"\b[A-Za-z]{1,12}[-_][A-Za-z0-9]{2,}\b")
_EXACT_MARKERS = ("unchanged", "identical", "same text", "same payload")
_NORMALIZED_MARKERS = ("normalized", "normalised", "same contents")


def _existing_keys(connection: sqlite3.Connection) -> set[tuple[str, str | None, str]]:
    return {
        (str(row["source_event_id"]), row["target_event_id"], str(row["relation_type"]))
        for row in connection.execute(
            "SELECT source_event_id, target_event_id, relation_type FROM relationships"
        ).fetchall()
    }


def _existing_edges(connection: sqlite3.Connection) -> set[tuple[str, str | None]]:
    return {
        (str(row["source_event_id"]), row["target_event_id"])
        for row in connection.execute(
            "SELECT source_event_id, target_event_id FROM relationships"
        ).fetchall()
    }


def _raw_events(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT event_id, sequence, source_type, payload_json, payload_sha256, metadata_json FROM raw_events ORDER BY sequence"
    ).fetchall()


def _payload_text(row: sqlite3.Row) -> str:
    try:
        payload = json.loads(row["payload_json"])
    except (TypeError, json.JSONDecodeError):
        return ""
    if isinstance(payload, dict) and isinstance(payload.get("text"), str):
        return payload["text"]
    return canonical_json(payload)


def _observation_rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT o.event_id, o.subject, o.predicate, o.knowledge_status, o.operation,
               o.supersedes_event_id, r.source_type, r.sequence
        FROM observations o JOIN raw_events r ON r.event_id = o.event_id
        ORDER BY r.sequence, o.observation_id
        """
    ).fetchall()


def _changed_field(predicate: str) -> list[str]:
    """Return a public-neutral field name for a recovered observation delta."""

    return [predicate] if predicate else []


def _candidate(
    source_event_id: str,
    target_event_id: str | None,
    relation_type: str,
    changed_fields: list[str],
    *,
    note: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "source_event_id": source_event_id,
        "target_event_id": target_event_id,
        "relation_type": relation_type,
        "changed_fields": sorted({field for field in changed_fields if field}),
    }
    if note:
        item["note"] = note
    return item


def deterministic_relationships(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Recover only relations with an unambiguous deterministic evidence path.

    Existing semantic relationships win. The function therefore returns only
    missing relationships and is safe to call after every chronological
    extraction batch. Identical raw payloads are considered duplicate evidence
    only when the later event was independently marked as a duplicate by the
    semantic extraction; repeated identical text can otherwise represent a
    second real observation.
    """

    existing = _existing_keys(connection)
    existing_edges = _existing_edges(connection)
    events = _raw_events(connection)
    by_hash: dict[str, list[sqlite3.Row]] = defaultdict(list)
    by_event = {row["event_id"]: row for row in events}
    for row in events:
        by_hash[str(row["payload_sha256"])].append(row)

    recovered: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None, str]] = set()

    def add(item: dict[str, Any]) -> None:
        key = (item["source_event_id"], item.get("target_event_id"), item["relation_type"])
        if item["relation_type"] not in _KNOWN_RELATION_TYPES:
            return
        edge = (item["source_event_id"], item.get("target_event_id"))
        if key in existing or edge in existing_edges or key in seen:
            return
        seen.add(key)
        existing_edges.add(edge)
        recovered.append(item)

    for row in _observation_rows(connection):
        source = str(row["event_id"])
        target = row["supersedes_event_id"]
        if not isinstance(target, str) or target not in by_event:
            continue
        operation = str(row["operation"])
        relation_type = "meaningful_change"
        if operation == "contradiction":
            relation_type = "contradiction"
        elif operation == "correction":
            relation_type = "correction"
        add(
            _candidate(
                source,
                target,
                relation_type,
                _changed_field(str(row["predicate"])),
            )
        )

    duplicate_observations = {
        str(row["event_id"])
        for row in _observation_rows(connection)
        if str(row["operation"]) == "duplicate"
    }
    for payload_hash, rows in by_hash.items():
        del payload_hash
        ordered = sorted(rows, key=lambda row: int(row["sequence"]))
        for source_row in ordered[1:]:
            source = str(source_row["event_id"])
            if source not in duplicate_observations:
                continue
            prior = [row for row in ordered if int(row["sequence"]) < int(source_row["sequence"])]
            if prior:
                add(_candidate(source, str(prior[-1]["event_id"]), "exact_duplicate", []))

    # A task-status correction without an extracted relation is recoverable
    # from the source type and explicit supersession link. This deliberately
    # does not infer a task from an arbitrary noun or invent an owner.
    for row in _observation_rows(connection):
        if str(row["source_type"]).casefold() not in _TASK_SOURCE_TYPES:
            continue
        if str(row["predicate"]).casefold() not in {"status", "lifecycle"}:
            continue
        target = row["supersedes_event_id"]
        if not isinstance(target, str) or target not in by_event:
            continue
        value = str(row["operation"]).casefold()
        if value not in {"correction", "supersede"}:
            continue
        add(_candidate(str(row["event_id"]), target, "meaningful_change", ["lifecycle"]))

    return recovered


def recovery_digest(relationships: list[dict[str, Any]]) -> str:
    """Return a stable digest for trajectory metadata and unit assertions."""

    return hashlib.sha256(canonical_json(relationships).encode("utf-8")).hexdigest()


def _identifier_tokens(text: str) -> list[str]:
    """Extract stable, non-date identifiers from a raw capture."""

    result: list[str] = []
    seen: set[str] = set()
    for match in _IDENTIFIER_PATTERN.finditer(text):
        token = match.group(0).casefold().replace("_", "-")
        if token not in seen:
            seen.add(token)
            result.append(token)
    return result


def _merchant_key(text: str) -> str | None:
    """Derive a short stable merchant key from a phrase before ``receipt``."""

    match = re.search(r"\b([A-Za-z][A-Za-z0-9 &'./-]{1,60}?)\s+receipt\b", text, re.IGNORECASE)
    if not match:
        return None
    words = re.findall(r"[A-Za-z0-9]+", match.group(1).casefold())
    if not words or words[0] in {
        "a",
        "an",
        "the",
        "receipt",
        "copy",
        "normalized",
        "normalised",
        "of",
        "uploaded",
        "captured",
        "unchanged",
        "same",
        "distinct",
        "is",
        "was",
        "are",
    }:
        return None
    return words[0]


def _receipt_like(row: sqlite3.Row, text: str) -> bool:
    return str(row["source_type"]).casefold() == "receipt" or "receipt" in text.casefold()


def _relation_row_value(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "source_event_id": row["source_event_id"],
        "target_event_id": row["target_event_id"],
        "relation_type": row["relation_type"],
        "changed_fields": json.loads(row["changed_fields_json"]),
        "duplicate_group": row["duplicate_group"],
        "note": row["note"],
    }


def retrieved_relation_replacements(
    connection: sqlite3.Connection,
    *,
    max_candidates: int = 4,
) -> dict[str, Any]:
    """Build bounded raw-capture candidates and conservative replacements.

    Only receipt-like relation sources with one existing relation are
    considered. The first stable identifier in the source text is the primary
    identity; earlier captures sharing it are returned newest-first. A
    meaningful change prefers the newest earlier non-duplicate member, while a
    duplicate or similarity relation prefers the newest member. This keeps the
    candidate set small and makes the lineage rule auditable.
    """

    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    events = _raw_events(connection)
    by_event = {str(row["event_id"]): row for row in events}
    text_by_event = {str(row["event_id"]): _payload_text(row) for row in events}
    tokens_by_event = {event_id: _identifier_tokens(text) for event_id, text in text_by_event.items()}
    relations = connection.execute(
        "SELECT * FROM relationships ORDER BY relationship_id"
    ).fetchall()
    relations_by_source: dict[str, list[sqlite3.Row]] = defaultdict(list)
    duplicate_sources: set[str] = set()
    for row in relations:
        source = str(row["source_event_id"])
        relations_by_source[source].append(row)
        if str(row["relation_type"]).casefold() in {"exact_duplicate", "normalized_duplicate", "duplicate"}:
            duplicate_sources.add(source)

    replacements: list[dict[str, Any]] = []
    candidate_sets: list[dict[str, Any]] = []
    for source, source_relations in relations_by_source.items():
        source_row = by_event.get(source)
        if source_row is None or len(source_relations) != 1:
            continue
        current_row = source_relations[0]
        current = _relation_row_value(current_row)
        relation_type = str(current["relation_type"]).casefold()
        if relation_type not in _RECEIPT_RELATION_TYPES:
            continue
        source_text = text_by_event.get(source, "")
        if not _receipt_like(source_row, source_text):
            continue
        tokens = tokens_by_event.get(source, [])
        if not tokens:
            continue
        primary_token = tokens[0]
        candidates = [
            row
            for row in events
            if int(row["sequence"]) < int(source_row["sequence"])
            and primary_token in tokens_by_event.get(str(row["event_id"]), [])
        ]
        candidates = sorted(candidates, key=lambda row: int(row["sequence"]), reverse=True)[:max_candidates]
        if not candidates:
            continue

        if relation_type == "meaningful_change":
            non_duplicate = [row for row in candidates if str(row["event_id"]) not in duplicate_sources]
            selected = non_duplicate[0] if non_duplicate else candidates[0]
        else:
            selected = candidates[0]
        selected_id = str(selected["event_id"])

        replacement = dict(current)
        replacement["target_event_id"] = selected_id
        if relation_type in {"exact_duplicate", "normalized_duplicate", "duplicate"}:
            lowered = source_text.casefold()
            if any(marker in lowered for marker in _EXACT_MARKERS):
                replacement["relation_type"] = "exact_duplicate"
            elif any(marker in lowered for marker in _NORMALIZED_MARKERS):
                replacement["relation_type"] = "normalized_duplicate"
            replacement["changed_fields"] = []
        elif relation_type == "similar_not_duplicate":
            replacement["changed_fields"] = []
            if replacement.get("note") is None and "separate purchase" in source_text.casefold():
                replacement["note"] = "different receipt identifier and purchase"

        if replacement["relation_type"] in {"exact_duplicate", "normalized_duplicate", "duplicate", "meaningful_change"}:
            merchant = next(
                (
                    merchant_key
                    for merchant_key in (
                        _merchant_key(source_text),
                        *(_merchant_key(text_by_event.get(str(row["event_id"]), "")) for row in candidates),
                    )
                    if merchant_key
                ),
                None,
            )
            if merchant:
                replacement["duplicate_group"] = f"{merchant}-{primary_token}"

        comparable_keys = ("target_event_id", "relation_type", "changed_fields", "duplicate_group", "note")
        changed = any(replacement.get(key) != current.get(key) for key in comparable_keys)
        if changed:
            replacements.append(replacement)

        candidate_sets.append(
            {
                "source_event_id": source,
                "source_raw_text": source_text,
                "source_sequence": int(source_row["sequence"]),
                "source_relation": current,
                "identifiers": tokens,
                "primary_identifier": primary_token,
                "selected_target_event_id": selected_id,
                "candidates": [
                    {
                        "event_id": str(row["event_id"]),
                        "sequence": int(row["sequence"]),
                        "source_type": row["source_type"],
                        "raw_text": text_by_event.get(str(row["event_id"]), ""),
                        "metadata": json.loads(row["metadata_json"]),
                    }
                    for row in candidates
                ],
                "replacement": replacement if changed else None,
            }
        )

    return {
        "max_candidates": max_candidates,
        "candidate_sets": candidate_sets,
        "replacements": replacements,
        "replacement_digest": recovery_digest(replacements),
    }


__all__ = [
    "DETERMINISTIC_RECOVERY_VERSION",
    "deterministic_relationships",
    "recovery_digest",
    "retrieved_relation_replacements",
]
