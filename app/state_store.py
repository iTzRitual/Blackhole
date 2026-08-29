"""Append-only raw capture storage and deterministic rebuildable projection."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECTION_VERSION = "experiment-001-projection-v2"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def unique_refs(value: Iterable[str]) -> list[str]:
    return sorted({item for item in value if isinstance(item, str) and item})


class StateStore:
    """SQLite store whose raw event table is protected by aborting triggers."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "StateStore":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS raw_events (
                event_id TEXT PRIMARY KEY,
                sequence INTEGER NOT NULL UNIQUE CHECK(sequence > 0),
                captured_at TEXT NOT NULL,
                observed_at TEXT,
                source_type TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                inserted_at TEXT NOT NULL
            );

            CREATE TRIGGER IF NOT EXISTS raw_events_no_update
            BEFORE UPDATE ON raw_events
            BEGIN
                SELECT RAISE(ABORT, 'raw_events are immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS raw_events_no_delete
            BEFORE DELETE ON raw_events
            BEGIN
                SELECT RAISE(ABORT, 'raw_events are immutable');
            END;

            CREATE TABLE IF NOT EXISTS observations (
                observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL REFERENCES raw_events(event_id),
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                knowledge_status TEXT NOT NULL CHECK(knowledge_status IN ('known', 'inferred', 'unknown')),
                value_json TEXT,
                unknown_reason TEXT,
                operation TEXT NOT NULL CHECK(operation IN ('set', 'supersede', 'correction', 'contradiction', 'duplicate')),
                supersedes_event_id TEXT,
                source_refs_json TEXT NOT NULL,
                extractor_version TEXT NOT NULL,
                fingerprint TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS relationships (
                relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_event_id TEXT NOT NULL REFERENCES raw_events(event_id),
                target_event_id TEXT REFERENCES raw_events(event_id),
                relation_type TEXT NOT NULL,
                changed_fields_json TEXT NOT NULL,
                duplicate_group TEXT,
                note TEXT,
                extractor_version TEXT NOT NULL,
                fingerprint TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projection_runs (
                projection_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                projection_version TEXT NOT NULL,
                input_digest TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS current_facts (
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                knowledge_status TEXT NOT NULL,
                value_json TEXT,
                unknown_reason TEXT,
                source_refs_json TEXT NOT NULL,
                latest_sequence INTEGER NOT NULL,
                observation_ids_json TEXT NOT NULL,
                projection_run_id INTEGER NOT NULL REFERENCES projection_runs(projection_run_id),
                PRIMARY KEY(subject, predicate)
            );
            """
        )
        self.connection.commit()

    def insert_raw_events(self, events: Iterable[dict[str, Any]]) -> int:
        inserted = 0
        for event in events:
            event_id = event.get("event_id")
            sequence = event.get("sequence")
            payload = event.get("payload")
            if not isinstance(event_id, str) or not isinstance(sequence, int) or not isinstance(payload, dict):
                raise ValueError("raw event requires event_id, integer sequence, and payload object")
            payload_json = canonical_json(payload)
            payload_sha256 = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
            declared_hash = event.get("payload_sha256")
            if declared_hash is not None and declared_hash != payload_sha256:
                raise ValueError(f"payload hash mismatch for {event_id}")
            raw_json = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            existing = self.connection.execute(
                "SELECT raw_json FROM raw_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            if existing is not None:
                if json.loads(existing["raw_json"]) != event:
                    raise ValueError(f"immutable raw event conflict for {event_id}")
                continue
            self.connection.execute(
                """
                INSERT INTO raw_events(
                    event_id, sequence, captured_at, observed_at, source_type,
                    raw_json, payload_json, payload_sha256, metadata_json, inserted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    sequence,
                    str(event.get("captured_at", "")),
                    event.get("observed_at"),
                    str(event.get("source_type", "text")),
                    raw_json,
                    payload_json,
                    payload_sha256,
                    canonical_json(event.get("metadata", {})),
                    utc_now(),
                ),
            )
            inserted += 1
        self.connection.commit()
        return inserted

    def add_observations(self, observations: Iterable[dict[str, Any]], extractor_version: str) -> int:
        inserted = 0
        for item in observations:
            event_id = item.get("event_id")
            subject = item.get("subject")
            predicate = item.get("predicate")
            status = item.get("knowledge_status")
            if not all(isinstance(value, str) and value for value in (event_id, subject, predicate, status)):
                raise ValueError("observation requires event_id, subject, predicate, and knowledge_status")
            if status not in {"known", "inferred", "unknown"}:
                raise ValueError(f"unsupported observation status: {status}")
            if self.connection.execute("SELECT 1 FROM raw_events WHERE event_id = ?", (event_id,)).fetchone() is None:
                raise ValueError(f"observation references unknown event {event_id}")
            operation = item.get("operation", "set")
            if operation not in {"set", "supersede", "correction", "contradiction", "duplicate"}:
                operation = "set"
            value = item.get("value") if status != "unknown" else None
            unknown_reason = item.get("unknown_reason") if status == "unknown" else None
            source_refs = unique_refs(item.get("source_refs", [event_id]))
            if not source_refs:
                source_refs = [event_id]
            fingerprint_value = {
                "event_id": event_id,
                "subject": subject,
                "predicate": predicate,
                "knowledge_status": status,
                "value": value,
                "unknown_reason": unknown_reason,
                "operation": operation,
                "supersedes_event_id": item.get("supersedes_event_id"),
                "source_refs": source_refs,
            }
            fingerprint = hashlib.sha256(canonical_json(fingerprint_value).encode("utf-8")).hexdigest()
            cursor = self.connection.execute(
                """
                INSERT OR IGNORE INTO observations(
                    event_id, subject, predicate, knowledge_status, value_json,
                    unknown_reason, operation, supersedes_event_id, source_refs_json,
                    extractor_version, fingerprint, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    subject,
                    predicate,
                    status,
                    canonical_json(value) if value is not None else None,
                    unknown_reason,
                    operation,
                    item.get("supersedes_event_id"),
                    canonical_json(source_refs),
                    extractor_version,
                    fingerprint,
                    utc_now(),
                ),
            )
            inserted += int(cursor.rowcount > 0)
        self.connection.commit()
        return inserted

    def add_relationships(self, relationships: Iterable[dict[str, Any]], extractor_version: str) -> int:
        inserted = 0
        for item in relationships:
            source_event_id = item.get("source_event_id")
            target_event_id = item.get("target_event_id")
            relation_type = item.get("relation_type")
            if not all(isinstance(value, str) and value for value in (source_event_id, relation_type)):
                continue
            if self.connection.execute("SELECT 1 FROM raw_events WHERE event_id = ?", (source_event_id,)).fetchone() is None:
                continue
            if target_event_id is not None and self.connection.execute("SELECT 1 FROM raw_events WHERE event_id = ?", (target_event_id,)).fetchone() is None:
                target_event_id = None
            changed_fields = item.get("changed_fields", [])
            if not isinstance(changed_fields, list):
                changed_fields = []
            fingerprint_value = {
                "source_event_id": source_event_id,
                "target_event_id": target_event_id,
                "relation_type": relation_type,
                "changed_fields": unique_refs(changed_fields),
                "duplicate_group": item.get("duplicate_group"),
                "note": item.get("note"),
            }
            fingerprint = hashlib.sha256(canonical_json(fingerprint_value).encode("utf-8")).hexdigest()
            cursor = self.connection.execute(
                """
                INSERT OR IGNORE INTO relationships(
                    source_event_id, target_event_id, relation_type, changed_fields_json,
                    duplicate_group, note, extractor_version, fingerprint, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_event_id,
                    target_event_id,
                    relation_type,
                    canonical_json(unique_refs(changed_fields)),
                    item.get("duplicate_group"),
                    item.get("note"),
                    extractor_version,
                    fingerprint,
                    utc_now(),
                ),
            )
            inserted += int(cursor.rowcount > 0)
        self.connection.commit()
        return inserted

    def replace_relationships_for_sources(
        self,
        relationships: Iterable[dict[str, Any]],
        extractor_version: str,
    ) -> int:
        """Replace derived relationships for explicitly selected source events.

        Raw events and semantic observations remain append-only. Relationship
        rows are derived state, so a versioned reconciliation pass may replace
        the rows for a source event before the projection is rebuilt. Callers
        must pass only sources for which the replacement is complete and
        unambiguous.
        """

        items = [item for item in relationships if isinstance(item, dict)]
        source_event_ids = sorted(
            {
                item.get("source_event_id")
                for item in items
                if isinstance(item.get("source_event_id"), str) and item.get("source_event_id")
            }
        )
        if not source_event_ids:
            return 0
        placeholders = ",".join("?" for _ in source_event_ids)
        self.connection.execute(
            f"DELETE FROM relationships WHERE source_event_id IN ({placeholders})",
            source_event_ids,
        )
        self.connection.commit()
        return self.add_relationships(items, extractor_version)

    def rebuild_projection(self) -> dict[str, Any]:
        observation_rows = self.connection.execute(
            """
            SELECT o.*, r.sequence
            FROM observations o JOIN raw_events r ON r.event_id = o.event_id
            ORDER BY r.sequence, o.observation_id
            """
        ).fetchall()
        relationship_rows = self.connection.execute(
            "SELECT * FROM relationships ORDER BY relationship_id"
        ).fetchall()
        digest_input = [dict(row) for row in observation_rows] + [dict(row) for row in relationship_rows]
        digest = hashlib.sha256(canonical_json(digest_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            "INSERT INTO projection_runs(projection_version, input_digest, created_at) VALUES (?, ?, ?)",
            (PROJECTION_VERSION, digest, utc_now()),
        )
        projection_run_id = int(cursor.lastrowid)
        self.connection.execute("DELETE FROM current_facts")

        duplicate_sources = {
            row["source_event_id"]
            for row in relationship_rows
            if str(row["relation_type"]).casefold() in {"exact_duplicate", "normalized_duplicate", "duplicate"}
        }
        observations_by_event: dict[str, list[sqlite3.Row]] = {}
        for row in observation_rows:
            observations_by_event.setdefault(row["event_id"], []).append(row)
        resolved_fields: set[tuple[str, str]] = set()
        field_aliases = {
            "amount": {"amount", "current_price", "historical_price", "last_charge", "current_amount", "observed_total", "purchased_total", "premium", "quoted_amount"},
            "status": {"status", "lifecycle"},
        }
        for relation in relationship_rows:
            relation_type = str(relation["relation_type"]).casefold()
            if relation_type in {"exact_duplicate", "normalized_duplicate", "duplicate", "similar_not_duplicate", "contradiction"}:
                continue
            source_event = relation["source_event_id"]
            changed_fields = json.loads(relation["changed_fields_json"])
            source_observations = observations_by_event.get(source_event, [])
            for field in changed_fields:
                predicates = field_aliases.get(field, {field})
                if any(
                    row["predicate"] in predicates
                    and row["operation"] not in {"contradiction", "duplicate"}
                    and row["knowledge_status"] in {"known", "inferred"}
                    for row in source_observations
                ):
                    for predicate in predicates:
                        resolved_fields.add((source_event, predicate))
        grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for row in observation_rows:
            if row["event_id"] in duplicate_sources or row["operation"] == "duplicate":
                continue
            grouped.setdefault((row["subject"], row["predicate"]), []).append(row)

        for (subject, predicate), rows in grouped.items():
            current: sqlite3.Row | None = None
            conflict_rows: list[sqlite3.Row] = []
            for row in rows:
                operation = row["operation"]
                if conflict_rows and (row["event_id"], row["predicate"]) in resolved_fields:
                    conflict_rows = []
                if operation == "contradiction":
                    conflict_rows.extend([item for item in (current, row) if item is not None])
                    current = row
                    continue
                if conflict_rows and operation not in {"correction", "supersede"}:
                    conflict_rows.append(row)
                    current = row
                    continue
                if operation in {"correction", "supersede"}:
                    conflict_rows = []
                current = row
            if current is None:
                continue
            if conflict_rows:
                source_refs = unique_refs(
                    ref
                    for row in conflict_rows
                    for ref in json.loads(row["source_refs_json"])
                )
                self.connection.execute(
                    """
                    INSERT INTO current_facts(
                        subject, predicate, knowledge_status, value_json, unknown_reason,
                        source_refs_json, latest_sequence, observation_ids_json, projection_run_id
                    ) VALUES (?, ?, 'unknown', NULL, 'conflicting', ?, ?, ?, ?)
                    """,
                    (
                        subject,
                        predicate,
                        canonical_json(source_refs),
                        current["sequence"],
                        canonical_json([row["observation_id"] for row in conflict_rows]),
                        projection_run_id,
                    ),
                )
                continue
            self.connection.execute(
                """
                INSERT INTO current_facts(
                    subject, predicate, knowledge_status, value_json, unknown_reason,
                    source_refs_json, latest_sequence, observation_ids_json, projection_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subject,
                    predicate,
                    current["knowledge_status"],
                    current["value_json"],
                    current["unknown_reason"],
                    current["source_refs_json"],
                    current["sequence"],
                    canonical_json([row["observation_id"] for row in rows]),
                    projection_run_id,
                ),
            )
        self.connection.commit()
        return {"projection_run_id": projection_run_id, "projection_version": PROJECTION_VERSION, "input_digest": digest}

    def snapshot(self) -> dict[str, Any]:
        current_rows = self.connection.execute(
            "SELECT * FROM current_facts ORDER BY subject, predicate"
        ).fetchall()
        observation_rows = self.connection.execute(
            """
            SELECT o.*, r.sequence, r.observed_at
            FROM observations o JOIN raw_events r ON r.event_id = o.event_id
            ORDER BY r.sequence, o.observation_id
            """
        ).fetchall()
        relationship_rows = self.connection.execute(
            "SELECT * FROM relationships ORDER BY relationship_id"
        ).fetchall()
        event_rows = self.connection.execute(
            "SELECT event_id, sequence, captured_at, observed_at, source_type FROM raw_events ORDER BY sequence"
        ).fetchall()

        current: list[dict[str, Any]] = []
        for row in current_rows:
            item = {
                "subject": row["subject"],
                "predicate": row["predicate"],
                "knowledge_status": row["knowledge_status"],
                "source_refs": json.loads(row["source_refs_json"]),
                "latest_sequence": row["latest_sequence"],
            }
            if row["knowledge_status"] == "unknown":
                item["unknown_reason"] = row["unknown_reason"] or "missing"
            elif row["value_json"] is not None:
                item["value"] = json.loads(row["value_json"])
            current.append(item)

        history: list[dict[str, Any]] = []
        for row in observation_rows:
            item = {
                "event_id": row["event_id"],
                "sequence": row["sequence"],
                "observed_at": row["observed_at"],
                "subject": row["subject"],
                "predicate": row["predicate"],
                "knowledge_status": row["knowledge_status"],
                "operation": row["operation"],
                "source_refs": json.loads(row["source_refs_json"]),
            }
            if row["value_json"] is not None:
                item["value"] = json.loads(row["value_json"])
            if row["unknown_reason"] is not None:
                item["unknown_reason"] = row["unknown_reason"]
            if row["supersedes_event_id"] is not None:
                item["supersedes_event_id"] = row["supersedes_event_id"]
            history.append(item)

        relationships: list[dict[str, Any]] = []
        for row in relationship_rows:
            relationships.append(
                {
                    "source_event_id": row["source_event_id"],
                    "target_event_id": row["target_event_id"],
                    "relation_type": row["relation_type"],
                    "changed_fields": json.loads(row["changed_fields_json"]),
                    "duplicate_group": row["duplicate_group"],
                    "note": row["note"],
                }
            )

        relation_counts: dict[str, int] = {}
        for relation in relationships:
            relation_type = str(relation["relation_type"])
            relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1
        duplicate_groups = {
            relation.get("duplicate_group")
            for relation in relationships
            if relation.get("duplicate_group")
        }
        return {
            "projection_version": PROJECTION_VERSION,
            "current_facts": current,
            "history": history,
            "relationships": relationships,
            "deterministic_counts": {
                "duplicate_event_count": sum(
                    count
                    for relation_type, count in relation_counts.items()
                    if relation_type.casefold() in {"exact_duplicate", "normalized_duplicate", "duplicate"}
                ),
                "duplicate_group_count": len(duplicate_groups),
                "meaningful_change_event_count": sum(
                    count for relation_type, count in relation_counts.items() if relation_type.casefold() == "meaningful_change"
                ),
                "relation_counts": dict(sorted(relation_counts.items())),
            },
            "event_index": [dict(row) for row in event_rows],
        }

    def extraction_context(self) -> dict[str, Any]:
        """Return a compact prior context for the next semantic batch."""

        snapshot = self.snapshot()
        return {
            "projection_version": snapshot["projection_version"],
            "current_facts": snapshot["current_facts"],
            "relationships": snapshot["relationships"],
            "recent_captures": [
                {
                    "event_id": event["event_id"],
                    "sequence": event["sequence"],
                    "observed_at": event["observed_at"],
                    "source_type": event["source_type"],
                }
                for event in snapshot["event_index"][-40:]
            ],
        }
