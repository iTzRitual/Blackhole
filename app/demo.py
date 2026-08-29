"""Small deterministic Blackhole demo runtime.

The demo uses the same append-only SQLite state boundary and deterministic
response projector as the experiment slice, but it has its own small synthetic
seed. Captures are saved immediately; this demo does not silently invoke a
provider or read authentication material.
"""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.query_service import (
    DEFAULT_QUERY_BUNDLE,
    answer_question_from_snapshot,
    build_state_view,
    projections,
)
from app.state_store import StateStore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_PATH = ROOT / "data" / "synthetic" / "demo-seed.json"
DEFAULT_DB_PATH = ROOT / "data" / "demo" / "state.sqlite"

DEMO_QUERY_BUNDLE = DEFAULT_QUERY_BUNDLE


def load_demo_seed(seed_path: Path = DEFAULT_SEED_PATH) -> dict[str, Any]:
    return json.loads(seed_path.read_text(encoding="utf-8"))


def demo_contract(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or load_demo_seed()
    return {
        "response_contract": "blackhole-demo-v1",
        "public_ontology": {"subjects": seed.get("subjects", [])},
    }


def seed_database(db_path: Path = DEFAULT_DB_PATH, *, seed_path: Path = DEFAULT_SEED_PATH) -> dict[str, Any]:
    """Reset the demo database from the committed synthetic seed."""

    seed = load_demo_seed(seed_path)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    for suffix in ("-wal", "-shm"):
        journal = Path(f"{db_path}{suffix}")
        if journal.exists():
            journal.unlink()
    with StateStore(db_path) as store:
        event_count = store.insert_raw_events(seed.get("events", []))
        observation_count = store.add_observations(seed.get("observations", []), "blackhole-demo-seed-v1")
        relationship_count = store.add_relationships(seed.get("relationships", []), "blackhole-demo-seed-v1")
        projection = store.rebuild_projection()
    return {
        "db_path": str(db_path),
        "events": event_count,
        "observations": observation_count,
        "relationships": relationship_count,
        "projection": projection,
    }


def ensure_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    if not Path(db_path).exists():
        seed_database(Path(db_path))


def append_capture(
    text: str,
    db_path: Path = DEFAULT_DB_PATH,
    *,
    source_type: str = "text",
    filename: str | None = None,
) -> dict[str, Any]:
    """Persist a raw capture and rebuild state without provider interaction."""

    normalized = text.strip()
    if not normalized:
        raise ValueError("capture text must not be empty")
    db_path = Path(db_path)
    ensure_database(db_path)
    with StateStore(db_path) as store:
        row = store.connection.execute("SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence FROM raw_events").fetchone()
        sequence = int(row["next_sequence"])
        event_id = f"capture-{sequence:04d}"
        captured_at = datetime.now(timezone.utc).isoformat()
        metadata: dict[str, Any] = {"demo": True, "semantic_status": "pending"}
        if filename:
            metadata["filename"] = filename
        event = {
            "event_id": event_id,
            "sequence": sequence,
            "captured_at": captured_at,
            "observed_at": date.today().isoformat(),
            "source_type": source_type.strip() or "text",
            "payload": {"text": normalized},
            "metadata": metadata,
        }
        store.insert_raw_events([event])
        projection = store.rebuild_projection()
    return {"event_id": event_id, "sequence": sequence, "projection": projection}


def provider_status() -> dict[str, Any]:
    """Report CLI availability without inspecting credentials or auth files."""

    executable = shutil.which("codex")
    if executable:
        return {
            "available": True,
            "executable": executable,
            "message": "Codex CLI detected. Login and authentication remain external to Blackhole.",
        }
    return {
        "available": False,
        "executable": None,
        "message": "Codex CLI not detected. Install and log in to Codex externally for semantic interpretation.",
    }


def _raw_capture_view(store: StateStore) -> list[dict[str, Any]]:
    rows = store.connection.execute("SELECT raw_json FROM raw_events ORDER BY sequence DESC LIMIT 12").fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        event = json.loads(row["raw_json"])
        payload = event.get("payload", {})
        result.append(
            {
                "event_id": event.get("event_id"),
                "sequence": event.get("sequence"),
                "captured_at": event.get("captured_at"),
                "observed_at": event.get("observed_at"),
                "source_type": event.get("source_type"),
                "text": payload.get("text") if isinstance(payload, dict) else None,
            }
        )
    return result


def _projections(snapshot: dict[str, Any]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    return projections(snapshot, contract=demo_contract(), query_bundle=DEMO_QUERY_BUNDLE)


def build_view(db_path: Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Build the small user-facing state view from the current SQLite state."""

    db_path = Path(db_path)
    ensure_database(db_path)
    with StateStore(db_path) as store:
        snapshot = store.snapshot()
        view = build_state_view(snapshot, contract=demo_contract(), query_bundle=DEMO_QUERY_BUNDLE)
        view["provider"] = provider_status()
        view["recent_captures"] = _raw_capture_view(store)
        return view


def answer_question(question: str, db_path: Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Answer a small set of demo questions from deterministic state projections."""

    normalized = question.strip().casefold()
    if not normalized:
        raise ValueError("question must not be empty")
    db_path = Path(db_path)
    ensure_database(db_path)
    with StateStore(db_path) as store:
        answer = answer_question_from_snapshot(
            question,
            store.snapshot(),
            contract=demo_contract(),
            query_bundle=DEMO_QUERY_BUNDLE,
        )
    answer["provider"] = provider_status()
    return answer
