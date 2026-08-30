"""Append-only raw capture storage and deterministic rebuildable projection."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECTION_VERSION = "experiment-001-projection-v2"
DUPLICATE_EVIDENCE_PROJECTION_VERSION = "experiment-005-duplicate-evidence-projection-v1"
TRUE_DUPLICATE_RELATION_TYPES = frozenset({"exact_duplicate", "normalized_duplicate", "duplicate"})
PROCESSING_STATE_VERSION = "blackhole-processing-state-v1"
PROCESSING_STATUSES = frozenset({"pending", "processing", "processed", "failed"})


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
        # HostServer may keep one runtime alive while request handlers run in
        # worker threads.  Domain operations remain serialized at the Host
        # boundary; disabling SQLite's thread-affinity guard lets that scoped
        # ownership model close cleanly without changing the V1 schema or
        # projection semantics.
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._last_duplicate_evidence_stats: dict[str, Any] = {
            "enabled": False,
            "component_count": 0,
            "member_event_count": 0,
            "noncanonical_event_count": 0,
            "observations_recovered_from_duplicate_events": 0,
            "consolidated_identical_observations": 0,
            "conflicts_preserved": 0,
            "count_invariants": {},
        }
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

            CREATE TABLE IF NOT EXISTS duplicate_components (
                component_id TEXT PRIMARY KEY,
                canonical_event_id TEXT NOT NULL REFERENCES raw_events(event_id),
                member_event_ids_json TEXT NOT NULL,
                member_count INTEGER NOT NULL CHECK(member_count > 1),
                projection_run_id INTEGER NOT NULL REFERENCES projection_runs(projection_run_id)
            );

            CREATE TABLE IF NOT EXISTS processing_state (
                event_id TEXT PRIMARY KEY REFERENCES raw_events(event_id),
                status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'processed', 'failed')),
                processing_version TEXT NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
                last_attempted_at TEXT,
                last_successful_at TEXT,
                last_error TEXT,
                extractor_version TEXT,
                completion_version TEXT,
                relation_recovery_version TEXT,
                duplicate_projection_version TEXT,
                updated_at TEXT NOT NULL
            );
            """
        )
        # Existing demo/replay databases predate the operational queue. Their
        # semantic rows are already derived, so import them as processed;
        # source-only rows become pending. New captures are inserted as
        # pending in insert_raw_events below.
        self.connection.execute(
            """
            INSERT OR IGNORE INTO processing_state(
                event_id, status, processing_version, attempt_count,
                last_attempted_at, last_successful_at, last_error,
                extractor_version, completion_version, relation_recovery_version,
                duplicate_projection_version, updated_at
            )
            SELECT r.event_id,
                   CASE WHEN EXISTS (SELECT 1 FROM observations o WHERE o.event_id = r.event_id)
                        THEN 'processed' ELSE 'pending' END,
                   ?, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, ?
            FROM raw_events r
            """,
            (PROCESSING_STATE_VERSION, utc_now()),
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
            self.connection.execute(
                """
                INSERT INTO processing_state(
                    event_id, status, processing_version, attempt_count,
                    last_attempted_at, last_successful_at, last_error,
                    extractor_version, completion_version, relation_recovery_version,
                    duplicate_projection_version, updated_at
                ) VALUES (?, 'pending', ?, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, ?)
                """,
                (event_id, PROCESSING_STATE_VERSION, utc_now()),
            )
            inserted += 1
        self.connection.commit()
        return inserted

    @staticmethod
    def _raw_event_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return json.loads(row["raw_json"])

    def raw_event(self, event_id: str) -> dict[str, Any] | None:
        """Return one immutable raw event without exposing derived state."""

        row = self.connection.execute(
            "SELECT raw_json FROM raw_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        return self._raw_event_from_row(row) if row is not None else None

    def raw_events(self, *, max_sequence: int | None = None) -> list[dict[str, Any]]:
        """Return raw captures in source sequence order."""

        if max_sequence is None:
            rows = self.connection.execute(
                "SELECT raw_json FROM raw_events ORDER BY sequence"
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT raw_json FROM raw_events WHERE sequence <= ? ORDER BY sequence",
                (max_sequence,),
            ).fetchall()
        return [self._raw_event_from_row(row) for row in rows]

    @staticmethod
    def _processing_record(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "event_id": row["event_id"],
            "sequence": row["sequence"],
            "status": row["status"],
            "processing_version": row["processing_version"],
            "attempt_count": row["attempt_count"],
            "last_attempted_at": row["last_attempted_at"],
            "last_successful_at": row["last_successful_at"],
            "last_error": row["last_error"],
            "extractor_version": row["extractor_version"],
            "completion_version": row["completion_version"],
            "relation_recovery_version": row["relation_recovery_version"],
            "duplicate_projection_version": row["duplicate_projection_version"],
            "updated_at": row["updated_at"],
        }

    def processing_status(self, event_id: str | None = None) -> dict[str, Any] | None:
        """Return auditable derived processing state for one or all events."""

        query = """
            SELECT p.*, r.sequence
            FROM processing_state p JOIN raw_events r ON r.event_id = p.event_id
        """
        if event_id is not None:
            row = self.connection.execute(
                query + " WHERE p.event_id = ?", (event_id,)
            ).fetchone()
            return self._processing_record(row) if row is not None else None
        rows = self.connection.execute(query + " ORDER BY r.sequence").fetchall()
        records = [self._processing_record(row) for row in rows]
        counts = {status: 0 for status in sorted(PROCESSING_STATUSES)}
        for record in records:
            status = record["status"]
            if status in counts:
                counts[status] += 1
        return {"counts": counts, "events": records}

    def processing_events(self, *, statuses: Iterable[str] = ("pending",), limit: int | None = None) -> list[dict[str, Any]]:
        """Return raw events whose derived processing status is selected."""

        selected = [status for status in statuses if status in PROCESSING_STATUSES]
        if not selected:
            return []
        placeholders = ",".join("?" for _ in selected)
        query = f"""
            SELECT r.raw_json
            FROM processing_state p JOIN raw_events r ON r.event_id = p.event_id
            WHERE p.status IN ({placeholders})
            ORDER BY r.sequence
        """
        parameters: list[Any] = list(selected)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            query += " LIMIT ?"
            parameters.append(limit)
        return [self._raw_event_from_row(row) for row in self.connection.execute(query, parameters).fetchall()]

    def claim_processing(
        self,
        event_ids: Iterable[str],
        processing_version: str,
        *,
        include_failed: bool = False,
    ) -> int:
        """Atomically claim pending (or explicitly retried failed) events."""

        statuses = ("pending", "failed") if include_failed else ("pending",)
        placeholders = ",".join("?" for _ in statuses)
        claimed = 0
        for event_id in event_ids:
            if not isinstance(event_id, str) or not event_id:
                continue
            cursor = self.connection.execute(
                f"""
                UPDATE processing_state
                SET status = 'processing', processing_version = ?,
                    attempt_count = attempt_count + 1,
                    last_attempted_at = ?, last_error = NULL, updated_at = ?
                WHERE event_id = ? AND status IN ({placeholders})
                """,
                (processing_version, utc_now(), utc_now(), event_id, *statuses),
            )
            claimed += int(cursor.rowcount > 0)
        self.connection.commit()
        return claimed

    def mark_processed(
        self,
        event_ids: Iterable[str],
        *,
        processing_version: str,
        extractor_version: str,
        completion_version: str | None,
        relation_recovery_version: str | None,
        duplicate_projection_version: str | None,
    ) -> int:
        """Record successful derived processing without touching raw events."""

        updated = 0
        for event_id in event_ids:
            cursor = self.connection.execute(
                """
                UPDATE processing_state
                SET status = 'processed', processing_version = ?,
                    last_successful_at = ?, last_error = NULL,
                    extractor_version = ?, completion_version = ?,
                    relation_recovery_version = ?, duplicate_projection_version = ?,
                    updated_at = ?
                WHERE event_id = ? AND status = 'processing'
                """,
                (
                    processing_version,
                    utc_now(),
                    extractor_version,
                    completion_version,
                    relation_recovery_version,
                    duplicate_projection_version,
                    utc_now(),
                    event_id,
                ),
            )
            updated += int(cursor.rowcount > 0)
        self.connection.commit()
        return updated

    def mark_failed(self, event_ids: Iterable[str], *, processing_version: str, error: str) -> int:
        """Record a retryable failure while retaining every raw capture."""

        safe_error = str(error).strip()[:1000] or "processing failed"
        updated = 0
        for event_id in event_ids:
            cursor = self.connection.execute(
                """
                UPDATE processing_state
                SET status = 'failed', processing_version = ?, last_error = ?, updated_at = ?
                WHERE event_id = ? AND status = 'processing'
                """,
                (processing_version, safe_error, utc_now(), event_id),
            )
            updated += int(cursor.rowcount > 0)
        self.connection.commit()
        return updated

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

    @staticmethod
    def _duplicate_components(
        relationship_rows: Iterable[Any], event_sequences: dict[str, int]
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """Build stable components from true duplicate edges only.

        Components are derived from the undirected relation graph. The earliest
        event by sequence is the canonical member; relation direction is not
        allowed to make a later capture canonical by accident.
        """

        parent: dict[str, str] = {}

        def find(item: str) -> str:
            parent.setdefault(item, item)
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(left: str, right: str) -> None:
            left_root, right_root = find(left), find(right)
            if left_root == right_root:
                return
            if left_root < right_root:
                parent[right_root] = left_root
            else:
                parent[left_root] = right_root

        for relation in relationship_rows:
            relation_type = str(relation["relation_type"]).casefold()
            source = relation["source_event_id"]
            target = relation["target_event_id"]
            if relation_type in TRUE_DUPLICATE_RELATION_TYPES and isinstance(source, str) and isinstance(target, str):
                union(source, target)

        members_by_root: dict[str, list[str]] = {}
        for event_id in parent:
            members_by_root.setdefault(find(event_id), []).append(event_id)

        components: list[dict[str, Any]] = []
        event_to_component: dict[str, str] = {}
        for members in members_by_root.values():
            ordered_members = sorted(
                members,
                key=lambda event_id: (event_sequences.get(event_id, 2**63 - 1), event_id),
            )
            canonical_event_id = ordered_members[0]
            component_id = f"duplicate-component:{canonical_event_id}"
            record = {
                "component_id": component_id,
                "canonical_event_id": canonical_event_id,
                "member_event_ids": ordered_members,
                "member_count": len(ordered_members),
            }
            components.append(record)
            for event_id in ordered_members:
                event_to_component[event_id] = component_id

        components.sort(key=lambda item: (event_sequences.get(item["canonical_event_id"], 2**63 - 1), item["component_id"]))
        return components, event_to_component

    @staticmethod
    def _row_hidden(row: Any, key: str, default: Any = None) -> Any:
        return row.get(key, default) if isinstance(row, dict) else default

    @staticmethod
    def _row_value(row: Any) -> Any:
        if row["knowledge_status"] == "unknown" or row["value_json"] is None:
            return None
        return json.loads(row["value_json"])

    @classmethod
    def _row_signature(cls, row: Any) -> tuple[str, str | None]:
        status = str(row["knowledge_status"])
        if status == "unknown":
            return status, None
        return status, canonical_json(cls._row_value(row))

    @classmethod
    def _consolidate_component_rows(
        cls,
        rows: list[Any],
        *,
        component: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, int]]:
        """Consolidate one component/predicate without counting occurrences twice."""

        ordered_rows = sorted(rows, key=lambda row: (row["sequence"], row["observation_id"]))
        latest = ordered_rows[-1]
        statuses = [str(row["knowledge_status"]) for row in ordered_rows]
        value_rows = [row for row in ordered_rows if row["knowledge_status"] != "unknown" and row["value_json"] is not None]
        value_signatures = {canonical_json(cls._row_value(row)) for row in value_rows}
        explicit_rows = [
            row
            for row in ordered_rows
            if row["operation"] in {"correction", "supersede"}
            and isinstance(row["supersedes_event_id"], str)
        ]
        superseded_ids = {row["supersedes_event_id"] for row in explicit_rows}
        superseded_signatures = {
            canonical_json(cls._row_value(row))
            for row in value_rows
            if row["event_id"] in superseded_ids
        }

        resolved_row: Any | None = None
        if len(value_signatures) > 1 and explicit_rows:
            terminal_explicit_rows = [
                row for row in explicit_rows if row["event_id"] not in superseded_ids
            ]
            terminal_signatures = {
                canonical_json(cls._row_value(row)) for row in terminal_explicit_rows
            }
            if len(terminal_explicit_rows) == 1 and len(terminal_signatures) == 1:
                candidate = terminal_explicit_rows[0]
                candidate_signature = canonical_json(cls._row_value(candidate))
                unresolved_rows = [
                    row
                    for row in value_rows
                    if canonical_json(cls._row_value(row)) != candidate_signature
                    and row["event_id"] not in superseded_ids
                    and canonical_json(cls._row_value(row)) not in superseded_signatures
                    and row["operation"] not in {"correction", "supersede"}
                ]
                unresolved_unknowns = [
                    row
                    for row in ordered_rows
                    if row["knowledge_status"] == "unknown"
                    and row["event_id"] not in superseded_ids
                ]
                if not unresolved_rows and not unresolved_unknowns:
                    resolved_row = candidate

        if len(value_signatures) > 1 and resolved_row is None:
            output_status = "unknown"
            output_value_json = None
            output_reason = "conflicting"
            output_operation = "contradiction"
            conflicts_preserved = 1
            consolidated_identical = 0
        elif not value_rows:
            output_status = "unknown"
            output_value_json = None
            output_reason = next(
                (row["unknown_reason"] for row in reversed(ordered_rows) if row["unknown_reason"]),
                "missing",
            )
            output_operation = "set"
            conflicts_preserved = 0
            consolidated_identical = max(0, len(ordered_rows) - 1)
        elif resolved_row is not None:
            output_status = str(resolved_row["knowledge_status"])
            output_value_json = resolved_row["value_json"]
            output_reason = None
            output_operation = str(resolved_row["operation"])
            conflicts_preserved = 0
            consolidated_identical = max(0, len(ordered_rows) - 1)
        elif any(row["knowledge_status"] == "unknown" for row in ordered_rows):
            output_status = "unknown"
            output_value_json = None
            output_reason = next(
                (row["unknown_reason"] for row in reversed(ordered_rows) if row["unknown_reason"]),
                "missing",
            )
            output_operation = "set"
            conflicts_preserved = 0
            consolidated_identical = 0
        else:
            value_signature = next(iter(value_signatures))
            same_value = all(
                row["knowledge_status"] != "unknown"
                and row["value_json"] is not None
                and canonical_json(cls._row_value(row)) == value_signature
                for row in ordered_rows
            )
            if same_value:
                status_rank = {"known": 0, "inferred": 1, "unknown": 2}
                output_status = max(statuses, key=lambda status: status_rank.get(status, 2))
                if output_status == "unknown":
                    output_value_json = None
                    output_reason = next(
                        (row["unknown_reason"] for row in reversed(ordered_rows) if row["unknown_reason"]),
                        "missing",
                    )
                else:
                    output_value_json = next(row["value_json"] for row in reversed(ordered_rows) if row["knowledge_status"] == output_status)
                    output_reason = None
                output_operation = "set"
                conflicts_preserved = 0
                consolidated_identical = max(0, len(ordered_rows) - 1)
            else:
                output_status = "unknown"
                output_value_json = None
                output_reason = "conflicting"
                output_operation = "contradiction"
                conflicts_preserved = 1
                consolidated_identical = 0

        source_refs = unique_refs(
            ref
            for row in ordered_rows
            for ref in json.loads(row["source_refs_json"])
        )
        output = dict(latest)
        output.update(
            {
                "event_id": latest["event_id"],
                "sequence": latest["sequence"],
                "knowledge_status": output_status,
                "value_json": output_value_json,
                "unknown_reason": output_reason,
                "operation": output_operation,
                "supersedes_event_id": resolved_row["supersedes_event_id"] if resolved_row is not None else None,
                "source_refs_json": canonical_json(source_refs),
                "observation_ids": [row["observation_id"] for row in ordered_rows],
                "component_id": component["component_id"],
                "component_event_ids": list(component["member_event_ids"]),
            }
        )
        return output, {
            "consolidated_identical_observations": consolidated_identical,
            "conflicts_preserved": conflicts_preserved,
        }

    @classmethod
    def _consolidate_observations(
        cls,
        observation_rows: list[Any],
        components: list[dict[str, Any]],
        event_to_component: dict[str, str],
        relationship_rows: list[Any],
    ) -> tuple[list[Any], dict[str, int]]:
        components_by_id = {item["component_id"]: item for item in components}
        grouped: dict[tuple[str, str, str], list[Any]] = {}
        passthrough: list[Any] = []
        duplicate_sources = {
            row["source_event_id"]
            for row in relationship_rows
            if str(row["relation_type"]).casefold() in TRUE_DUPLICATE_RELATION_TYPES
        }
        recovered_observation_ids: set[int] = set()
        for row in observation_rows:
            component_id = event_to_component.get(row["event_id"])
            if component_id is None:
                passthrough.append(row)
                continue
            grouped.setdefault((component_id, row["subject"], row["predicate"]), []).append(row)
            if row["event_id"] in duplicate_sources or row["operation"] == "duplicate":
                recovered_observation_ids.add(int(row["observation_id"]))

        consolidated: list[Any] = list(passthrough)
        stats = {
            "observations_recovered_from_duplicate_events": len(recovered_observation_ids),
            "consolidated_identical_observations": 0,
            "conflicts_preserved": 0,
        }
        for (component_id, _subject, _predicate), rows in grouped.items():
            output, row_stats = cls._consolidate_component_rows(rows, component=components_by_id[component_id])
            consolidated.append(output)
            stats["consolidated_identical_observations"] += row_stats["consolidated_identical_observations"]
            stats["conflicts_preserved"] += row_stats["conflicts_preserved"]
        consolidated.sort(key=lambda row: (row["sequence"], row["observation_id"]))
        return consolidated, stats

    def rebuild_projection(self, *, duplicate_evidence: bool = False) -> dict[str, Any]:
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
        event_sequences = {
            row["event_id"]: int(row["sequence"])
            for row in self.connection.execute("SELECT event_id, sequence FROM raw_events")
        }
        components, event_to_component = self._duplicate_components(relationship_rows, event_sequences)
        duplicate_edge_count = sum(
            str(row["relation_type"]).casefold() in TRUE_DUPLICATE_RELATION_TYPES
            and isinstance(row["source_event_id"], str)
            and isinstance(row["target_event_id"], str)
            for row in relationship_rows
        )
        if duplicate_evidence:
            projection_rows, consolidation_stats = self._consolidate_observations(
                list(observation_rows),
                components,
                event_to_component,
                list(relationship_rows),
            )
        else:
            projection_rows = list(observation_rows)
            consolidation_stats = {
                "observations_recovered_from_duplicate_events": 0,
                "consolidated_identical_observations": 0,
                "conflicts_preserved": 0,
            }
        projection_version = DUPLICATE_EVIDENCE_PROJECTION_VERSION if duplicate_evidence else PROJECTION_VERSION
        digest_input: Any = [dict(row) for row in observation_rows] + [dict(row) for row in relationship_rows]
        if duplicate_evidence:
            digest_input = {"mode": projection_version, "inputs": digest_input}
        digest = hashlib.sha256(canonical_json(digest_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            "INSERT INTO projection_runs(projection_version, input_digest, created_at) VALUES (?, ?, ?)",
            (projection_version, digest, utc_now()),
        )
        projection_run_id = int(cursor.lastrowid)
        self.connection.execute("DELETE FROM current_facts")
        self.connection.execute("DELETE FROM duplicate_components")
        if duplicate_evidence:
            for component in components:
                self.connection.execute(
                    """
                    INSERT INTO duplicate_components(
                        component_id, canonical_event_id, member_event_ids_json,
                        member_count, projection_run_id
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        component["component_id"],
                        component["canonical_event_id"],
                        canonical_json(component["member_event_ids"]),
                        component["member_count"],
                        projection_run_id,
                    ),
                )

        duplicate_sources = {
            row["source_event_id"]
            for row in relationship_rows
            if str(row["relation_type"]).casefold() in TRUE_DUPLICATE_RELATION_TYPES
        }
        observations_by_event: dict[str, list[sqlite3.Row]] = {}
        for row in observation_rows:
            observations_by_event.setdefault(row["event_id"], []).append(row)
        resolved_fields: set[tuple[str, str]] = set()
        resolved_component_fields: set[tuple[str, str]] = set()
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
            source_component = event_to_component.get(source_event) if duplicate_evidence else None
            if source_component is not None:
                source_observations = [
                    row for row in projection_rows if self._row_hidden(row, "component_id") == source_component
                ]
            for field in changed_fields:
                predicates = field_aliases.get(field, {field})
                if any(
                    row["predicate"] in predicates
                    and row["operation"] not in {"contradiction", "duplicate"}
                    and row["knowledge_status"] in {"known", "inferred"}
                    for row in source_observations
                ):
                    for predicate in predicates:
                        if source_component is not None:
                            resolved_component_fields.add((source_component, predicate))
                        else:
                            resolved_fields.add((source_event, predicate))
        grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for row in projection_rows:
            component_id = self._row_hidden(row, "component_id")
            if (
                (not duplicate_evidence and row["event_id"] in duplicate_sources)
                or (component_id is None and row["operation"] == "duplicate")
            ):
                continue
            grouped.setdefault((row["subject"], row["predicate"]), []).append(row)

        for (subject, predicate), rows in grouped.items():
            current: sqlite3.Row | None = None
            conflict_rows: list[Any] = []
            for row in rows:
                operation = row["operation"]
                row_component = self._row_hidden(row, "component_id")
                if conflict_rows and (
                    (row["event_id"], row["predicate"]) in resolved_fields
                    or (row_component, row["predicate"]) in resolved_component_fields
                ):
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
                        canonical_json(
                            [
                                observation_id
                                for row in conflict_rows
                                for observation_id in (
                                    self._row_hidden(row, "observation_ids", [row["observation_id"]])
                                )
                            ]
                        ),
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
                    canonical_json(
                        [
                            observation_id
                            for row in rows
                            for observation_id in self._row_hidden(row, "observation_ids", [row["observation_id"]])
                        ]
                    ),
                    projection_run_id,
                ),
            )
        self._last_duplicate_evidence_stats = {
            "enabled": duplicate_evidence,
            "component_count": len(components) if duplicate_evidence else 0,
            "member_event_count": sum(item["member_count"] for item in components) if duplicate_evidence else 0,
            "noncanonical_event_count": sum(item["member_count"] - 1 for item in components) if duplicate_evidence else 0,
            **consolidation_stats,
            "count_invariants": {
                "raw_event_count": len(event_sequences),
                "duplicate_relation_edge_count": duplicate_edge_count,
                "duplicate_component_occurrence_units": len(components),
                "input_observation_count": len(observation_rows),
                "projected_observation_group_count": len(projection_rows),
                "projected_groups_not_increased": len(projection_rows) <= len(observation_rows),
            }
            if duplicate_evidence
            else {},
        }
        self.connection.commit()
        return {
            "projection_run_id": projection_run_id,
            "projection_version": projection_version,
            "input_digest": digest,
            "duplicate_evidence": dict(self._last_duplicate_evidence_stats),
        }

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
        component_rows = self.connection.execute(
            "SELECT * FROM duplicate_components ORDER BY canonical_event_id, component_id"
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

        duplicate_components = [
            {
                "component_id": row["component_id"],
                "canonical_event_id": row["canonical_event_id"],
                "member_event_ids": json.loads(row["member_event_ids_json"]),
                "member_count": row["member_count"],
            }
            for row in component_rows
        ]

        relation_counts: dict[str, int] = {}
        for relation in relationships:
            relation_type = str(relation["relation_type"])
            relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1
        duplicate_groups = {
            relation.get("duplicate_group")
            for relation in relationships
            if relation.get("duplicate_group")
        }
        latest_projection = self.connection.execute(
            "SELECT projection_version FROM projection_runs ORDER BY projection_run_id DESC LIMIT 1"
        ).fetchone()
        projection_version = latest_projection["projection_version"] if latest_projection is not None else PROJECTION_VERSION
        duplicate_evidence_stats = dict(self._last_duplicate_evidence_stats)
        if not duplicate_components:
            duplicate_evidence_stats = {
                "enabled": False,
                "component_count": 0,
                "member_event_count": 0,
                "noncanonical_event_count": 0,
                "observations_recovered_from_duplicate_events": 0,
                "consolidated_identical_observations": 0,
                "conflicts_preserved": 0,
                "count_invariants": {},
            }
        return {
            "projection_version": projection_version,
            "current_facts": current,
            "history": history,
            "relationships": relationships,
            "duplicate_components": duplicate_components,
            "duplicate_evidence_stats": duplicate_evidence_stats,
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

    def extraction_context(self, *, max_sequence: int | None = None) -> dict[str, Any]:
        """Return a compact prior context for the next semantic batch."""

        snapshot = self.snapshot()
        event_index = snapshot["event_index"]
        if max_sequence is not None:
            event_index = [event for event in event_index if event["sequence"] <= max_sequence]
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
                for event in event_index[-40:]
            ],
        }
