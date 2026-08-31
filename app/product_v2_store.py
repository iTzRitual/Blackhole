"""Durable, rebuildable storage for the open-world Product V2 runtime.

The historical ``StateStore`` remains the V1 benchmark/product compatibility
store.  This module owns a separate Product V2 database so generic product
facts, attachments, and attention state cannot accidentally change the frozen
V1 projection.  Raw source rows are immutable during normal processing and
history operations; an explicit user Undo is the one supported destructive
operation and permanently forgets that capture. Current views are replaceable
projections with a recorded input digest.
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


PRODUCT_STORE_VERSION = "blackhole-product-v2-store-v3"
PRODUCT_PROJECTION_VERSION = "blackhole-product-v2-projection-v3"
PRODUCT_PROCESSING_VERSION = "blackhole-product-v2-processing-v1"
PRODUCT_EXTRACTOR_VERSION = "blackhole-product-v2-extractor-v3"
PROCESSING_STATUSES = frozenset({"pending", "processing", "processed", "failed"})
ATTENTION_STATUSES = frozenset({"open", "completed", "cancelled"})
# Automatic retries are deliberately finite.  The first claim is an attempt;
# four durable delays permit five automatic attempts in total.  An explicit
# user retry requeues the event and remains available after the automatic cap.
AUTOMATIC_RETRY_BACKOFF_SECONDS = (1, 2, 4, 8)
MAX_AUTOMATIC_ATTEMPTS = len(AUTOMATIC_RETRY_BACKOFF_SECONDS) + 1


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


def _attention_timestamp_key(value: Any) -> str:
    """Return a stable instant key without changing the stored timestamp."""

    if not isinstance(value, str) or not value.strip():
        return ""
    try:
        return _parse_iso(value).isoformat()
    except (TypeError, ValueError):
        return value.strip().casefold()


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
            # Product V2 source rows are still immutable during normal runtime
            # operations. Explicit user forget is implemented below as the
            # narrowly-scoped deletion capability, so the original blanket
            # DELETE trigger must not remain on databases created by an older
            # Product V2 build.
            self.connection.execute("DROP TRIGGER IF EXISTS product_source_events_no_delete")
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

                CREATE TABLE IF NOT EXISTS deleted_events (
                    event_id TEXT PRIMARY KEY,
                    deleted_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS product_delete_authorizations (
                    event_id TEXT PRIMARY KEY
                );

                CREATE TRIGGER IF NOT EXISTS product_source_events_no_delete
                BEFORE DELETE ON source_events
                WHEN NOT EXISTS (
                    SELECT 1 FROM product_delete_authorizations
                    WHERE event_id = OLD.event_id
                )
                BEGIN
                    SELECT RAISE(ABORT, 'Product V2 source events are immutable outside explicit Undo');
                END;

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
                    metadata_json TEXT NOT NULL DEFAULT '{}',
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
                    metadata_json TEXT NOT NULL DEFAULT '{}',
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
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    operation TEXT NOT NULL,
                    projection_run_id INTEGER NOT NULL,
                    PRIMARY KEY(entity_key, concept)
                );

                CREATE TABLE IF NOT EXISTS current_fact_occurrences (
                    occurrence_id TEXT PRIMARY KEY,
                    entity_key TEXT NOT NULL,
                    entity_label TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    knowledge_status TEXT NOT NULL,
                    value_json TEXT,
                    unknown_reason TEXT,
                    source_refs_json TEXT NOT NULL,
                    latest_sequence INTEGER NOT NULL,
                    fact_ids_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    operation TEXT NOT NULL,
                    projection_run_id INTEGER NOT NULL
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
                CREATE INDEX IF NOT EXISTS product_event_attachment_hash_idx
                    ON event_attachments(sha256);
                """
            )
            self._ensure_column_locked("memory_facts", "metadata_json", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column_locked("memory_relations", "metadata_json", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column_locked("current_facts", "metadata_json", "TEXT NOT NULL DEFAULT '{}'")
            self.connection.commit()

    def _ensure_column_locked(self, table: str, column: str, definition: str) -> None:
        columns = {
            str(row[1])
            for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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

    def put_blob(self, content: bytes) -> tuple[str, int, Path]:
        """Publish a blob while sharing the store lock with explicit forget."""

        with self._lock:
            return self.blobs.put(content)

    def remove_blob_if_unreferenced(self, sha256: str) -> bool:
        """Remove one orphaned blob, if no live capture references its hash."""

        with self._transaction(immediate=True):
            row = self.connection.execute(
                "SELECT relative_path FROM attachment_blobs WHERE sha256 = ?",
                (sha256,),
            ).fetchone()
            references = self.connection.execute(
                "SELECT COUNT(*) AS count FROM event_attachments WHERE sha256 = ?",
                (sha256,),
            ).fetchone()
            if int(references["count"]) > 0:
                return False
            if row is None:
                # A failed capture can publish the content-addressed file
                # before its attachment_blobs row is created. It is still an
                # orphan when no event link exists.
                path = self.blobs.path_for_hash(sha256).resolve()
            else:
                path = (self.home / row["relative_path"]).resolve()
            try:
                path.relative_to(self.blobs.root.resolve())
            except ValueError as error:
                raise RuntimeError("attachment path escaped blob store") from error
            if row is not None:
                self.connection.execute("DELETE FROM attachment_blobs WHERE sha256 = ?", (sha256,))
            path.unlink(missing_ok=True)
            return path.exists() is False

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
            if self.connection.execute(
                "SELECT 1 FROM deleted_events WHERE event_id = ?", (event_id,)
            ).fetchone() is not None:
                raise ValueError(f"capture was permanently deleted: {event_id}")
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

    def is_deleted(self, event_id: str) -> bool:
        with self._lock:
            return self.connection.execute(
                "SELECT 1 FROM deleted_events WHERE event_id = ?", (event_id,)
            ).fetchone() is not None

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
        eligibility = "(p.next_retry_at IS NULL OR p.next_retry_at <= ?)"
        query_params: list[Any] = [*statuses, now_text]
        if include_failed:
            # Failed rows at the automatic-attempt cap stay failed until an
            # explicit retry.  Without this predicate a terminal failed row
            # with a NULL next_retry_at would be immediately reacquired.
            eligibility += " AND (p.status <> 'failed' OR p.attempt_count < ?)"
            query_params.append(MAX_AUTOMATIC_ATTEMPTS)
        with self._transaction(immediate=True):
            rows = self.connection.execute(
                f"""
                SELECT s.raw_json, p.event_id
                FROM processing_state p JOIN source_events s ON s.event_id = p.event_id
                WHERE p.status IN ({placeholders})
                  AND {eligibility}
                ORDER BY s.sequence LIMIT ?
                """,
                (*query_params, limit),
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
        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata = {
            str(key): value
            for key, value in metadata.items()
            if isinstance(key, (str, int, float, bool))
        }
        for key in (
            "attribution",
            "confidence",
            "claim_type",
            "certainty",
            "negated",
            "semantic_relation",
            "actionable",
            "historical",
            "lifecycle_key",
        ):
            if key in item and key not in metadata:
                metadata[key] = item[key]
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
            "metadata": metadata,
        }
        fingerprint = hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO memory_facts(
                source_event_id, entity_key, entity_label, concept,
                knowledge_status, value_json, unknown_reason, operation,
                supersedes_event_id, source_refs_json, temporal_json, metadata_json,
                extractor_version, fingerprint, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                canonical_json(metadata),
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
        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata = {
            str(key): value
            for key, value in metadata.items()
            if isinstance(key, (str, int, float, bool))
        }
        for key in (
            "attribution",
            "confidence",
            "claim_type",
            "certainty",
            "negated",
            "semantic_relation",
        ):
            if key in item and key not in metadata:
                metadata[key] = item[key]
        fingerprint_input = {
            "source_event_id": event_id,
            "source_entity_key": item.get("source_entity_key"),
            "relation_type": item["relation_type"],
            "target_entity_key": item.get("target_entity_key"),
            "target_event_id": item.get("target_event_id"),
            "knowledge_status": item.get("knowledge_status", "known"),
            "value": item.get("value"),
            "source_refs": source_refs,
            "metadata": metadata,
        }
        fingerprint = hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO memory_relations(
                source_event_id, source_entity_key, relation_type,
                target_entity_key, target_event_id, knowledge_status,
                value_json, source_refs_json, metadata_json, extractor_version,
                fingerprint, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                canonical_json(metadata),
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

    @staticmethod
    def _json_list(value: Any) -> list[Any]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
        return value if isinstance(value, list) else []

    @classmethod
    def _scrub_event_reference(cls, value: Any, event_id: str) -> Any:
        """Remove one event ID from derived reference-shaped JSON values."""

        reference_keys = {
            "event_id",
            "source_event_id",
            "target_event_id",
            "related_event_id",
            "supersedes_event_id",
        }
        if isinstance(value, list):
            return [
                cls._scrub_event_reference(item, event_id)
                for item in value
                if item != event_id
            ]
        if isinstance(value, dict):
            result: dict[Any, Any] = {}
            for key, item in value.items():
                if str(key) in reference_keys and item == event_id:
                    continue
                result[key] = cls._scrub_event_reference(item, event_id)
            return result
        return value

    @classmethod
    def _contains_event_reference(cls, value: Any, event_id: str) -> bool:
        reference_keys = {
            "event_id",
            "source_event_id",
            "target_event_id",
            "related_event_id",
            "supersedes_event_id",
        }
        if isinstance(value, list):
            return any(cls._contains_event_reference(item, event_id) for item in value)
        if isinstance(value, dict):
            return any(
                (str(key) in reference_keys and item == event_id)
                or cls._contains_event_reference(item, event_id)
                for key, item in value.items()
            )
        return False

    @classmethod
    def _fact_fingerprint_from_row(
        cls,
        row: sqlite3.Row,
        *,
        source_refs: list[str],
        supersedes_event_id: str | None,
    ) -> str:
        value = None
        if row["value_json"] is not None:
            try:
                value = json.loads(row["value_json"])
            except (TypeError, ValueError, json.JSONDecodeError):
                value = None
        status = str(row["knowledge_status"])
        fingerprint_input = {
            "source_event_id": row["source_event_id"],
            "entity_key": row["entity_key"],
            "entity_label": row["entity_label"],
            "concept": row["concept"],
            "knowledge_status": status,
            "value": None if status == "unknown" else value,
            "unknown_reason": row["unknown_reason"] if status == "unknown" else None,
            "operation": row["operation"],
            "supersedes_event_id": supersedes_event_id,
            "source_refs": source_refs,
            "temporal": cls._row_json(row, "temporal_json", {}),
            "metadata": cls._json_object(row["metadata_json"]),
        }
        return hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()

    @classmethod
    def _relation_fingerprint_from_row(
        cls,
        row: sqlite3.Row,
        *,
        source_refs: list[str],
    ) -> str:
        value = None
        if row["value_json"] is not None:
            try:
                value = json.loads(row["value_json"])
            except (TypeError, ValueError, json.JSONDecodeError):
                value = None
        fingerprint_input = {
            "source_event_id": row["source_event_id"],
            "source_entity_key": row["source_entity_key"],
            "relation_type": row["relation_type"],
            "target_entity_key": row["target_entity_key"],
            "target_event_id": row["target_event_id"],
            "knowledge_status": row["knowledge_status"],
            "value": value,
            "source_refs": source_refs,
            "metadata": cls._json_object(row["metadata_json"]),
        }
        return hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()

    @staticmethod
    def _attention_fingerprint_from_row(
        row: sqlite3.Row,
        *,
        source_refs: list[str],
        details: dict[str, Any],
    ) -> str:
        fingerprint_input = {
            "source_event_id": row["source_event_id"],
            "kind": row["kind"],
            "title": row["title"],
            "status": row["status"],
            "knowledge_status": row["knowledge_status"],
            "starts_at": row["starts_at"],
            "due_at": row["due_at"],
            "timezone": row["timezone"],
            "source_refs": source_refs,
            "details": details,
        }
        return hashlib.sha256(canonical_json(fingerprint_input).encode("utf-8")).hexdigest()

    def forget(self, event_id: str, *, reason: str = "user undo") -> dict[str, Any]:
        """Permanently forget one capture and rebuild remaining Product V2 state.

        The tombstone contains only the event ID and deletion time. All source,
        processing, semantic, provenance, and attachment-link rows belonging
        exclusively to the capture are removed in the same SQLite transaction.
        A late worker therefore either observes the deleted lease or waits for
        this transaction and then fails its ownership check.
        """

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be a non-empty string")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("retraction reason must not be empty")
        event_id = event_id.strip()
        with self._transaction(immediate=True):
            if self.connection.execute(
                "SELECT 1 FROM deleted_events WHERE event_id = ?", (event_id,)
            ).fetchone() is not None:
                return {
                    "event_id": event_id,
                    "forgotten": True,
                    "deleted": False,
                    "already_deleted": True,
                    "retracted": True,
                    "deletion_status": "already_deleted",
                    "blobs_deleted": 0,
                    "blobs_preserved": 0,
                    "projection_run_id": None,
                }

            if self.connection.execute(
                "SELECT 1 FROM source_events WHERE event_id = ?", (event_id,)
            ).fetchone() is None:
                raise ValueError(f"unknown event: {event_id}")

            attachment_rows = self.connection.execute(
                """
                SELECT a.sha256, b.relative_path
                FROM event_attachments a JOIN attachment_blobs b ON b.sha256 = a.sha256
                WHERE a.event_id = ?
                ORDER BY a.attachment_index
                """,
                (event_id,),
            ).fetchall()
            hashes = list(dict.fromkeys(str(row["sha256"]) for row in attachment_rows))

            fact_rows = self.connection.execute(
                "SELECT * FROM memory_facts ORDER BY fact_id"
            ).fetchall()
            relation_rows = self.connection.execute(
                "SELECT * FROM memory_relations ORDER BY relation_id"
            ).fetchall()
            attention_rows = self.connection.execute(
                "SELECT * FROM attention_candidates ORDER BY candidate_id"
            ).fetchall()

            candidate_fingerprints_to_delete: set[str] = set()
            candidate_fingerprint_updates: list[tuple[str, str]] = []
            for row in attention_rows:
                refs = {
                    item for item in self._json_list(row["source_refs_json"])
                    if isinstance(item, str) and item
                }
                if row["source_event_id"] == event_id:
                    candidate_fingerprints_to_delete.add(str(row["fingerprint"]))
                    continue
                details_value = self._row_json(row, "details_json", {})
                if event_id not in refs and not self._contains_event_reference(details_value, event_id):
                    continue
                new_refs = sorted(refs - {event_id})
                if row["source_event_id"] not in new_refs:
                    new_refs.append(str(row["source_event_id"]))
                    new_refs.sort()
                details = self._scrub_event_reference(
                    details_value, event_id
                )
                if not isinstance(details, dict):
                    details = {}
                new_fingerprint = self._attention_fingerprint_from_row(
                    row,
                    source_refs=new_refs,
                    details=details,
                )
                candidate_fingerprint_updates.append((str(row["fingerprint"]), new_fingerprint))

            if candidate_fingerprints_to_delete:
                placeholders = ",".join("?" for _ in candidate_fingerprints_to_delete)
                self.connection.execute(
                    f"DELETE FROM attention_status_events WHERE candidate_fingerprint IN ({placeholders})",
                    tuple(candidate_fingerprints_to_delete),
                )
            self.connection.execute(
                "DELETE FROM attention_candidates WHERE source_event_id = ?", (event_id,)
            )

            deleted_fact_rows = [row for row in fact_rows if row["source_event_id"] == event_id]
            self.connection.execute(
                "DELETE FROM memory_facts WHERE source_event_id = ?", (event_id,)
            )
            for row in fact_rows:
                if row["source_event_id"] == event_id:
                    continue
                refs = {
                    item for item in self._json_list(row["source_refs_json"])
                    if isinstance(item, str) and item
                }
                supersedes = row["supersedes_event_id"]
                if event_id not in refs and supersedes != event_id:
                    continue
                new_refs = sorted(refs - {event_id})
                source_id = str(row["source_event_id"])
                if source_id not in new_refs:
                    new_refs.append(source_id)
                    new_refs.sort()
                new_supersedes = None if supersedes == event_id else supersedes
                new_fingerprint = self._fact_fingerprint_from_row(
                    row,
                    source_refs=new_refs,
                    supersedes_event_id=new_supersedes,
                )
                try:
                    self.connection.execute(
                        """
                        UPDATE memory_facts
                        SET supersedes_event_id = ?, source_refs_json = ?, fingerprint = ?
                        WHERE fact_id = ?
                        """,
                        (new_supersedes, canonical_json(new_refs), new_fingerprint, row["fact_id"]),
                    )
                except sqlite3.IntegrityError:
                    # Scrubbing can make two derived rows identical. Keep one
                    # authoritative evidence row rather than preserving a
                    # stale duplicate that still carries the deleted ref.
                    self.connection.execute(
                        "DELETE FROM memory_facts WHERE fact_id = ?", (row["fact_id"],)
                    )

            self.connection.execute(
                "DELETE FROM memory_relations WHERE source_event_id = ?", (event_id,)
            )
            for row in relation_rows:
                if row["source_event_id"] == event_id or row["target_event_id"] == event_id:
                    self.connection.execute(
                        "DELETE FROM memory_relations WHERE relation_id = ?", (row["relation_id"],)
                    )
                    continue
                refs = {
                    item for item in self._json_list(row["source_refs_json"])
                    if isinstance(item, str) and item
                }
                if event_id not in refs:
                    continue
                new_refs = sorted(refs - {event_id})
                source_id = str(row["source_event_id"])
                if source_id not in new_refs:
                    new_refs.append(source_id)
                    new_refs.sort()
                new_fingerprint = self._relation_fingerprint_from_row(
                    row,
                    source_refs=new_refs,
                )
                try:
                    self.connection.execute(
                        "UPDATE memory_relations SET source_refs_json = ?, fingerprint = ? WHERE relation_id = ?",
                        (canonical_json(new_refs), new_fingerprint, row["relation_id"]),
                    )
                except sqlite3.IntegrityError:
                    self.connection.execute(
                        "DELETE FROM memory_relations WHERE relation_id = ?", (row["relation_id"],)
                    )

            for old_fingerprint, new_fingerprint in candidate_fingerprint_updates:
                row = self.connection.execute(
                    "SELECT * FROM attention_candidates WHERE fingerprint = ?",
                    (old_fingerprint,),
                ).fetchone()
                if row is None:
                    continue
                refs = sorted(
                    {
                        item for item in self._json_list(row["source_refs_json"])
                        if isinstance(item, str) and item and item != event_id
                    }
                )
                source_id = str(row["source_event_id"])
                if source_id not in refs:
                    refs.append(source_id)
                    refs.sort()
                details = self._scrub_event_reference(
                    self._row_json(row, "details_json", {}), event_id
                )
                if not isinstance(details, dict):
                    details = {}
                actual_fingerprint = self._attention_fingerprint_from_row(
                    row,
                    source_refs=refs,
                    details=details,
                )
                try:
                    self.connection.execute(
                        """
                        UPDATE attention_candidates
                        SET fingerprint = ?, source_refs_json = ?, details_json = ?
                        WHERE candidate_id = ?
                        """,
                        (
                            actual_fingerprint,
                            canonical_json(refs),
                            canonical_json(details),
                            row["candidate_id"],
                        ),
                    )
                    self.connection.execute(
                        "UPDATE attention_status_events SET candidate_fingerprint = ? WHERE candidate_fingerprint = ?",
                        (actual_fingerprint, old_fingerprint),
                    )
                except sqlite3.IntegrityError:
                    self.connection.execute(
                        "DELETE FROM attention_status_events WHERE candidate_fingerprint = ?",
                        (old_fingerprint,),
                    )
                    self.connection.execute(
                        "DELETE FROM attention_candidates WHERE candidate_id = ?",
                        (row["candidate_id"],),
                    )

            self.connection.execute("DELETE FROM retractions WHERE event_id = ?", (event_id,))
            self.connection.execute("DELETE FROM processing_state WHERE event_id = ?", (event_id,))
            self.connection.execute("DELETE FROM event_attachments WHERE event_id = ?", (event_id,))
            self.connection.execute(
                "INSERT OR REPLACE INTO product_delete_authorizations(event_id) VALUES (?)",
                (event_id,),
            )
            self.connection.execute("DELETE FROM source_events WHERE event_id = ?", (event_id,))
            self.connection.execute(
                "DELETE FROM product_delete_authorizations WHERE event_id = ?",
                (event_id,),
            )
            self.connection.execute(
                "INSERT INTO deleted_events(event_id, deleted_at) VALUES (?, ?)",
                (event_id, utc_now()),
            )

            blobs_deleted = 0
            blobs_preserved = 0
            for sha256 in hashes:
                references = self.connection.execute(
                    "SELECT COUNT(*) AS count FROM event_attachments WHERE sha256 = ?",
                    (sha256,),
                ).fetchone()
                if int(references["count"]) > 0:
                    blobs_preserved += 1
                    continue
                blob_row = self.connection.execute(
                    "SELECT relative_path FROM attachment_blobs WHERE sha256 = ?",
                    (sha256,),
                ).fetchone()
                if blob_row is None:
                    continue
                path = (self.home / blob_row["relative_path"]).resolve()
                try:
                    path.relative_to(self.blobs.root.resolve())
                except ValueError as error:
                    raise RuntimeError("attachment path escaped blob store") from error
                self.connection.execute("DELETE FROM attachment_blobs WHERE sha256 = ?", (sha256,))
                path.unlink(missing_ok=True)
                blobs_deleted += 1

            # Projection history contains only rebuild metadata, but it is
            # derived from the deleted evidence. Drop it so the next run is a
            # clean projection of the remaining live state.
            self.connection.execute("DELETE FROM projection_runs")
            projection = self._rebuild_derived_locked()
            return {
                "event_id": event_id,
                "forgotten": True,
                "deleted": True,
                "already_deleted": False,
                # Compatibility field for the existing /api/v2/retract route;
                # the operation itself is permanent deletion, not an audit-only
                # semantic retraction.
                "retracted": True,
                "deletion_status": "deleted",
                "facts_deleted": len(deleted_fact_rows),
                "relations_deleted": sum(
                    1 for row in relation_rows
                    if row["source_event_id"] == event_id or row["target_event_id"] == event_id
                ),
                "attachments_deleted": len(attachment_rows),
                "blobs_deleted": blobs_deleted,
                "blobs_preserved": blobs_preserved,
                "projection_run_id": projection["projection_run_id"],
            }

    def retract(self, event_id: str, *, reason: str = "user undo") -> dict[str, Any]:
        """Compatibility name for the permanent Product V2 Undo operation."""

        return self.forget(event_id, reason=reason)

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

    @staticmethod
    def _attention_lifecycle_key(row: sqlite3.Row) -> str:
        """Return an explicit or conservative key for one attention timeline.

        Providers may give related candidates a stable ``lifecycle_key`` in
        their details.  The title fallback keeps simple providers useful while
        still normalizing only punctuation and terminal lifecycle prefixes;
        unrelated titles remain separate timelines.
        """

        try:
            details = json.loads(row["details_json"])
        except (TypeError, ValueError, json.JSONDecodeError):
            details = {}
        if isinstance(details, dict):
            explicit = details.get("lifecycle_key")
            if isinstance(explicit, str) and explicit.strip():
                return "key:" + _legacy_key(explicit)
        title = str(row["title"] or "").casefold().strip()
        title = re.sub(r"^(?:completed|complete|done|finished|cancelled|canceled)\s*[:\-–—]\s*", "", title)
        title = re.sub(r"[^\w]+", " ", title, flags=re.UNICODE).strip()
        return "title:" + re.sub(r"\s+", " ", title)

    @classmethod
    def _attention_projection_keys(cls, row: sqlite3.Row) -> tuple[tuple[str, ...], ...]:
        """Return conservative equivalence keys for one Attention candidate.

        A provider may emit both a first-class Attention item and an
        actionable fact for the same capture.  Their titles or kind labels can
        differ, so the projection uses explicit lifecycle identity first and
        then only strong same-occurrence signals: entity plus time, title plus
        time, or same-capture title.  Distinct timed occurrences are never
        merged merely because their action kind is the same.
        """

        details = cls._json_object(row["details_json"])
        source_event_id = str(row["source_event_id"] or "")
        title = str(row["title"] or "").casefold().strip()
        title = re.sub(r"^(?:completed|complete|done|finished|cancelled|canceled)\s*[:\-–—]\s*", "", title)
        title = re.sub(r"[^\w]+", " ", title, flags=re.UNICODE).strip()
        title = re.sub(r"\s+", " ", title)
        entity_key = details.get("entity_key")
        entity = _legacy_key(entity_key) if isinstance(entity_key, str) and entity_key.strip() else ""
        point = _attention_timestamp_key(row["due_at"] or row["starts_at"])
        explicit = details.get("lifecycle_key")
        keys: list[tuple[str, ...]] = []
        if isinstance(explicit, str) and explicit.strip():
            keys.append(("lifecycle", _legacy_key(explicit)))
        if entity and point:
            keys.append(("entity-point", entity, point))
        if title and point:
            keys.append(("title-point", title, point))
        if source_event_id and title:
            keys.append(("capture-title", source_event_id, title))
        if source_event_id and entity:
            keys.append(("capture-entity", source_event_id, entity))
        if not point and title:
            keys.append(("title", title))
        return tuple(keys)

    @classmethod
    def _attention_source_refs(cls, row: sqlite3.Row) -> set[str]:
        try:
            raw_refs = json.loads(row["source_refs_json"])
        except (TypeError, ValueError, json.JSONDecodeError):
            raw_refs = []
        refs = {ref for ref in raw_refs if isinstance(ref, str) and ref} if isinstance(raw_refs, list) else set()
        event_id = str(row["source_event_id"] or "")
        if event_id:
            refs.add(event_id)
        return refs

    @staticmethod
    def _json_object(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (TypeError, ValueError, json.JSONDecodeError):
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    @classmethod
    def _fact_metadata(cls, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        try:
            value = row["metadata_json"]
        except (KeyError, IndexError, TypeError):
            value = {}
        return cls._json_object(value)

    @classmethod
    def _fact_temporal(cls, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        try:
            value = row["temporal_json"]
        except (KeyError, IndexError, TypeError):
            value = {}
        return cls._json_object(value)

    @classmethod
    def _fact_status(cls, row: sqlite3.Row | dict[str, Any]) -> str:
        try:
            status = row["knowledge_status"]
        except (KeyError, IndexError, TypeError):
            status = "unknown"
        return status if status in {"known", "inferred", "unknown"} else "unknown"

    @classmethod
    def _fact_sequence(cls, row: sqlite3.Row | dict[str, Any]) -> int:
        try:
            return int(row["sequence"])
        except (KeyError, IndexError, TypeError, ValueError):
            return 0

    @classmethod
    def _fact_id(cls, row: sqlite3.Row | dict[str, Any]) -> int:
        try:
            return int(row["fact_id"])
        except (KeyError, IndexError, TypeError, ValueError):
            return 0

    @classmethod
    def _fact_event_id(cls, row: sqlite3.Row | dict[str, Any]) -> str:
        try:
            return str(row["source_event_id"])
        except (KeyError, IndexError, TypeError):
            return ""

    @classmethod
    def _fact_value(cls, row: sqlite3.Row | dict[str, Any]) -> Any:
        try:
            value = row["value_json"]
        except (KeyError, IndexError, TypeError):
            value = None
        if value is None:
            return None
        try:
            return json.loads(value) if isinstance(value, str) else value
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    @classmethod
    def _fact_refs(cls, row: sqlite3.Row | dict[str, Any]) -> set[str]:
        try:
            value = row["source_refs_json"]
        except (KeyError, IndexError, TypeError):
            value = []
        try:
            refs = json.loads(value) if isinstance(value, str) else value
        except (TypeError, ValueError, json.JSONDecodeError):
            refs = []
        result = {ref for ref in refs if isinstance(ref, str) and ref} if isinstance(refs, list) else set()
        event_id = cls._fact_event_id(row)
        if event_id:
            result.add(event_id)
        return result

    @classmethod
    def _fact_signature(cls, row: sqlite3.Row | dict[str, Any]) -> str | None:
        if cls._fact_status(row) == "unknown":
            return None
        metadata = cls._fact_metadata(row)
        return canonical_json({"value": cls._fact_value(row), "negated": bool(metadata.get("negated", False))})

    @classmethod
    def _fact_relation(cls, row: sqlite3.Row | dict[str, Any]) -> str:
        metadata = cls._fact_metadata(row)
        semantic_relation = metadata.get("semantic_relation")
        if isinstance(semantic_relation, str) and semantic_relation.strip():
            return _legacy_key(semantic_relation)
        try:
            operation = row["operation"]
        except (KeyError, IndexError, TypeError):
            operation = "set"
        return _legacy_key(operation)

    @classmethod
    def _fact_is_occurrence(cls, row: sqlite3.Row | dict[str, Any]) -> bool:
        """Recognize an explicit occurrence primitive without an ontology.

        The semantic provider owns deciding whether a claim describes an
        occurrence or a durable state.  The projector only honors explicit
        metadata and keeps occurrence rows side by side instead of treating
        different values as a state conflict.
        """

        metadata = cls._fact_metadata(row)
        if metadata.get("occurrence") is True:
            return True
        claim_type = metadata.get("claim_type")
        claim_markers = {
            "occurrence",
            "event",
            "episode",
            "action",
            "transaction",
            "visit",
            "consumption",
            "purchase",
            "payment",
        }
        if isinstance(claim_type, str) and _legacy_key(claim_type) in claim_markers:
            return True
        semantic_relation = metadata.get("semantic_relation")
        relation_markers = {
            "occurrence",
            "event",
            "episode",
            "transaction",
            "visit",
            "consumption",
            "purchase",
            "payment",
        }
        return isinstance(semantic_relation, str) and _legacy_key(semantic_relation) in relation_markers

    @classmethod
    def _fact_temporal_bounds(
        cls,
        row: sqlite3.Row | dict[str, Any],
    ) -> tuple[datetime | None, datetime | None]:
        temporal = cls._fact_temporal(row)
        # ``normalized`` and coarse interval fields describe the time being
        # asserted (for example, an appointment next Thursday).  They are
        # not validity bounds for the fact itself: a current assertion about
        # a future meeting must remain current.  Only explicit validity or
        # effectiveness fields participate in version selection.
        start_value = next(
            (
                temporal.get(key)
                for key in ("valid_from", "effective_at")
                if temporal.get(key) is not None
            ),
            None,
        )
        end_value = temporal.get("valid_to")

        def parse(value: Any) -> datetime | None:
            if not isinstance(value, str):
                return None
            try:
                return _parse_iso(value)
            except (TypeError, ValueError):
                return None

        return parse(start_value), parse(end_value)

    @classmethod
    def _fact_temporally_active(
        cls,
        row: sqlite3.Row | dict[str, Any],
        now: datetime | None,
    ) -> bool:
        if now is None:
            return True
        start, end = cls._fact_temporal_bounds(row)
        current = now.astimezone(timezone.utc)
        return not (start is not None and start > current) and not (end is not None and end <= current)

    @classmethod
    def _fact_sort_key(cls, row: sqlite3.Row | dict[str, Any]) -> tuple[datetime, int, int]:
        start, _end = cls._fact_temporal_bounds(row)
        if start is None:
            try:
                start = _parse_iso(str(row["captured_at"]))
            except (KeyError, TypeError, ValueError):
                start = datetime.min.replace(tzinfo=timezone.utc)
        return start, cls._fact_sequence(row), cls._fact_id(row)

    @classmethod
    def _fact_view(cls, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        metadata = cls._fact_metadata(row)
        result: dict[str, Any] = {
            "fact_id": cls._fact_id(row),
            "source_event_id": cls._fact_event_id(row),
            "knowledge_status": cls._fact_status(row),
            "value": cls._fact_value(row),
            "source_refs": sorted(cls._fact_refs(row)),
        }
        if metadata.get("negated"):
            result["negated"] = True
        if metadata.get("attribution") is not None:
            result["attribution"] = metadata["attribution"]
        if metadata.get("claim_type") is not None:
            result["claim_type"] = metadata["claim_type"]
        if metadata.get("semantic_relation") is not None:
            result["semantic_relation"] = metadata["semantic_relation"]
        if cls._fact_status(row) == "unknown":
            result["unknown_reason"] = row["unknown_reason"] or "not_stated"
        return result

    def _fact_projections(
        self,
        fact_rows: list[sqlite3.Row],
        relation_rows: list[sqlite3.Row],
        retracted: set[str],
        *,
        now: datetime | None,
    ) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
        """Project current truth from evidence without a last-write-wins rule."""

        groups: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for row in fact_rows:
            if self._fact_event_id(row) in retracted:
                continue
            groups.setdefault((str(row["entity_key"]), str(row["concept"])), []).append(row)

        annotations: dict[int, dict[str, Any]] = {
            self._fact_id(row): {
                "active": False,
                "current": False,
                "superseded": False,
                "resolved": False,
                "superseded_by_event_ids": [],
            }
            for row in fact_rows
        }
        relation_replacements: dict[str, list[sqlite3.Row]] = {}
        relation_types = {
            "correction",
            "moved",
            "postponed",
            "rebook",
            "reschedule",
            "supersede",
            "supersession",
            "meaningful_change",
            "resolves_uncertainty",
            "resolution",
        }
        for relation in relation_rows:
            if self._fact_event_id(relation) in retracted:
                continue
            relation_type = _legacy_key(str(relation["relation_type"]))
            target = relation["target_event_id"]
            if isinstance(target, str) and target and relation_type in relation_types:
                relation_replacements.setdefault(self._fact_event_id(relation), []).append(relation)

        projections: list[dict[str, Any]] = []
        for group_key, group_rows in groups.items():
            rows = sorted(group_rows, key=lambda row: (self._fact_sequence(row), self._fact_id(row)))
            superseded_by: dict[str, list[sqlite3.Row]] = {}

            def add_supersession(target_event_id: Any, replacement: sqlite3.Row) -> None:
                if not isinstance(target_event_id, str) or not target_event_id:
                    return
                if target_event_id == self._fact_event_id(replacement):
                    return
                superseded_by.setdefault(target_event_id, []).append(replacement)

            for row in rows:
                operation = str(row["operation"] or "set")
                relation = self._fact_relation(row)
                # An explicitly contradictory report is evidence for the
                # disagreement, never permission to erase its target.
                if operation != "contradiction" and relation not in {"contradiction", "duplicate"}:
                    add_supersession(row["supersedes_event_id"], row)
                if operation in {"correction", "supersede"} or relation in {
                    "correction",
                    "moved",
                    "postponed",
                    "rebook",
                    "reschedule",
                    "supersede",
                    "supersession",
                    "meaningful_change",
                }:
                    if row["supersedes_event_id"] is None:
                        for prior in rows:
                            if self._fact_sequence(prior) >= self._fact_sequence(row):
                                continue
                            if str(prior["operation"] or "set") == "duplicate":
                                continue
                            if operation == "contradiction" or relation == "contradiction":
                                continue
                            add_supersession(self._fact_event_id(prior), row)
                for relation_row in relation_replacements.get(self._fact_event_id(row), []):
                    # This source row is the replacement named by a relation
                    # whose target is another capture. The relation itself is
                    # retained separately, while the target is only removed
                    # from the current view when the replacement is effective.
                    add_supersession(relation_row["target_event_id"], row)

            for target_event_id, replacements in superseded_by.items():
                for target in rows:
                    if self._fact_event_id(target) != target_event_id:
                        continue
                    effective_replacements = [
                        replacement
                        for replacement in replacements
                        if self._fact_temporally_active(replacement, now)
                    ]
                    if not effective_replacements:
                        continue
                    annotation = annotations[self._fact_id(target)]
                    annotation["superseded_by_event_ids"] = sorted(
                        {self._fact_event_id(replacement) for replacement in effective_replacements}
                    )
                    annotation["superseded"] = True

            temporally_available = [row for row in rows if self._fact_temporally_active(row, now)]
            if now is None:
                version_rows = temporally_available
            else:
                timed_rows = [
                    (row, self._fact_temporal_bounds(row)[0])
                    for row in temporally_available
                    if self._fact_temporal_bounds(row)[0] is not None
                ]
                eligible_starts = [start for _row, start in timed_rows if start is not None and start <= now]
                if eligible_starts:
                    latest_start = max(eligible_starts)
                    version_rows = [row for row, start in timed_rows if start == latest_start]
                    replacement_event_ids = {
                        self._fact_event_id(replacement)
                        for replacements in superseded_by.values()
                        for replacement in replacements
                    }
                    version_rows.extend(
                        row
                        for row in temporally_available
                        if self._fact_temporal_bounds(row)[0] is None
                        and self._fact_event_id(row) in replacement_event_ids
                    )
                elif timed_rows:
                    version_rows = [row for row in temporally_available if not self._fact_temporal_bounds(row)[0]]
                else:
                    version_rows = temporally_available

            def replacement_is_active(target_event_id: str) -> bool:
                return any(
                    self._fact_temporally_active(replacement, now)
                    for replacement in superseded_by.get(target_event_id, [])
                )

            active_rows = [
                row
                for row in version_rows
                if not replacement_is_active(self._fact_event_id(row))
            ]

            # A later direct observation may resolve an earlier speculative or
            # missing value. An unresolved contradiction is different: it is
            # deliberately retained and still projects to conflict.
            for row in active_rows:
                if self._fact_status(row) not in {"unknown", "inferred"}:
                    continue
                relation = self._fact_relation(row)
                if relation == "contradiction" or str(row["operation"] or "set") == "contradiction":
                    continue
                if any(
                    self._fact_status(candidate) == "known"
                    and self._fact_sequence(candidate) > self._fact_sequence(row)
                    and self._fact_relation(candidate) not in {"contradiction"}
                    for candidate in active_rows
                ):
                    annotations[self._fact_id(row)]["resolved"] = True
            active_rows = [
                row
                for row in active_rows
                if not annotations[self._fact_id(row)]["resolved"]
            ]

            if not active_rows:
                continue
            for row in active_rows:
                annotations[self._fact_id(row)]["active"] = True

            occurrence_rows = [
                row
                for row in active_rows
                if self._fact_is_occurrence(row)
                and str(row["operation"] or "set") not in {"correction", "supersede", "contradiction"}
                and self._fact_relation(row) not in {"correction", "supersede", "contradiction", "reschedule", "resolution"}
            ]
            if occurrence_rows:
                for row in occurrence_rows:
                    annotations[self._fact_id(row)]["current"] = True
                    metadata = dict(self._fact_metadata(row))
                    metadata["semantic_state"] = "occurrence"
                    metadata["occurrence"] = True
                    projected_occurrence: dict[str, Any] = {
                        "entity_key": group_key[0],
                        "entity_label": str(row["entity_label"] or group_key[0]),
                        "concept": group_key[1],
                        "knowledge_status": self._fact_status(row),
                        "unknown_reason": row["unknown_reason"] if self._fact_status(row) == "unknown" else None,
                        "source_refs": sorted(self._fact_refs(row)),
                        "latest_sequence": self._fact_sequence(row),
                        "fact_ids": [self._fact_id(row)],
                        "operation": str(row["operation"] or "set"),
                        "temporal": self._fact_temporal(row),
                        "metadata": metadata,
                        "source_event_id": self._fact_event_id(row),
                        "captured_at": row["captured_at"] if "captured_at" in row.keys() else None,
                    }
                    value = self._fact_value(row)
                    if value is not None and self._fact_status(row) != "unknown":
                        projected_occurrence["value"] = value
                    projections.append(projected_occurrence)
            state_active_rows = [row for row in active_rows if row not in occurrence_rows]
            if not state_active_rows:
                continue

            value_rows = [row for row in state_active_rows if self._fact_signature(row) is not None]
            known_rows = [row for row in value_rows if self._fact_status(row) == "known"]
            inferred_rows = [row for row in value_rows if self._fact_status(row) == "inferred"]
            known_signatures = {self._fact_signature(row) for row in known_rows}
            inferred_signatures = {self._fact_signature(row) for row in inferred_rows}
            is_conflict = len(known_signatures) > 1 or (not known_signatures and len(inferred_signatures) > 1)
            if is_conflict:
                state = "conflict"
                chosen_row = max(value_rows, key=self._fact_sort_key)
                output_status = "unknown"
                output_value = None
                output_reason = "conflicting"
                supporting_rows = value_rows
            elif known_signatures:
                chosen_signature = next(iter(known_signatures))
                supporting_rows = [row for row in value_rows if self._fact_signature(row) == chosen_signature]
                chosen_row = max(
                    [row for row in supporting_rows if self._fact_status(row) == "known"],
                    key=self._fact_sort_key,
                )
                output_status = "known"
                output_value = self._fact_value(chosen_row)
                output_reason = None
                state = "current"
            elif inferred_signatures:
                chosen_signature = next(iter(inferred_signatures))
                supporting_rows = [row for row in value_rows if self._fact_signature(row) == chosen_signature]
                chosen_row = max(supporting_rows, key=self._fact_sort_key)
                output_status = "inferred"
                output_value = self._fact_value(chosen_row)
                output_reason = None
                state = "uncertain"
            else:
                chosen_row = max(state_active_rows, key=self._fact_sort_key)
                supporting_rows = [chosen_row]
                output_status = "unknown"
                output_value = None
                output_reason = next(
                    (str(row["unknown_reason"]) for row in reversed(state_active_rows) if row["unknown_reason"]),
                    "not_stated",
                )
                state = "unknown"

            for row in supporting_rows:
                annotations[self._fact_id(row)]["current"] = True
            metadata = dict(self._fact_metadata(chosen_row))
            metadata["semantic_state"] = state
            if is_conflict:
                metadata["conflicting_values"] = [self._fact_view(row) for row in value_rows]
                metadata["conflicting_fact_ids"] = [self._fact_id(row) for row in value_rows]
                metadata["conflict_source_refs"] = sorted(
                    {ref for row in value_rows for ref in self._fact_refs(row)}
                )
            uncertainty_rows = [
                row
                for row in state_active_rows
                if row not in supporting_rows
                and (
                    self._fact_status(row) in {"unknown", "inferred"}
                    or self._fact_signature(row) != self._fact_signature(chosen_row)
                )
            ]
            if output_status == "known" and uncertainty_rows:
                metadata["uncertainty"] = [self._fact_view(row) for row in uncertainty_rows]
                metadata["uncertainty_source_refs"] = sorted(
                    {ref for row in uncertainty_rows for ref in self._fact_refs(row)}
                )
            temporal = self._fact_temporal(chosen_row)
            return_value = {
                "entity_key": group_key[0],
                "entity_label": str(chosen_row["entity_label"] or group_key[0]),
                "concept": group_key[1],
                "knowledge_status": output_status,
                "unknown_reason": output_reason,
                "source_refs": sorted(
                    {ref for row in supporting_rows for ref in self._fact_refs(row)}
                    if not is_conflict
                    else {ref for row in value_rows for ref in self._fact_refs(row)}
                ),
                "latest_sequence": max(self._fact_sequence(row) for row in state_active_rows),
                "fact_ids": [self._fact_id(row) for row in state_active_rows],
                "operation": "contradiction" if is_conflict else str(chosen_row["operation"] or "set"),
                "temporal": temporal,
                "metadata": metadata,
                "source_event_id": self._fact_event_id(chosen_row),
                "captured_at": chosen_row["captured_at"] if "captured_at" in chosen_row.keys() else None,
            }
            if output_value is not None:
                return_value["value"] = output_value
            if metadata.get("negated"):
                return_value["negated"] = True
            if metadata.get("attribution") is not None:
                return_value["attribution"] = metadata["attribution"]
            if metadata.get("claim_type") is not None:
                return_value["claim_type"] = metadata["claim_type"]
            if metadata.get("confidence") is not None:
                return_value["confidence"] = metadata["confidence"]
            projections.append(return_value)
        projections.sort(key=lambda item: (str(item["entity_key"]), str(item["concept"])))
        return projections, annotations

    def _rebuild_derived_locked(self) -> dict[str, Any]:
        retracted = self._retracted_event_ids_locked()
        fact_rows = self.connection.execute(
            """
            SELECT f.*, s.sequence, s.captured_at, s.timezone
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
        self.connection.execute("DELETE FROM current_fact_occurrences")
        self.connection.execute("DELETE FROM current_attention")

        projection_reference = None
        if fact_rows:
            try:
                projection_reference = max(_parse_iso(str(row["captured_at"])) for row in fact_rows)
            except (KeyError, TypeError, ValueError):
                projection_reference = None
        fact_projections, _annotations = self._fact_projections(
            fact_rows,
            relation_rows,
            retracted,
            now=projection_reference,
        )
        for projected in fact_projections:
            is_occurrence = projected.get("metadata", {}).get("semantic_state") == "occurrence"
            target_table = "current_fact_occurrences" if is_occurrence else "current_facts"
            occurrence_id = None
            if is_occurrence:
                occurrence_id = hashlib.sha256(
                    canonical_json(
                        {
                            "entity_key": projected["entity_key"],
                            "concept": projected["concept"],
                            "source_event_id": projected.get("source_event_id"),
                            "fact_ids": projected["fact_ids"],
                        }
                    ).encode("utf-8")
                ).hexdigest()
            self.connection.execute(
                f"""
                INSERT INTO {target_table}(
                    {"occurrence_id, " if is_occurrence else ""}entity_key, entity_label, concept, knowledge_status,
                    value_json, unknown_reason, source_refs_json,
                    latest_sequence, fact_ids_json, metadata_json, operation,
                    projection_run_id
                ) VALUES ({"?, " if is_occurrence else ""}?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *((occurrence_id,) if is_occurrence else ()),
                    projected["entity_key"],
                    projected["entity_label"],
                    projected["concept"],
                    projected["knowledge_status"],
                    canonical_json(projected["value"]) if projected.get("value") is not None else None,
                    projected["unknown_reason"],
                    canonical_json(projected["source_refs"]),
                    projected["latest_sequence"],
                    canonical_json(projected["fact_ids"]),
                    canonical_json(projected.get("metadata", {})),
                    projected["operation"],
                    projection_run_id,
                ),
            )

        latest_attention_status: dict[str, tuple[int, str]] = {}
        for row in status_rows:
            latest_attention_status[row["candidate_fingerprint"]] = (
                int(row["status_event_id"]),
                row["status"],
            )
        source_sequences = {
            row["event_id"]: int(row["sequence"])
            for row in self.connection.execute("SELECT event_id, sequence FROM source_events").fetchall()
        }
        active_attention_rows = [
            row for row in attention_rows if row["source_event_id"] not in retracted
        ]
        parent = list(range(len(active_attention_rows)))

        def find(index: int) -> int:
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        def union(left: int, right: int) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parent[right_root] = left_root

        key_owner: dict[tuple[str, ...], int] = {}
        event_rows: dict[str, list[int]] = {}
        for index, row in enumerate(active_attention_rows):
            event_rows.setdefault(str(row["source_event_id"]), []).append(index)
            for key in self._attention_projection_keys(row):
                owner = key_owner.get(key)
                if owner is None:
                    key_owner[key] = index
                else:
                    union(owner, index)

        # Related/superseded event links are semantic identity, even when the
        # linked candidates use different titles or timestamps.
        for index, row in enumerate(active_attention_rows):
            details = self._json_object(row["details_json"])
            linked_event = details.get("supersedes_event_id", details.get("related_event_id"))
            if not isinstance(linked_event, str):
                continue
            for target_index in event_rows.get(linked_event, []):
                union(index, target_index)

        grouped_attention: dict[int, list[sqlite3.Row]] = {}
        for index, row in enumerate(active_attention_rows):
            grouped_attention.setdefault(find(index), []).append(row)

        def candidate_score(candidate: sqlite3.Row) -> tuple[int, int, int, int]:
            return (
                source_sequences.get(candidate["source_event_id"], 0),
                int(bool(candidate["due_at"] or candidate["starts_at"])),
                len(str(candidate["title"] or "")),
                int(candidate["candidate_id"]),
            )

        for group_rows in grouped_attention.values():
            row = max(group_rows, key=candidate_score)
            status_event = max(
                (
                    latest_attention_status[candidate["fingerprint"]]
                    for candidate in group_rows
                    if candidate["fingerprint"] in latest_attention_status
                ),
                default=None,
            )
            status = status_event[1] if status_event is not None else row["status"]
            lifecycle_action_value = self._json_object(row["details_json"]).get("lifecycle_action")
            lifecycle_action = lifecycle_action_value.casefold().strip() if isinstance(lifecycle_action_value, str) else ""
            if lifecycle_action in {"supersede", "superseded", "replaced", "obsolete"}:
                # Supersession removes the old item from the current
                # lifecycle projection. Completed and cancelled rows remain
                # available as explicit lifecycle history; the UI and badge
                # filter them from active Attention.
                continue
            merged_refs = sorted(
                {
                    reference
                    for candidate in group_rows
                    for reference in self._attention_source_refs(candidate)
                }
            )
            merged_details: dict[str, Any] = {}
            for candidate in sorted(group_rows, key=candidate_score):
                details = self._json_object(candidate["details_json"])
                for key, value in details.items():
                    if key not in merged_details and value is not None:
                        merged_details[key] = value
            starts_at = next(
                (candidate["starts_at"] for candidate in sorted(group_rows, key=candidate_score, reverse=True)
                 if candidate["starts_at"]),
                None,
            )
            due_at = next(
                (candidate["due_at"] for candidate in sorted(group_rows, key=candidate_score, reverse=True)
                 if candidate["due_at"]),
                None,
            )
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
                    starts_at,
                    due_at,
                    row["timezone"],
                    canonical_json(merged_refs),
                    canonical_json(merged_details),
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
        try:
            metadata_raw = row["metadata_json"]
        except (KeyError, IndexError, TypeError):
            metadata_raw = "{}"
        try:
            metadata = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw
        except (TypeError, ValueError, json.JSONDecodeError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        result: dict[str, Any] = {
            "entity_key": row["entity_key"],
            "entity_label": row["entity_label"],
            "concept": row["concept"],
            "knowledge_status": row["knowledge_status"],
            "source_refs": json.loads(row["source_refs_json"]),
        }
        if "captured_at" in row.keys():
            result["captured_at"] = row["captured_at"]
        if "timezone" in row.keys():
            result["timezone"] = row["timezone"]
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
        if metadata.get("negated"):
            result["negated"] = True
        for key in ("attribution", "claim_type", "certainty", "confidence", "semantic_relation"):
            if metadata.get(key) is not None:
                result[key] = metadata[key]
        if metadata:
            result["semantic_metadata"] = metadata
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
            history_rows = self.connection.execute(
                """
                SELECT f.*, s.sequence, s.captured_at, s.timezone
                FROM memory_facts f JOIN source_events s ON s.event_id = f.source_event_id
                ORDER BY s.sequence, f.fact_id
                """
            ).fetchall()
            relation_rows = self.connection.execute(
                """
                SELECT r.*, s.sequence
                FROM memory_relations r JOIN source_events s ON s.event_id = r.source_event_id
                ORDER BY s.sequence, r.relation_id
                """
            ).fetchall()
            current_projections, annotations = self._fact_projections(
                history_rows,
                relation_rows,
                retracted,
                now=current_time,
            )
            history: list[dict[str, Any]] = []
            for row in history_rows:
                result = self._fact_dict(
                    {**dict(row), "retracted_event_ids": retracted}  # type: ignore[arg-type]
                )
                annotation = annotations.get(int(row["fact_id"]), {})
                result.update(
                    {
                        "active": bool(annotation.get("active", False)),
                        "current": bool(annotation.get("current", False)),
                        "superseded": bool(annotation.get("superseded", False)),
                        "resolved": bool(annotation.get("resolved", False)),
                    }
                )
                if annotation.get("superseded_by_event_ids"):
                    result["superseded_by_event_ids"] = annotation["superseded_by_event_ids"]
                history.append(result)
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
                metadata = self._json_object(row["metadata_json"] if "metadata_json" in row.keys() else {})
                if metadata:
                    item["semantic_metadata"] = metadata
                    for key in ("attribution", "claim_type", "certainty", "confidence", "semantic_relation"):
                        if metadata.get(key) is not None:
                            item[key] = metadata[key]
                    if metadata.get("negated"):
                        item["negated"] = True
                if row["value_json"] is not None:
                    item["value"] = json.loads(row["value_json"])
                relations.append(item)
            attention_rows = self.connection.execute(
                """
                SELECT a.*, s.captured_at AS captured_at, s.observed_at AS observed_at,
                       s.source_type AS source_type
                FROM current_attention a
                LEFT JOIN source_events s ON s.event_id = a.source_event_id
                ORDER BY a.due_at IS NULL, a.due_at, a.starts_at IS NULL, a.starts_at, a.fingerprint
                """
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
                    "captured_at": row["captured_at"],
                    "observed_at": row["observed_at"],
                    "source_type": row["source_type"],
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
            for row in current_projections:
                entity = entities.setdefault(
                    str(row["entity_key"]),
                    {
                        "entity_key": row["entity_key"],
                        "label": row["entity_label"],
                        "source_refs": [],
                    },
                )
                entity["source_refs"] = sorted(
                    set(entity["source_refs"])
                    | set(row.get("source_refs", []))
                )
            return {
                "store_version": PRODUCT_STORE_VERSION,
                "projection_version": latest_projection["projection_version"] if latest_projection else PRODUCT_PROJECTION_VERSION,
                "projection_run_id": latest_projection["projection_run_id"] if latest_projection else None,
                "counts": {
                    "captures": len(sources),
                    "active_captures": sum(not item["retracted"] for item in sources),
                    "facts": len(current_projections),
                    "fact_history": len(history),
                    "entities": len(entities),
                    "relationships": len(relations),
                    "attention": sum(item["status"] == "open" for item in attention),
                    "attention_lifecycle": len(attention),
                    "attachments": len(attachments),
                },
                "entities": list(entities.values()),
                "facts": current_projections,
                "current_facts": current_projections,
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
    "AUTOMATIC_RETRY_BACKOFF_SECONDS",
    "BlobStore",
    "MAX_AUTOMATIC_ATTEMPTS",
    "PRODUCT_EXTRACTOR_VERSION",
    "PRODUCT_PROCESSING_VERSION",
    "PRODUCT_PROJECTION_VERSION",
    "PRODUCT_STORE_VERSION",
    "ProductStore",
    "canonical_json",
    "utc_now",
]
