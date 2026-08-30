"""Durable, rebuildable storage for the open-world Product V2 runtime.

The historical ``StateStore`` remains the V1 benchmark/product compatibility
store.  This module owns a separate Product V2 database so generic product
facts, attachments, and attention state cannot accidentally change the frozen
V1 projection.  Raw source rows and user retractions are append-only; current
views are replaceable projections with a recorded input digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


PRODUCT_STORE_VERSION = "blackhole-product-v2-store-v1"
PRODUCT_PROJECTION_VERSION = "blackhole-product-v2-projection-v1"
PRODUCT_PROCESSING_VERSION = "blackhole-product-v2-processing-v1"
PRODUCT_EXTRACTOR_VERSION = "blackhole-product-v2-extractor-v1"
PROCESSING_STATUSES = frozenset({"pending", "processing", "processed", "failed"})
ATTENTION_STATUSES = frozenset({"open", "completed", "cancelled"})


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime:
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    parsed = datetime.fromisoformat(candidate)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_error(error: Any) -> str:
    text = str(error).strip()
    return text[:1000] or "processing failed"


def _json_value(value: Any) -> str:
    return canonical_json(value)


def _legacy_key(value: Any) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE).strip("_")
    return text[:160] or "unknown_entity"


class BlobStore:
    """Content-addressed local blob store scoped to one Blackhole Home."""

    def __init__(self, home: str | Path) -> None:
        self.home = Path(home).expanduser().resolve()
        self.root = self.home / "blobs"
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for_hash(self, sha256: str) -> Path:
        if (
            not isinstance(sha256, str)
            or sha256 != sha256.casefold()
            or len(sha256) != 64
            or any(character not in "0123456789abcdef" for character in sha256)
        ):
            raise ValueError("attachment hash must be a lowercase SHA-256 digest")
        return self.root / sha256[:2] / sha256

    def put(self, content: bytes) -> tuple[str, int, Path]:
        if not isinstance(content, bytes):
            raise TypeError("attachment content must be bytes")
        digest = hashlib.sha256(content).hexdigest()
        destination = self.path_for_hash(digest)
        destination.parent.mkdir(parents=True, exist_ok=True)

        def verify_existing() -> None:
            existing = destination.read_bytes()
            if len(existing) != len(content) or hashlib.sha256(existing).hexdigest() != digest:
                raise IOError("content-addressed attachment integrity conflict")

        if destination.exists():
            verify_existing()
            return digest, len(content), destination

        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{digest}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_name = temporary.name
            temporary_path = Path(temporary_name)
            try:
                # A hard link publishes the already-fsynced temporary inode
                # without replacing an existing immutable blob.
                os.link(temporary_path, destination)
            except FileExistsError:
                # Another capture may have stored the same digest between the
                # existence check and the link. The bytes must still match.
                verify_existing()
        finally:
            if temporary_name is not None:
                Path(temporary_name).unlink(missing_ok=True)
        return digest, len(content), destination

    def read(self, sha256: str) -> bytes:
        path = self.path_for_hash(sha256)
        return path.read_bytes()


class ProductStore:
    """SQLite owner for Product V2 source, semantic, and attention state."""

    def __init__(
        self,
        path: str | Path,
        *,
        home: str | Path | None = None,
        legacy_database_path: str | Path | None = None,
        migrate_legacy: bool = True,
    ) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.home = Path(home or self.path.parent).expanduser().resolve()
        self.blobs = BlobStore(self.home)
        self.connection = sqlite3.connect(
            self.path,
            timeout=30,
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 30000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._lock = threading.RLock()
        self._create_schema()
        if migrate_legacy:
            self._migrate_legacy(legacy_database_path or (self.home / "blackhole.db"))

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def __enter__(self) -> "ProductStore":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @contextmanager
    def _transaction(self, *, immediate: bool = False) -> Iterator[None]:
        with self._lock:
            self.connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            try:
                yield
            except Exception:
                self.connection.rollback()
                raise
            else:
                self.connection.commit()

    def _create_schema(self) -> None:
        with self._lock:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS source_events (
                    event_id TEXT PRIMARY KEY,
                    sequence INTEGER NOT NULL UNIQUE CHECK(sequence > 0),
                    captured_at TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    observed_at TEXT,
                    source_type TEXT NOT NULL,
                    raw_json TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    inserted_at TEXT NOT NULL
                );

                CREATE TRIGGER IF NOT EXISTS product_source_events_no_update
                BEFORE UPDATE ON source_events
                BEGIN
                    SELECT RAISE(ABORT, 'Product V2 source events are immutable');
                END;

                CREATE TRIGGER IF NOT EXISTS product_source_events_no_delete
                BEFORE DELETE ON source_events
                BEGIN
                    SELECT RAISE(ABORT, 'Product V2 source events are immutable');
                END;

                CREATE TABLE IF NOT EXISTS attachment_blobs (
                    sha256 TEXT PRIMARY KEY,
                    relative_path TEXT NOT NULL UNIQUE,
                    byte_length INTEGER NOT NULL CHECK(byte_length >= 0),
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS event_attachments (
                    event_id TEXT NOT NULL REFERENCES source_events(event_id),
                    sha256 TEXT NOT NULL REFERENCES attachment_blobs(sha256),
                    attachment_index INTEGER NOT NULL CHECK(attachment_index >= 0),
                    original_filename TEXT,
                    mime_type TEXT NOT NULL,
                    byte_length INTEGER NOT NULL CHECK(byte_length >= 0),
                    processing_status TEXT NOT NULL DEFAULT 'unread',
                    processing_detail TEXT,
                    PRIMARY KEY(event_id, attachment_index)
                );

                CREATE TABLE IF NOT EXISTS processing_state (
                    event_id TEXT PRIMARY KEY REFERENCES source_events(event_id),
                    status TEXT NOT NULL CHECK(status IN ('pending', 'processing', 'processed', 'failed')),
                    processing_version TEXT NOT NULL,
                    owner_id TEXT,
                    lease_until TEXT,
                    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
                    last_attempted_at TEXT,
                    last_successful_at TEXT,
                    last_error TEXT,
                    next_retry_at TEXT,
                    extractor_version TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS retractions (
                    retraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE REFERENCES source_events(event_id),
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memory_facts (
                    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_event_id TEXT NOT NULL REFERENCES source_events(event_id),
                    entity_key TEXT NOT NULL,
                    entity_label TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    knowledge_status TEXT NOT NULL CHECK(knowledge_status IN ('known', 'inferred', 'unknown')),
                    value_json TEXT,
                    unknown_reason TEXT,
                    operation TEXT NOT NULL CHECK(operation IN ('set', 'correction', 'supersede', 'contradiction', 'duplicate')),
                    supersedes_event_id TEXT,
                    source_refs_json TEXT NOT NULL,
                    temporal_json TEXT NOT NULL,
                    extractor_version TEXT NOT NULL,
                    fingerprint TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memory_relations (
                    relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_event_id TEXT NOT NULL REFERENCES source_events(event_id),
                    source_entity_key TEXT,
                    relation_type TEXT NOT NULL,
                    target_entity_key TEXT,
                    target_event_id TEXT,
                    knowledge_status TEXT NOT NULL CHECK(knowledge_status IN ('known', 'inferred', 'unknown')),
                    value_json TEXT,
                    source_refs_json TEXT NOT NULL,
                    extractor_version TEXT NOT NULL,
                    fingerprint TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS attention_candidates (
                    candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_event_id TEXT NOT NULL REFERENCES source_events(event_id),
                    fingerprint TEXT NOT NULL UNIQUE,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('open', 'completed', 'cancelled')),
                    knowledge_status TEXT NOT NULL CHECK(knowledge_status IN ('known', 'inferred', 'unknown')),
                    starts_at TEXT,
                    due_at TEXT,
                    timezone TEXT NOT NULL,
                    source_refs_json TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    extractor_version TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS attention_status_events (
                    status_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('open', 'completed', 'cancelled')),
                    created_at TEXT NOT NULL,
                    note TEXT
                );

                CREATE TABLE IF NOT EXISTS current_facts (
                    entity_key TEXT NOT NULL,
                    entity_label TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    knowledge_status TEXT NOT NULL,
                    value_json TEXT,
                    unknown_reason TEXT,
                    source_refs_json TEXT NOT NULL,
                    latest_sequence INTEGER NOT NULL,
                    fact_ids_json TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    projection_run_id INTEGER NOT NULL,
                    PRIMARY KEY(entity_key, concept)
                );

                CREATE TABLE IF NOT EXISTS current_attention (
                    fingerprint TEXT PRIMARY KEY,
                    source_event_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    knowledge_status TEXT NOT NULL,
                    starts_at TEXT,
                    due_at TEXT,
                    timezone TEXT NOT NULL,
                    source_refs_json TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    projection_run_id INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projection_runs (
                    projection_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    projection_version TEXT NOT NULL,
                    input_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS migration_log (
                    migration_key TEXT PRIMARY KEY,
                    source_path TEXT,
                    imported_count INTEGER NOT NULL DEFAULT 0,
                    completed_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS product_processing_status_idx
                    ON processing_state(status, next_retry_at, lease_until);
                CREATE INDEX IF NOT EXISTS product_fact_entity_idx
                    ON memory_facts(entity_key, concept);
                CREATE INDEX IF NOT EXISTS product_fact_event_idx
                    ON memory_facts(source_event_id);
                CREATE INDEX IF NOT EXISTS product_attention_due_idx
                    ON current_attention(status, due_at);
                """
            )
            self.connection.commit()

    def _migrate_legacy(self, legacy_database_path: str | Path) -> None:
        """Copy legacy V1 raw/semantic records once, without mutating them.

        The legacy database is opened read-only.  A conflicting event ID is a
        hard migration error rather than an overwrite.  No benchmark expected
        output or evaluator table is read.
        """

        legacy_path = Path(legacy_database_path).expanduser().resolve()
        key = f"legacy-state-store:{legacy_path}"
        with self._lock:
            if self.connection.execute(
                "SELECT 1 FROM migration_log WHERE migration_key = ?", (key,)
            ).fetchone() is not None:
                return
        if not legacy_path.exists() or legacy_path.resolve() == self.path.resolve():
            return

        legacy: sqlite3.Connection | None = None
        imported = 0
        migrated_derived_event_ids: set[str] = set()
        try:
            legacy = sqlite3.connect(f"file:{legacy_path.as_posix()}?mode=ro", uri=True)
            legacy.row_factory = sqlite3.Row
            table_names = {
                str(row[0])
                for row in legacy.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            if "raw_events" not in table_names:
                return
            raw_rows = legacy.execute(
                "SELECT event_id, sequence, captured_at, observed_at, source_type, raw_json, payload_json, payload_sha256, metadata_json FROM raw_events ORDER BY sequence"
            ).fetchall()
            with self._transaction(immediate=True):
                for row in raw_rows:
                    existing = self.connection.execute(
                        "SELECT raw_json, sequence FROM source_events WHERE event_id = ?",
                        (row["event_id"],),
                    ).fetchone()
                    if existing is not None:
                        if json.loads(existing["raw_json"]) != json.loads(row["raw_json"]):
                            raise ValueError(
                                f"Product V2 migration conflict for event {row['event_id']}"
                            )
                        continue
                    payload_json = row["payload_json"]
                    if not isinstance(payload_json, str):
                        payload_json = canonical_json(json.loads(row["raw_json"]).get("payload", {}))
                    metadata_json = row["metadata_json"]
                    if not isinstance(metadata_json, str):
                        metadata_json = canonical_json({})
                    self.connection.execute(
                        """
                        INSERT INTO source_events(
                            event_id, sequence, captured_at, timezone, observed_at,
                            source_type, raw_json, payload_json, payload_sha256,
                            metadata_json, inserted_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["event_id"],
                            int(row["sequence"]),
                            str(row["captured_at"]),
                            "UTC",
                            row["observed_at"],
                            str(row["source_type"]),
                            row["raw_json"],
                            payload_json,
                            str(row["payload_sha256"]),
                            metadata_json,
                            utc_now(),
                        ),
                    )
                    self.connection.execute(
                        """
                        INSERT INTO processing_state(
                            event_id, status, processing_version, attempt_count,
                            updated_at
                        ) VALUES (?, 'pending', ?, 0, ?)
                        """,
                        (row["event_id"], PRODUCT_PROCESSING_VERSION, utc_now()),
                    )
                    imported += 1

                # Existing semantic observations are useful product memory,
                # but remain explicitly derived and can be superseded/rebuilt.
                if "observations" in table_names:
                    observation_rows = legacy.execute(
                        "SELECT o.*, r.sequence FROM observations o JOIN raw_events r ON r.event_id = o.event_id ORDER BY r.sequence, o.observation_id"
                    ).fetchall()
                    for row in observation_rows:
                        if self.connection.execute(
                            "SELECT 1 FROM source_events WHERE event_id = ?", (row["event_id"],)
                        ).fetchone() is None:
                            continue
                        self._insert_fact_locked(
                            {
                                "source_event_id": row["event_id"],
                                "entity_key": _legacy_key(row["subject"]),
                                "entity_label": str(row["subject"]),
                                "concept": _legacy_key(row["predicate"]),
                                "knowledge_status": str(row["knowledge_status"]),
                                "value": json.loads(row["value_json"]) if row["value_json"] else None,
                                "unknown_reason": row["unknown_reason"],
                                "operation": row["operation"] if row["operation"] in {"set", "correction", "supersede", "contradiction", "duplicate"} else "set",
                                "supersedes_event_id": row["supersedes_event_id"],
                                "source_refs": json.loads(row["source_refs_json"]),
                                "temporal": {},
                            },
                            extractor_version="legacy-v1-import",
                        )
                        migrated_derived_event_ids.add(str(row["event_id"]))
                if "relationships" in table_names:
                    relationship_rows = legacy.execute("SELECT * FROM relationships").fetchall()
                    for row in relationship_rows:
                        self._insert_relation_locked(
                            {
                                "source_event_id": row["source_event_id"],
                                "source_entity_key": None,
                                "relation_type": str(row["relation_type"]),
                                "target_event_id": row["target_event_id"],
                                "target_entity_key": None,
                                "knowledge_status": "known",
                                "value": {
                                    "changed_fields": json.loads(row["changed_fields_json"])
                                },
                                "source_refs": [row["source_event_id"]],
                            },
                            extractor_version="legacy-v1-import",
                        )
                        migrated_derived_event_ids.add(str(row["source_event_id"]))
                        if row["target_event_id"]:
                            migrated_derived_event_ids.add(str(row["target_event_id"]))
                # Imported V1 semantic rows are already a valid derived
                # representation. Do not make a migrated home call a provider
                # merely because its raw event came from the old store.
                for event_id in migrated_derived_event_ids:
                    self.connection.execute(
                        """
                        UPDATE processing_state
                        SET status = 'processed',
                            processing_version = 'legacy-v1-import',
                            last_successful_at = COALESCE(last_successful_at, ?),
                            last_error = NULL,
                            next_retry_at = NULL,
                            updated_at = ?
                        WHERE event_id = ? AND status = 'pending'
                        """,
                        (utc_now(), utc_now(), event_id),
                    )
                self._rebuild_derived_locked()
                self.connection.execute(
                    "INSERT INTO migration_log(migration_key, source_path, imported_count, completed_at) VALUES (?, ?, ?, ?)",
                    (key, str(legacy_path), imported, utc_now()),
                )
        except sqlite3.Error as error:
            raise RuntimeError(f"Product V2 migration could not read {legacy_path}") from error
        finally:
            if legacy is not None:
                legacy.close()

    @staticmethod
    def _row_json(row: sqlite3.Row, field: str, default: Any = None) -> Any:
        value = row[field]
        if value is None:
            return default
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default

    def next_sequence(self) -> int:
        with self._lock:
            row = self.connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence FROM source_events"
            ).fetchone()
            return int(row["next_sequence"])

    def insert_capture(
        self,
        event: dict[str, Any],
        *,
        attachments: list[dict[str, Any]] | None = None,
    ) -> bool:
        event_id = event.get("event_id")
        sequence = event.get("sequence")
        payload = event.get("payload")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("capture event_id must be a non-empty string")
        if sequence is not None and (
            isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1
        ):
            raise ValueError("capture sequence must be a positive integer")
        if not isinstance(payload, dict) or not payload:
            raise ValueError("capture payload must be a non-empty object")
        payload_json = canonical_json(payload)
        payload_sha256 = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        raw_json = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        attachment_rows = list(attachments or [])
        with self._transaction(immediate=True):
            existing = self.connection.execute(
                "SELECT raw_json FROM source_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            if existing is not None:
                if event.get("sequence") is None:
                    existing_event = json.loads(existing["raw_json"])
                    event["sequence"] = existing_event.get("sequence")
                    raw_json = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                if json.loads(existing["raw_json"]) != event:
                    raise ValueError(f"immutable Product V2 source conflict for {event_id}")
                return False
            if sequence is None:
                row = self.connection.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence FROM source_events"
                ).fetchone()
                sequence = int(row["next_sequence"])
                event["sequence"] = sequence
                raw_json = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            try:
                self.connection.execute(
                    """
                    INSERT INTO source_events(
                        event_id, sequence, captured_at, timezone, observed_at,
                        source_type, raw_json, payload_json, payload_sha256,
                        metadata_json, inserted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        sequence,
                        str(event.get("captured_at", "")),
                        str(event.get("timezone", "UTC")),
                        event.get("observed_at"),
                        str(event.get("source_type", "text")),
                        raw_json,
                        payload_json,
                        payload_sha256,
                        canonical_json(event.get("metadata", {})),
                        utc_now(),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError(f"capture sequence conflict for {event_id}") from error
            self.connection.execute(
                "INSERT INTO processing_state(event_id, status, processing_version, attempt_count, updated_at) VALUES (?, 'pending', ?, 0, ?)",
                (event_id, PRODUCT_PROCESSING_VERSION, utc_now()),
            )
            for index, attachment in enumerate(attachment_rows):
                sha256 = attachment.get("sha256")
                if not isinstance(sha256, str):
                    raise ValueError("attachment hash is required")
                blob = self.blobs.path_for_hash(sha256)
                if not blob.is_file():
                    raise ValueError("attachment blob is missing")
                byte_length = int(attachment.get("byte_length", -1))
                if byte_length < 0 or blob.stat().st_size != byte_length:
                    raise ValueError("attachment byte length does not match blob")
                self.connection.execute(
                    "INSERT OR IGNORE INTO attachment_blobs(sha256, relative_path, byte_length, created_at) VALUES (?, ?, ?, ?)",
                    (sha256, blob.relative_to(self.home).as_posix(), byte_length, utc_now()),
                )
                self.connection.execute(
                    """
                    INSERT INTO event_attachments(
                        event_id, sha256, attachment_index, original_filename,
                        mime_type, byte_length, processing_status, processing_detail
                    ) VALUES (?, ?, ?, ?, ?, ?, 'unread', NULL)
                    """,
                    (
                        event_id,
                        sha256,
                        index,
                        attachment.get("original_filename"),
                        str(attachment.get("mime_type", "application/octet-stream")),
                        byte_length,
                    ),
                )
        return True

    def raw_event(self, event_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self.connection.execute(
                "SELECT raw_json FROM source_events WHERE event_id = ?", (event_id,)
            ).fetchone()
            return json.loads(row["raw_json"]) if row is not None else None

    def raw_events(self, *, max_sequence: int | None = None) -> list[dict[str, Any]]:
        with self._lock:
            query = "SELECT raw_json FROM source_events"
            params: tuple[Any, ...] = ()
            if max_sequence is not None:
                query += " WHERE sequence <= ?"
                params = (max_sequence,)
            query += " ORDER BY sequence"
            return [json.loads(row["raw_json"]) for row in self.connection.execute(query, params).fetchall()]

    def attachments_for_event(self, event_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT a.*, b.relative_path
                FROM event_attachments a JOIN attachment_blobs b ON b.sha256 = a.sha256
                WHERE a.event_id = ? ORDER BY a.attachment_index
                """,
                (event_id,),
            ).fetchall()
            return [
                {
                    "sha256": row["sha256"],
                    "blob_ref": f"sha256:{row['sha256']}",
                    "relative_path": row["relative_path"],
                    "path": str(self.home / row["relative_path"]),
                    "attachment_index": row["attachment_index"],
                    "original_filename": row["original_filename"],
                    "mime_type": row["mime_type"],
                    "byte_length": row["byte_length"],
                    "processing_status": row["processing_status"],
                    "processing_detail": row["processing_detail"],
                }
                for row in rows
            ]

    def record_attachment_processing(
        self,
        event_id: str,
        sha256: str,
        *,
        status: str,
        detail: str | None = None,
    ) -> None:
        """Record a truthful derived read result for one stored attachment."""

        allowed = {"unread", "read", "unsupported", "unreadable"}
        if status not in allowed:
            raise ValueError("unsupported attachment processing status")
        with self._transaction(immediate=True):
            self.connection.execute(
                """
                UPDATE event_attachments
                SET processing_status = ?, processing_detail = ?
                WHERE event_id = ? AND sha256 = ?
                """,
                (status, detail[:500] if isinstance(detail, str) else None, event_id, sha256),
            )

    def _processing_record(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "event_id": row["event_id"],
            "sequence": row["sequence"],
            "status": row["status"],
            "processing_version": row["processing_version"],
            "owner_id": row["owner_id"],
            "lease_until": row["lease_until"],
            "attempt_count": row["attempt_count"],
            "last_attempted_at": row["last_attempted_at"],
            "last_successful_at": row["last_successful_at"],
            "last_error": row["last_error"],
            "next_retry_at": row["next_retry_at"],
            "extractor_version": row["extractor_version"],
            "updated_at": row["updated_at"],
        }

    def processing_status(self, event_id: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            query = "SELECT p.*, s.sequence FROM processing_state p JOIN source_events s ON s.event_id = p.event_id"
            if event_id is not None:
                row = self.connection.execute(query + " WHERE p.event_id = ?", (event_id,)).fetchone()
                return self._processing_record(row) if row is not None else None
            rows = self.connection.execute(query + " ORDER BY s.sequence").fetchall()
            records = [self._processing_record(row) for row in rows]
            counts = {status: 0 for status in sorted(PROCESSING_STATUSES)}
            for record in records:
                if record["status"] in counts:
                    counts[record["status"]] += 1
            return {"counts": counts, "events": records}

    def recover_stale_processing(self, *, now: str | None = None) -> int:
        current = _parse_iso(now or utc_now())
        with self._transaction(immediate=True):
            rows = self.connection.execute(
                "SELECT event_id, lease_until FROM processing_state WHERE status = 'processing'"
            ).fetchall()
            stale = [
                row["event_id"]
                for row in rows
                if not row["lease_until"] or _parse_iso(str(row["lease_until"])) <= current
            ]
            for event_id in stale:
                self.connection.execute(
                    """
                    UPDATE processing_state
                    SET status = 'pending', owner_id = NULL, lease_until = NULL,
                        last_error = 'processing lease expired; retry available',
                        next_retry_at = NULL, updated_at = ?
                    WHERE event_id = ? AND status = 'processing'
                    """,
                    (utc_now(), event_id),
                )
            return len(stale)

    def _claim(
        self,
        owner_id: str,
        *,
        limit: int,
        lease_seconds: int,
        include_failed: bool = False,
    ) -> list[dict[str, Any]]:
        if limit < 1:
            return []
        self.recover_stale_processing()
        now = datetime.now(timezone.utc)
        lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
        now_text = now.isoformat()
        statuses = ["pending"] + (["failed"] if include_failed else [])
        placeholders = ",".join("?" for _ in statuses)
        with self._transaction(immediate=True):
            rows = self.connection.execute(
                f"""
                SELECT s.raw_json, p.event_id
                FROM processing_state p JOIN source_events s ON s.event_id = p.event_id
                WHERE p.status IN ({placeholders})
                  AND (p.next_retry_at IS NULL OR p.next_retry_at <= ?)
                ORDER BY s.sequence LIMIT ?
                """,
                (*statuses, now_text, limit),
            ).fetchall()
            claimed: list[dict[str, Any]] = []
            claimed_ids: set[str] = set()
            for row in rows:
                earlier = self.connection.execute(
                    """
                    SELECT p.event_id
                    FROM processing_state p JOIN source_events s ON s.event_id = p.event_id
                    WHERE s.sequence < (
                        SELECT sequence FROM source_events WHERE event_id = ?
                    ) AND p.status <> 'processed'
                    """,
                    (row["event_id"],),
                ).fetchall()
                # A later event must wait behind an earlier event owned by
                # another worker, including a failed event awaiting retry.
                # Events claimed in this same transaction are the only
                # exception, which preserves chronological bounded batches.
                if any(item["event_id"] not in claimed_ids for item in earlier):
                    continue
                cursor = self.connection.execute(
                    f"""
                    UPDATE processing_state
                    SET status = 'processing', owner_id = ?, lease_until = ?,
                        attempt_count = attempt_count + 1, last_attempted_at = ?,
                        last_error = NULL, updated_at = ?
                    WHERE event_id = ? AND status IN ({placeholders})
                      AND (next_retry_at IS NULL OR next_retry_at <= ?)
                    """,
                    (owner_id, lease_until, now_text, now_text, row["event_id"], *statuses, now_text),
                )
                if cursor.rowcount:
                    event = json.loads(row["raw_json"])
                    event["attachments"] = self.attachments_for_event(str(row["event_id"]))
                    claimed.append(event)
                    claimed_ids.add(str(row["event_id"]))
            return claimed

    def claim_pending(self, owner_id: str, *, limit: int = 1, lease_seconds: int = 120) -> list[dict[str, Any]]:
        return self._claim(owner_id, limit=limit, lease_seconds=lease_seconds)

    def claim_failed(self, owner_id: str, *, limit: int = 1, lease_seconds: int = 120) -> list[dict[str, Any]]:
        return self._claim(owner_id, limit=limit, lease_seconds=lease_seconds, include_failed=True)

    def retry_failed(self, event_id: str | None = None, *, limit: int | None = None) -> int:
        with self._transaction(immediate=True):
            query = "SELECT event_id FROM processing_state WHERE status = 'failed' ORDER BY event_id"
            params: list[Any] = []
            if event_id is not None:
                query = "SELECT event_id FROM processing_state WHERE status = 'failed' AND event_id = ?"
                params = [event_id]
            if limit is not None:
                if limit < 0:
                    raise ValueError("limit must be non-negative")
                query += " LIMIT ?"
                params.append(limit)
            ids = [row["event_id"] for row in self.connection.execute(query, params).fetchall()]
            for selected in ids:
                self.connection.execute(
                    """
                    UPDATE processing_state
                    SET status = 'pending', owner_id = NULL, lease_until = NULL,
                        last_error = NULL, next_retry_at = NULL, updated_at = ?
                    WHERE event_id = ? AND status = 'failed'
                    """,
                    (utc_now(), selected),
                )
            return len(ids)

    def _insert_fact_locked(self, item: dict[str, Any], *, extractor_version: str) -> bool:
        event_id = item["source_event_id"]
        source_refs = sorted(
            {ref for ref in item.get("source_refs", []) if isinstance(ref, str) and ref}
            | {event_id}
        )
        status = item["knowledge_status"]
        value = None if status == "unknown" else item.get("value")
        unknown_reason = item.get("unknown_reason") if status == "unknown" else None
        operation = item.get("operation", "set")
        if operation not in {"set", "correction", "supersede", "contradiction", "duplicate"}:
            operation = "set"
        fingerprint_input = {
            "source_event_id": event_id,
            "entity_key": item["entity_key"],
            "entity_label": item.get("entity_label", item["entity_key"]),
            "concept": item["concept"],
            "knowledge_status": status,
            "value": value,
            "unknown_reason": unknown_reason,
            "operation": operation,
            "supersedes_event_id": item.get("supersedes_event_id"),
            "source_refs": source_refs,
            "temporal": item.get("temporal", {}),
        }
        fingerprint = hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO memory_facts(
                source_event_id, entity_key, entity_label, concept,
                knowledge_status, value_json, unknown_reason, operation,
                supersedes_event_id, source_refs_json, temporal_json,
                extractor_version, fingerprint, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                item["entity_key"],
                item.get("entity_label", item["entity_key"]),
                item["concept"],
                status,
                _json_value(value) if value is not None else None,
                unknown_reason,
                operation,
                item.get("supersedes_event_id"),
                canonical_json(source_refs),
                canonical_json(item.get("temporal", {})),
                extractor_version,
                fingerprint,
                utc_now(),
            ),
        )
        return bool(cursor.rowcount)

    def _insert_relation_locked(self, item: dict[str, Any], *, extractor_version: str) -> bool:
        event_id = item["source_event_id"]
        source_refs = sorted(
            {ref for ref in item.get("source_refs", []) if isinstance(ref, str) and ref}
            | {event_id}
        )
        fingerprint_input = {
            "source_event_id": event_id,
            "source_entity_key": item.get("source_entity_key"),
            "relation_type": item["relation_type"],
            "target_entity_key": item.get("target_entity_key"),
            "target_event_id": item.get("target_event_id"),
            "knowledge_status": item.get("knowledge_status", "known"),
            "value": item.get("value"),
            "source_refs": source_refs,
        }
        fingerprint = hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO memory_relations(
                source_event_id, source_entity_key, relation_type,
                target_entity_key, target_event_id, knowledge_status,
                value_json, source_refs_json, extractor_version, fingerprint,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                item.get("source_entity_key"),
                item["relation_type"],
                item.get("target_entity_key"),
                item.get("target_event_id"),
                item.get("knowledge_status", "known"),
                _json_value(item.get("value")) if item.get("value") is not None else None,
                canonical_json(source_refs),
                extractor_version,
                fingerprint,
                utc_now(),
            ),
        )
        return bool(cursor.rowcount)

    def _insert_attention_locked(self, item: dict[str, Any], *, extractor_version: str) -> bool:
        fingerprint_input = {
            "source_event_id": item["source_event_id"],
            "kind": item["kind"],
            "title": item["title"],
            "status": item["status"],
            "knowledge_status": item["knowledge_status"],
            "starts_at": item.get("starts_at"),
            "due_at": item.get("due_at"),
            "timezone": item["timezone"],
            "source_refs": sorted(set(item.get("source_refs", []))),
            "details": item.get("details", {}),
        }
        fingerprint = hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO attention_candidates(
                source_event_id, fingerprint, kind, title, status,
                knowledge_status, starts_at, due_at, timezone,
                source_refs_json, details_json, extractor_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["source_event_id"],
                fingerprint,
                item["kind"],
                item["title"],
                item["status"],
                item["knowledge_status"],
                item.get("starts_at"),
                item.get("due_at"),
                item["timezone"],
                canonical_json(sorted(set(item.get("source_refs", []))) or [item["source_event_id"]]),
                canonical_json(item.get("details", {})),
                extractor_version,
                utc_now(),
            ),
        )
        return bool(cursor.rowcount)

    def commit_semantic(
        self,
        owner_id: str,
        event_ids: Iterable[str],
        *,
        facts: Iterable[dict[str, Any]],
        relations: Iterable[dict[str, Any]],
        attention: Iterable[dict[str, Any]],
        extractor_version: str,
    ) -> dict[str, Any]:
        selected_ids = [event_id for event_id in event_ids if isinstance(event_id, str)]
        with self._transaction(immediate=True):
            if selected_ids:
                placeholders = ",".join("?" for _ in selected_ids)
                claimed = self.connection.execute(
                    f"SELECT event_id FROM processing_state WHERE event_id IN ({placeholders}) AND status = 'processing' AND owner_id = ?",
                    (*selected_ids, owner_id),
                ).fetchall()
                if {row["event_id"] for row in claimed} != set(selected_ids):
                    raise RuntimeError("processing lease is no longer owned")
            facts_added = sum(
                self._insert_fact_locked(item, extractor_version=extractor_version)
                for item in facts
            )
            relations_added = sum(
                self._insert_relation_locked(item, extractor_version=extractor_version)
                for item in relations
            )
            attention_added = sum(
                self._insert_attention_locked(item, extractor_version=extractor_version)
                for item in attention
            )
            projection = self._rebuild_derived_locked()
            for event_id in selected_ids:
                self.connection.execute(
                    """
                    UPDATE processing_state
                    SET status = 'processed', owner_id = NULL, lease_until = NULL,
                        last_successful_at = ?, last_error = NULL, next_retry_at = NULL,
                        extractor_version = ?, updated_at = ?
                    WHERE event_id = ? AND status = 'processing' AND owner_id = ?
                    """,
                    (utc_now(), extractor_version, utc_now(), event_id, owner_id),
                )
            return {
                "facts_added": facts_added,
                "relations_added": relations_added,
                "attention_added": attention_added,
                "projection_run_id": projection["projection_run_id"],
                "projection_version": projection["projection_version"],
            }

    def mark_failed(
        self,
        owner_id: str,
        event_ids: Iterable[str],
        *,
        error: str,
        retry_after_seconds: int = 0,
    ) -> int:
        ids = [event_id for event_id in event_ids if isinstance(event_id, str)]
        next_retry = None
        if retry_after_seconds > 0:
            next_retry = (datetime.now(timezone.utc) + timedelta(seconds=retry_after_seconds)).isoformat()
        with self._transaction(immediate=True):
            updated = 0
            for event_id in ids:
                cursor = self.connection.execute(
                    """
                    UPDATE processing_state
                    SET status = 'failed', owner_id = NULL, lease_until = NULL,
                        last_error = ?, next_retry_at = ?, updated_at = ?
                    WHERE event_id = ? AND status = 'processing' AND owner_id = ?
                    """,
                    (_safe_error(error), next_retry, utc_now(), event_id, owner_id),
                )
                updated += int(cursor.rowcount > 0)
            return updated

    def retract(self, event_id: str, *, reason: str = "user undo") -> dict[str, Any]:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("retraction reason must not be empty")
        with self._transaction(immediate=True):
            if self.connection.execute(
                "SELECT 1 FROM source_events WHERE event_id = ?", (event_id,)
            ).fetchone() is None:
                raise ValueError(f"unknown event: {event_id}")
            cursor = self.connection.execute(
                "INSERT OR IGNORE INTO retractions(event_id, reason, created_at) VALUES (?, ?, ?)",
                (event_id, reason.strip()[:500], utc_now()),
            )
            projection = self._rebuild_derived_locked()
            return {
                "event_id": event_id,
                "retracted": True,
                "already_retracted": not bool(cursor.rowcount),
                "projection_run_id": projection["projection_run_id"],
            }

    def set_attention_status(
        self,
        fingerprint: str,
        status: str,
        *,
        note: str | None = None,
    ) -> dict[str, Any]:
        if status not in ATTENTION_STATUSES:
            raise ValueError("attention status must be open, completed, or cancelled")
        with self._transaction(immediate=True):
            if self.connection.execute(
                "SELECT 1 FROM attention_candidates WHERE fingerprint = ?", (fingerprint,)
            ).fetchone() is None:
                raise ValueError(f"unknown attention item: {fingerprint}")
            self.connection.execute(
                "INSERT INTO attention_status_events(candidate_fingerprint, status, created_at, note) VALUES (?, ?, ?, ?)",
                (fingerprint, status, utc_now(), note[:500] if isinstance(note, str) else None),
            )
            projection = self._rebuild_derived_locked()
            return {"fingerprint": fingerprint, "status": status, "projection_run_id": projection["projection_run_id"]}

    def _retracted_event_ids_locked(self) -> set[str]:
        return {row["event_id"] for row in self.connection.execute("SELECT event_id FROM retractions").fetchall()}

    def _rebuild_derived_locked(self) -> dict[str, Any]:
        retracted = self._retracted_event_ids_locked()
        fact_rows = self.connection.execute(
            """
            SELECT f.*, s.sequence
            FROM memory_facts f JOIN source_events s ON s.event_id = f.source_event_id
            ORDER BY s.sequence, f.fact_id
            """
        ).fetchall()
        relation_rows = self.connection.execute(
            "SELECT * FROM memory_relations ORDER BY relation_id"
        ).fetchall()
        attention_rows = self.connection.execute(
            "SELECT * FROM attention_candidates ORDER BY candidate_id"
        ).fetchall()
        status_rows = self.connection.execute(
            "SELECT * FROM attention_status_events ORDER BY status_event_id"
        ).fetchall()
        digest_input = {
            "facts": [dict(row) for row in fact_rows],
            "relations": [dict(row) for row in relation_rows],
            "attention": [dict(row) for row in attention_rows],
            "attention_status": [dict(row) for row in status_rows],
            "retractions": sorted(retracted),
        }
        digest = hashlib.sha256(canonical_json(digest_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            "INSERT INTO projection_runs(projection_version, input_digest, created_at) VALUES (?, ?, ?)",
            (PRODUCT_PROJECTION_VERSION, digest, utc_now()),
        )
        projection_run_id = int(cursor.lastrowid)
        self.connection.execute("DELETE FROM current_facts")
        self.connection.execute("DELETE FROM current_attention")

        grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for row in fact_rows:
            if row["source_event_id"] in retracted:
                continue
            grouped.setdefault((row["entity_key"], row["concept"]), []).append(row)

        for (entity_key, concept), rows in grouped.items():
            superseded_event_ids = {
                row["supersedes_event_id"]
                for row in rows
                if row["supersedes_event_id"] and row["supersedes_event_id"] not in retracted
            }
            active = [row for row in rows if row["source_event_id"] not in superseded_event_ids]
            if not active:
                continue
            active.sort(key=lambda row: (int(row["sequence"]), int(row["fact_id"])))
            known_values = {
                canonical_json(json.loads(row["value_json"]))
                for row in active
                if row["knowledge_status"] != "unknown" and row["value_json"] is not None
            }
            source_refs = sorted(
                {
                    reference
                    for row in active
                    for reference in json.loads(row["source_refs_json"])
                    if isinstance(reference, str) and reference
                }
            )
            latest = active[-1]
            if len(known_values) > 1:
                output_status = "unknown"
                output_value = None
                output_reason = "conflicting"
                output_operation = "contradiction"
            elif not known_values:
                output_status = "unknown"
                output_value = None
                output_reason = next(
                    (row["unknown_reason"] for row in reversed(active) if row["unknown_reason"]),
                    "not_stated",
                )
                output_operation = "set"
            else:
                candidate = next(
                    row
                    for row in reversed(active)
                    if row["knowledge_status"] != "unknown" and row["value_json"] is not None
                )
                output_status = candidate["knowledge_status"]
                output_value = candidate["value_json"]
                output_reason = None
                output_operation = candidate["operation"]
                if any(row["knowledge_status"] == "unknown" for row in active):
                    output_status = "unknown"
                    output_value = None
                    output_reason = "ambiguous"
                    output_operation = "contradiction"
            self.connection.execute(
                """
                INSERT INTO current_facts(
                    entity_key, entity_label, concept, knowledge_status,
                    value_json, unknown_reason, source_refs_json,
                    latest_sequence, fact_ids_json, operation, projection_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_key,
                    latest["entity_label"],
                    concept,
                    output_status,
                    output_value,
                    output_reason,
                    canonical_json(source_refs),
                    latest["sequence"],
                    canonical_json([row["fact_id"] for row in active]),
                    output_operation,
                    projection_run_id,
                ),
            )

        latest_attention_status: dict[str, str] = {}
        for row in status_rows:
            latest_attention_status[row["candidate_fingerprint"]] = row["status"]
        for row in attention_rows:
            if row["source_event_id"] in retracted:
                continue
            status = latest_attention_status.get(row["fingerprint"], row["status"])
            self.connection.execute(
                """
                INSERT INTO current_attention(
                    fingerprint, source_event_id, kind, title, status,
                    knowledge_status, starts_at, due_at, timezone,
                    source_refs_json, details_json, projection_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["fingerprint"],
                    row["source_event_id"],
                    row["kind"],
                    row["title"],
                    status,
                    row["knowledge_status"],
                    row["starts_at"],
                    row["due_at"],
                    row["timezone"],
                    row["source_refs_json"],
                    row["details_json"],
                    projection_run_id,
                ),
            )
        return {
            "projection_run_id": projection_run_id,
            "projection_version": PRODUCT_PROJECTION_VERSION,
            "input_digest": digest,
        }

    def rebuild(self) -> dict[str, Any]:
        with self._transaction(immediate=True):
            return self._rebuild_derived_locked()

    @staticmethod
    def _fact_dict(row: sqlite3.Row, *, current: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "entity_key": row["entity_key"],
            "entity_label": row["entity_label"],
            "concept": row["concept"],
            "knowledge_status": row["knowledge_status"],
            "source_refs": json.loads(row["source_refs_json"]),
        }
        if current:
            result.update(
                {
                    "latest_sequence": row["latest_sequence"],
                    "operation": row["operation"],
                    "fact_ids": json.loads(row["fact_ids_json"]),
                }
            )
        else:
            result.update(
                {
                    "fact_id": row["fact_id"],
                    "source_event_id": row["source_event_id"],
                    "operation": row["operation"],
                    "temporal": json.loads(row["temporal_json"]),
                    "extractor_version": row["extractor_version"],
                    "created_at": row["created_at"],
                }
            )
            if row["supersedes_event_id"]:
                result["supersedes_event_id"] = row["supersedes_event_id"]
            result["sequence"] = row["sequence"]
            result["retracted"] = bool(row["source_event_id"] in row["retracted_event_ids"])
        if row["knowledge_status"] == "unknown":
            result["unknown_reason"] = row["unknown_reason"] or "not_stated"
        elif row["value_json"] is not None:
            result["value"] = json.loads(row["value_json"])
        return result

    def snapshot(self, *, now: datetime | None = None) -> dict[str, Any]:
        with self._lock:
            current_time = now or datetime.now(timezone.utc)
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
            current_time = current_time.astimezone(timezone.utc)
            retracted = self._retracted_event_ids_locked()
            current_rows = self.connection.execute(
                "SELECT * FROM current_facts ORDER BY entity_key, concept"
            ).fetchall()
            history_rows = self.connection.execute(
                """
                SELECT f.*, s.sequence
                FROM memory_facts f JOIN source_events s ON s.event_id = f.source_event_id
                ORDER BY s.sequence, f.fact_id
                """
            ).fetchall()
            history: list[dict[str, Any]] = []
            for row in history_rows:
                result = self._fact_dict(
                    {**dict(row), "retracted_event_ids": retracted}  # type: ignore[arg-type]
                )
                history.append(result)
            relation_rows = self.connection.execute(
                """
                SELECT r.*, s.sequence
                FROM memory_relations r JOIN source_events s ON s.event_id = r.source_event_id
                ORDER BY s.sequence, r.relation_id
                """
            ).fetchall()
            relations = []
            for row in relation_rows:
                item = {
                    "relation_id": row["relation_id"],
                    "source_event_id": row["source_event_id"],
                    "source_entity_key": row["source_entity_key"],
                    "relation_type": row["relation_type"],
                    "target_entity_key": row["target_entity_key"],
                    "target_event_id": row["target_event_id"],
                    "knowledge_status": row["knowledge_status"],
                    "source_refs": json.loads(row["source_refs_json"]),
                    "sequence": row["sequence"],
                    "retracted": row["source_event_id"] in retracted,
                }
                if row["value_json"] is not None:
                    item["value"] = json.loads(row["value_json"])
                relations.append(item)
            attention_rows = self.connection.execute(
                "SELECT * FROM current_attention ORDER BY due_at IS NULL, due_at, fingerprint"
            ).fetchall()
            attention = []
            for row in attention_rows:
                item = {
                    "fingerprint": row["fingerprint"],
                    "source_event_id": row["source_event_id"],
                    "kind": row["kind"],
                    "title": row["title"],
                    "status": row["status"],
                    "knowledge_status": row["knowledge_status"],
                    "starts_at": row["starts_at"],
                    "due_at": row["due_at"],
                    "timezone": row["timezone"],
                    "source_refs": json.loads(row["source_refs_json"]),
                    "details": json.loads(row["details_json"]),
                }
                if row["status"] == "open":
                    try:
                        due = _parse_iso(row["due_at"]) if row["due_at"] else None
                        item["state"] = "overdue" if due is not None and due <= current_time else "upcoming"
                    except (TypeError, ValueError):
                        item["state"] = "undated"
                else:
                    item["state"] = row["status"]
                attention.append(item)
            source_rows = self.connection.execute(
                "SELECT event_id, sequence, captured_at, timezone, observed_at, source_type FROM source_events ORDER BY sequence"
            ).fetchall()
            sources = [
                {
                    "event_id": row["event_id"],
                    "sequence": row["sequence"],
                    "captured_at": row["captured_at"],
                    "timezone": row["timezone"],
                    "observed_at": row["observed_at"],
                    "source_type": row["source_type"],
                    "retracted": row["event_id"] in retracted,
                }
                for row in source_rows
            ]
            attachment_rows = self.connection.execute(
                """
                SELECT a.*, b.relative_path
                FROM event_attachments a JOIN attachment_blobs b ON b.sha256 = a.sha256
                ORDER BY a.event_id, a.attachment_index
                """
            ).fetchall()
            attachments = [
                {
                    "event_id": row["event_id"],
                    "sha256": row["sha256"],
                    "blob_ref": f"sha256:{row['sha256']}",
                    "original_filename": row["original_filename"],
                    "mime_type": row["mime_type"],
                    "byte_length": row["byte_length"],
                    "processing_status": row["processing_status"],
                    "processing_detail": row["processing_detail"],
                }
                for row in attachment_rows
            ]
            latest_projection = self.connection.execute(
                "SELECT * FROM projection_runs ORDER BY projection_run_id DESC LIMIT 1"
            ).fetchone()
            processing = self.processing_status() or {"counts": {}, "events": []}
            entities: dict[str, dict[str, Any]] = {}
            for row in current_rows:
                entity = entities.setdefault(
                    row["entity_key"],
                    {
                        "entity_key": row["entity_key"],
                        "label": row["entity_label"],
                        "source_refs": [],
                    },
                )
                entity["source_refs"] = sorted(
                    set(entity["source_refs"])
                    | set(json.loads(row["source_refs_json"]))
                )
            return {
                "store_version": PRODUCT_STORE_VERSION,
                "projection_version": latest_projection["projection_version"] if latest_projection else PRODUCT_PROJECTION_VERSION,
                "projection_run_id": latest_projection["projection_run_id"] if latest_projection else None,
                "counts": {
                    "captures": len(sources),
                    "active_captures": sum(not item["retracted"] for item in sources),
                    "facts": len(current_rows),
                    "fact_history": len(history),
                    "entities": len(entities),
                    "relationships": len(relations),
                    "attention": len(attention),
                    "attachments": len(attachments),
                },
                "entities": list(entities.values()),
                "facts": [self._fact_dict(row, current=True) for row in current_rows],
                "current_facts": [self._fact_dict(row, current=True) for row in current_rows],
                "fact_history": history,
                "relationships": relations,
                "attention": attention,
                "sources": sources,
                "attachments": attachments,
                "processing": processing,
                "retracted_event_ids": sorted(retracted),
            }

    def search_rows(self, *, now: datetime | None = None) -> dict[str, list[dict[str, Any]]]:
        """Return bounded structured retrieval rows without raw-history replay."""

        snapshot = self.snapshot(now=now)
        active_history = [row for row in snapshot["fact_history"] if not row.get("retracted")]
        return {
            "facts": snapshot["current_facts"],
            "fact_history": active_history,
            "attention": snapshot["attention"],
            "sources": [row for row in snapshot["sources"] if not row["retracted"]],
            "relationships": [row for row in snapshot["relationships"] if not row["retracted"]],
        }

    def blob_path(self, sha256: str) -> Path:
        with self._lock:
            row = self.connection.execute(
                "SELECT relative_path FROM attachment_blobs WHERE sha256 = ?", (sha256,)
            ).fetchone()
            if row is None:
                raise FileNotFoundError(sha256)
            path = (self.home / row["relative_path"]).resolve()
            try:
                path.relative_to(self.blobs.root.resolve())
            except ValueError as error:
                raise RuntimeError("attachment path escaped blob store") from error
            return path

    def attachment_bytes(self, sha256: str) -> tuple[bytes, dict[str, Any]]:
        path = self.blob_path(sha256)
        with self._lock:
            row = self.connection.execute(
                """
                SELECT a.original_filename, a.mime_type, a.byte_length
                FROM event_attachments a WHERE a.sha256 = ?
                ORDER BY a.event_id, a.attachment_index LIMIT 1
                """,
                (sha256,),
            ).fetchone()
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != sha256:
            raise IOError("attachment blob integrity check failed")
        return content, {
            "sha256": sha256,
            "original_filename": row["original_filename"] if row else None,
            "mime_type": row["mime_type"] if row else "application/octet-stream",
            "byte_length": len(content),
        }


__all__ = [
    "ATTENTION_STATUSES",
    "BlobStore",
    "PRODUCT_EXTRACTOR_VERSION",
    "PRODUCT_PROCESSING_VERSION",
    "PRODUCT_PROJECTION_VERSION",
    "PRODUCT_STORE_VERSION",
    "ProductStore",
    "canonical_json",
    "utc_now",
]
