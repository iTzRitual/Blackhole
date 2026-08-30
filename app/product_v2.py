"""Open-world Product V2 runtime for Blackhole.

Product V2 deliberately does not reuse the benchmark query bundle or its
closed ontology.  It owns a durable capture queue, a generic semantic
representation, deterministic time normalization, Attention projections, and
bounded retrieval.  The local Codex CLI is an optional interpreter, never the
source of truth or the calculator of record.
"""

from __future__ import annotations

import base64
import copy
import inspect
import json
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
import uuid
from collections.abc import Callable, Iterable
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.codex_discovery import ProviderStatus
from app.product_v2_store import (
    AUTOMATIC_RETRY_BACKOFF_SECONDS,
    MAX_AUTOMATIC_ATTEMPTS,
    PRODUCT_EXTRACTOR_VERSION,
    PRODUCT_PROCESSING_VERSION,
    ProductStore,
    canonical_json,
    utc_now,
)
from app.runtime_config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    DEFAULT_TIMEOUT_SECONDS,
)


PRODUCT_RUNTIME_VERSION = "blackhole-product-v2-runtime-v1"
PRODUCT_DATABASE_NAME = "blackhole-v2.db"
PRODUCT_PROMPT_VERSION = "blackhole-product-v2-prompt-v1"
PROCESSING_PENDING_MESSAGE = "Still understanding your recent captures."
PROCESSING_FAILED_MESSAGE = "Some recent captures couldn't be understood yet. Your captures are still saved."
MAX_CAPTURE_TEXT = 100_000
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 25 * 1024 * 1024
MAX_ASK_CONTEXT_FACTS = 40
MAX_ASK_CONTEXT_HISTORY = 20


class ProductProviderUnavailableError(RuntimeError):
    """Safe provider condition used by the Product V2 queue."""


class ProductProviderExecutionError(RuntimeError):
    """Safe provider execution failure with bounded operational diagnostics."""

    def __init__(self, message: str, *, diagnostic: dict[str, Any]) -> None:
        super().__init__(message)
        self.diagnostic = copy.deepcopy(diagnostic)


class ProductSemanticProvider(Protocol):
    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        """Return generic facts, relations, attention, and attachment results."""


def _clean_text(value: Any, *, limit: int = 500) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w]+", "_", normalized, flags=re.UNICODE).strip("_")
    return normalized[:160] or "unknown_entity"


def _tokens(value: Any) -> set[str]:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True) if value is not None else ""
    stopwords = {"my"}
    return {
        token
        for token in re.findall(r"[\w]+", value.casefold(), flags=re.UNICODE)
        if len(token) > 1 and token not in stopwords
    }


def _safe_json_value(value: Any, *, depth: int = 0) -> Any:
    """Copy provider values while bounding accidental output expansion."""

    if depth > 6:
        return None
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, str):
            return value[:4000]
        return value
    if isinstance(value, list):
        return [_safe_json_value(item, depth=depth + 1) for item in value[:100]]
    if isinstance(value, dict):
        return {
            str(key)[:120]: _safe_json_value(item, depth=depth + 1)
            for key, item in list(value.items())[:100]
            if isinstance(key, (str, int, float, bool))
        }
    return None


def local_timezone_name() -> str:
    current = datetime.now().astimezone().tzinfo
    key = getattr(current, "key", None)
    if isinstance(key, str) and key:
        return key
    name = current.tzname(None) if current is not None else None
    windows_aliases = {
        "W. Europe Standard Time": "Europe/Berlin",
        "W. Europe Summer Time": "Europe/Berlin",
        "Central Europe Standard Time": "Europe/Budapest",
        "Central European Standard Time": "Europe/Warsaw",
        "Romance Standard Time": "Europe/Paris",
        "GMT Standard Time": "Europe/London",
    }
    if name in windows_aliases:
        return windows_aliases[name]
    offset = current.utcoffset() if current is not None else None
    if offset is not None:
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        total_minutes = abs(total_minutes)
        return f"UTC{sign}{total_minutes // 60:02d}:{total_minutes % 60:02d}"
    return "UTC"


def resolve_timezone(value: str | None) -> tuple[str, Any]:
    name = _clean_text(value, limit=120) or local_timezone_name()
    if name.upper() in {"UTC", "GMT", "Z"}:
        return "UTC", timezone.utc
    offset_match = re.fullmatch(r"UTC([+-])(\d{1,2})(?::?(\d{2}))?", name.upper())
    if offset_match:
        minutes = int(offset_match.group(2)) * 60 + int(offset_match.group(3) or 0)
        if offset_match.group(1) == "-":
            minutes = -minutes
        return name.upper(), timezone(timedelta(minutes=minutes))
    aliases = {
        "W. Europe Standard Time": "Europe/Berlin",
        "W. Europe Summer Time": "Europe/Berlin",
        "Central Europe Standard Time": "Europe/Budapest",
        "Central European Standard Time": "Europe/Warsaw",
        "Romance Standard Time": "Europe/Paris",
        "GMT Standard Time": "Europe/London",
    }
    name = aliases.get(name, name)
    try:
        return name, ZoneInfo(name)
    except ZoneInfoNotFoundError as error:
        raise ValueError(f"unknown timezone: {name}") from error


def parse_datetime(value: Any, *, zone: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    elif isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


_MONTHS = {
    "january": 1,
    "jan": 1,
    "stycznia": 1,
    "styczen": 1,
    "styczeń": 1,
    "february": 2,
    "feb": 2,
    "lutego": 2,
    "march": 3,
    "mar": 3,
    "marca": 3,
    "april": 4,
    "apr": 4,
    "kwietnia": 4,
    "may": 5,
    "maja": 5,
    "june": 6,
    "jun": 6,
    "czerwca": 6,
    "july": 7,
    "jul": 7,
    "lipca": 7,
    "august": 8,
    "aug": 8,
    "sierpnia": 8,
    "september": 9,
    "sep": 9,
    "września": 9,
    "wrzesnia": 9,
    "october": 10,
    "oct": 10,
    "października": 10,
    "pazdziernika": 10,
    "november": 11,
    "nov": 11,
    "listopada": 11,
    "december": 12,
    "dec": 12,
    "grudnia": 12,
}


def _relative_delta(value: Any) -> timedelta | None:
    if isinstance(value, dict):
        for key in ("relative_seconds", "seconds"):
            if isinstance(value.get(key), (int, float)) and not isinstance(value.get(key), bool):
                return timedelta(seconds=float(value[key]))
        for key in ("relative_minutes", "minutes"):
            if isinstance(value.get(key), (int, float)) and not isinstance(value.get(key), bool):
                return timedelta(minutes=float(value[key]))
        for key in ("relative_hours", "hours"):
            if isinstance(value.get(key), (int, float)) and not isinstance(value.get(key), bool):
                return timedelta(hours=float(value[key]))
    if not isinstance(value, str):
        return None
    match = re.search(
        r"\b(?:in|za|za około|za ok\.?)\s+(\d+(?:[.,]\d+)?)\s*(seconds?|secs?|sekund\w*|minutes?|mins?|minut\w*|hours?|hrs?|godzin\w*)\b",
        value.casefold(),
    )
    if not match:
        return None
    amount = float(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit.startswith(("second", "sec", "sekund")):
        return timedelta(seconds=amount)
    if unit.startswith(("hour", "hr", "godzin")):
        return timedelta(hours=amount)
    return timedelta(minutes=amount)


def _natural_date(value: str, *, base: datetime) -> datetime | None:
    lowered = value.casefold().strip()
    if lowered in {"today", "dzisiaj", "dziś"}:
        return base.replace(hour=0, minute=0, second=0, microsecond=0)
    if lowered in {"tomorrow", "jutro"}:
        return (base + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    match = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?[ .-]+([\wąćęłńóśźż]+)(?:[ .,-]+(\d{4}))?\b",
        lowered,
        flags=re.UNICODE,
    )
    if match:
        month = _MONTHS.get(match.group(2))
        if month:
            year = int(match.group(3) or base.year)
            try:
                return base.replace(year=year, month=month, day=int(match.group(1)), hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                return None
    match = re.search(
        r"\b([\wąćęłńóśźż]+)[ .-]+(\d{1,2})(?:[ ,.-]+(\d{4}))?\b",
        lowered,
        flags=re.UNICODE,
    )
    if match:
        month = _MONTHS.get(match.group(1))
        if month:
            year = int(match.group(3) or base.year)
            try:
                return base.replace(year=year, month=month, day=int(match.group(2)), hour=0, minute=0, second=0, microsecond=0)
            except ValueError:
                return None
    return None


def normalize_timestamp(
    value: Any,
    *,
    captured_at: datetime,
    zone: Any,
) -> str | None:
    """Normalize explicit and relative model proposals deterministically."""

    delta = _relative_delta(value)
    if delta is not None:
        return (captured_at + delta).astimezone(zone).isoformat()
    parsed = parse_datetime(value, zone=zone)
    if parsed is not None:
        return parsed.isoformat()
    if isinstance(value, str):
        natural = _natural_date(value, base=captured_at)
        if natural is not None:
            return natural.astimezone(zone).isoformat()
    if isinstance(value, dict):
        for key in ("iso", "datetime", "timestamp", "date", "value"):
            if key in value:
                normalized = normalize_timestamp(value[key], captured_at=captured_at, zone=zone)
                if normalized is not None:
                    return normalized
    return None


def time_context_for_event(event: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    timezone_name, zone = resolve_timezone(event.get("timezone"))
    captured = parse_datetime(event.get("captured_at"), zone=zone)
    if captured is None:
        captured = (now or datetime.now(timezone.utc)).astimezone(zone)
    current = (now or datetime.now(timezone.utc)).astimezone(zone)
    return {
        "timezone": timezone_name,
        "captured_at": captured.isoformat(),
        "captured_date": captured.date().isoformat(),
        "current_at": current.isoformat(),
        "current_date": current.date().isoformat(),
        "current_time": current.strftime("%H:%M:%S"),
    }


def _event_id(item: dict[str, Any], batch_ids: set[str]) -> str | None:
    value = item.get("event_id", item.get("source_event_id"))
    return value if isinstance(value, str) and value in batch_ids else None


def _entity(item: dict[str, Any]) -> tuple[str, str] | None:
    raw = item.get("entity_key", item.get("subject", item.get("entity")))
    label = ""
    if isinstance(raw, dict):
        label = _clean_text(raw.get("label") or raw.get("name") or raw.get("key"))
        raw = raw.get("key") or raw.get("name") or raw.get("label")
    if not isinstance(raw, str) or not raw.strip():
        return None
    label = label or _clean_text(raw)
    return _slug(raw), label[:240]


def normalize_fact(
    item: Any,
    *,
    batch_ids: set[str],
    available_ids: set[str],
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    source_event_id = _event_id(item, batch_ids)
    entity = _entity(item)
    concept = item.get("concept", item.get("predicate", item.get("fact_type")))
    if source_event_id is None or entity is None or not isinstance(concept, str) or not concept.strip():
        return None
    concept_key = _slug(concept)
    raw_status = item.get("knowledge_status", item.get("status", "inferred"))
    status = raw_status.casefold().strip() if isinstance(raw_status, str) else "inferred"
    if status not in {"known", "inferred", "unknown"}:
        status = "inferred"
    has_value = "value" in item and item.get("value") is not None and not (
        isinstance(item.get("value"), str) and not item["value"].strip()
    )
    if status != "unknown" and not has_value:
        status = "unknown"
    operation = item.get("operation", "set")
    if not isinstance(operation, str) or operation.casefold() not in {
        "set",
        "correction",
        "supersede",
        "contradiction",
        "duplicate",
    }:
        operation = "set"
    else:
        operation = operation.casefold()
    source_refs_value = item.get("source_refs", [source_event_id])
    source_refs = {
        reference
        for reference in source_refs_value
        if isinstance(reference, str) and reference in available_ids
    } if isinstance(source_refs_value, list) else set()
    source_refs.add(source_event_id)
    supersedes = item.get("supersedes_event_id")
    if not isinstance(supersedes, str) or supersedes not in available_ids:
        supersedes = None
    temporal = item.get("temporal", {})
    if not isinstance(temporal, dict):
        temporal = {}
    for key in ("valid_from", "valid_to", "observed_at"):
        if key in item and key not in temporal:
            temporal[key] = item[key]
    result: dict[str, Any] = {
        "source_event_id": source_event_id,
        "entity_key": entity[0],
        "entity_label": entity[1],
        "concept": concept_key,
        "knowledge_status": status,
        "operation": operation,
        "source_refs": source_refs,
        "temporal": _safe_json_value(temporal) or {},
    }
    if status == "unknown":
        result["unknown_reason"] = _clean_text(item.get("unknown_reason"), limit=300) or "not_stated"
    else:
        result["value"] = _safe_json_value(item.get("value"))
    if supersedes is not None:
        result["supersedes_event_id"] = supersedes
    return result


def normalize_relation(
    item: Any,
    *,
    batch_ids: set[str],
    available_ids: set[str],
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    source_event_id = item.get("source_event_id", item.get("event_id"))
    if not isinstance(source_event_id, str) or source_event_id not in batch_ids:
        return None
    relation_type = item.get("relation_type", item.get("type"))
    if not isinstance(relation_type, str) or not relation_type.strip():
        return None
    target_event_id = item.get("target_event_id")
    if not isinstance(target_event_id, str) or target_event_id not in available_ids:
        target_event_id = None
    source_entity = item.get("source_entity_key", item.get("subject"))
    target_entity = item.get("target_entity_key", item.get("target"))
    if isinstance(source_entity, dict):
        source_entity = source_entity.get("key") or source_entity.get("name")
    if isinstance(target_entity, dict):
        target_entity = target_entity.get("key") or target_entity.get("name")
    status = item.get("knowledge_status", "known")
    if not isinstance(status, str) or status.casefold() not in {"known", "inferred", "unknown"}:
        status = "inferred"
    source_refs_value = item.get("source_refs", [source_event_id])
    refs = {
        ref
        for ref in source_refs_value
        if isinstance(ref, str) and ref in available_ids
    } if isinstance(source_refs_value, list) else set()
    refs.add(source_event_id)
    return {
        "source_event_id": source_event_id,
        "source_entity_key": _slug(source_entity) if isinstance(source_entity, str) and source_entity else None,
        "relation_type": _slug(relation_type),
        "target_entity_key": _slug(target_entity) if isinstance(target_entity, str) and target_entity else None,
        "target_event_id": target_event_id,
        "knowledge_status": status.casefold(),
        "value": _safe_json_value(item.get("value")),
        "source_refs": sorted(refs),
    }


def _attention_status(value: Any) -> str:
    if not isinstance(value, str):
        return "open"
    normalized = value.casefold().strip()
    if normalized in {"completed", "complete", "done", "finished"}:
        return "completed"
    if normalized in {"cancelled", "canceled", "void", "dismissed"}:
        return "cancelled"
    return "open"


def normalize_attention(
    item: Any,
    *,
    event: dict[str, Any],
    available_ids: set[str],
    now: datetime | None,
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    event_id = item.get("event_id", item.get("source_event_id"))
    if not isinstance(event_id, str) or event_id != event.get("event_id"):
        return None
    title = _clean_text(item.get("title") or item.get("text") or item.get("task") or item.get("label"), limit=500)
    value = item.get("value")
    if not title and isinstance(value, str):
        title = _clean_text(value, limit=500)
    if not title and isinstance(value, dict):
        title = _clean_text(value.get("title") or value.get("text") or value.get("task"), limit=500)
    if not title:
        return None
    timezone_name, zone = resolve_timezone(event.get("timezone"))
    captured = parse_datetime(event.get("captured_at"), zone=zone) or (now or datetime.now(timezone.utc)).astimezone(zone)
    raw_due = item.get("due_at", item.get("deadline"))
    raw_starts = item.get("starts_at", item.get("start_at"))
    if raw_due is None and "relative_minutes" in item:
        raw_due = {"relative_minutes": item.get("relative_minutes")}
    if raw_due is None and isinstance(value, dict):
        raw_due = value.get("due_at", value.get("deadline"))
    if raw_starts is None and isinstance(value, dict):
        raw_starts = value.get("starts_at", value.get("start_at"))
    due_at = normalize_timestamp(raw_due, captured_at=captured, zone=zone) if raw_due is not None else None
    starts_at = normalize_timestamp(raw_starts, captured_at=captured, zone=zone) if raw_starts is not None else None
    knowledge_status = item.get("knowledge_status", "known")
    if not isinstance(knowledge_status, str) or knowledge_status.casefold() not in {"known", "inferred", "unknown"}:
        knowledge_status = "inferred"
    detail = _safe_json_value(item.get("details", {}))
    if not isinstance(detail, dict):
        detail = {}
    if raw_due is not None and due_at is None:
        knowledge_status = "unknown"
        detail["time_expression"] = _safe_json_value(raw_due)
        detail["time_status"] = "unreadable_or_ambiguous"
    source_refs_value = item.get("source_refs", [event_id])
    refs = {
        ref
        for ref in source_refs_value
        if isinstance(ref, str) and ref in available_ids
    } if isinstance(source_refs_value, list) else set()
    refs.add(event_id)
    return {
        "source_event_id": event_id,
        "kind": _slug(_clean_text(item.get("kind") or item.get("type") or "task", limit=80)),
        "title": title,
        "status": _attention_status(item.get("status")),
        "knowledge_status": knowledge_status.casefold(),
        "starts_at": starts_at,
        "due_at": due_at,
        "timezone": timezone_name,
        "source_refs": sorted(refs),
        "details": detail,
    }


def normalize_extraction(
    parsed: Any,
    *,
    events: list[dict[str, Any]],
    available_ids: set[str],
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize open-world provider output without a benchmark ontology."""

    if not isinstance(parsed, dict):
        return [], [], [], []
    batch_ids = {
        str(event.get("event_id"))
        for event in events
        if isinstance(event.get("event_id"), str)
    }
    raw_facts = parsed.get("facts")
    if not isinstance(raw_facts, list):
        raw_facts = parsed.get("observations", [])
    if not isinstance(raw_facts, list):
        raw_facts = []
    facts = [
        normalized
        for item in raw_facts
        for normalized in [normalize_fact(item, batch_ids=batch_ids, available_ids=available_ids)]
        if normalized is not None
    ]
    raw_relations = parsed.get("relationships", parsed.get("relations", []))
    if not isinstance(raw_relations, list):
        raw_relations = []
    relations = [
        normalized
        for item in raw_relations
        for normalized in [normalize_relation(item, batch_ids=batch_ids, available_ids=available_ids)]
        if normalized is not None
    ]
    raw_attention = parsed.get("attention", [])
    if not isinstance(raw_attention, list):
        raw_attention = []
    attention: list[dict[str, Any]] = []
    for event in events:
        event_attention = [
            item
            for item in raw_attention
            if isinstance(item, dict)
            and item.get("event_id", item.get("source_event_id")) == event.get("event_id")
        ]
        # A task/deadline fact is also a valid attention proposal.  This keeps
        # the provider schema compact while retaining generic facts.
        for fact in facts:
            if fact["source_event_id"] != event.get("event_id"):
                continue
            if fact["concept"] not in {"task", "deadline", "reminder", "obligation", "appointment"}:
                continue
            item: dict[str, Any] = {
                "event_id": event.get("event_id"),
                "kind": fact["concept"],
                "title": fact["entity_label"],
                "knowledge_status": fact["knowledge_status"],
                "source_refs": fact["source_refs"],
            }
            if isinstance(fact.get("value"), str):
                item["title"] = fact["value"]
            elif isinstance(fact.get("value"), dict):
                item.update(fact["value"])
            event_attention.append(item)
        for item in event_attention:
            normalized = normalize_attention(item, event=event, available_ids=available_ids, now=now)
            if normalized is not None:
                attention.append(normalized)
    attachment_results = parsed.get("attachment_results", parsed.get("attachments", []))
    if not isinstance(attachment_results, list):
        attachment_results = []
    return facts, relations, attention, [
        _safe_json_value(item) for item in attachment_results if isinstance(item, dict)
    ]


def _parse_model_json(text: str) -> dict[str, Any] | None:
    candidates = [text.strip()]
    if text.strip().startswith("```"):
        candidates.append("\n".join(line for line in text.splitlines() if not line.strip().startswith("```")).strip())
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first : last + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    return None


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|auth(?:orization)?|bearer|cookie|credential|password|secret|token)\b\s*[:=]\s*)([^\s,;]+)"
)
_DIAGNOSTIC_LINE = re.compile(
    r"(?i)\b(error|warn(?:ing)?|fail(?:ed|ure)?|invalid|unexpected|unsupported|unknown|timeout|timed out|denied|permission|usage)\b"
)


def _decode_process_output(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if isinstance(value, str) else ""


def _sanitize_provider_output(value: Any) -> str | None:
    """Keep only bounded diagnostic lines and redact credential-shaped values."""

    text = _decode_process_output(value)
    lines: list[str] = []
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate or not _DIAGNOSTIC_LINE.search(candidate):
            continue
        candidate = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", candidate)
        candidate = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", candidate)
        lines.append(candidate[:500])
        if sum(len(item) for item in lines) >= 1000:
            break
    result = "\n".join(lines)[:1000]
    return result or None


def product_database_path(home: str | Path) -> Path:
    """Return the single authoritative Product V2 database for one Home."""

    return Path(home).expanduser().resolve() / PRODUCT_DATABASE_NAME


class ProductCodexProvider:
    """Bounded, ephemeral Codex CLI adapter for Product V2.

    The installed CLI surface observed for this runtime is ``codex exec`` with
    ``--image`` for direct image inputs.  Each call uses an ephemeral session,
    read-only sandbox, no approval prompts, an isolated temporary workspace,
    and an explicit read-only additional directory for stored attachments.
    No auth material or raw provider output is persisted by Blackhole.
    """

    def __init__(
        self,
        *,
        home: str | Path,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        model: str = DEFAULT_MODEL,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    ) -> None:
        if timeout < 1:
            raise ValueError("timeout must be positive")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be non-empty")
        if reasoning_effort not in {"low", "medium", "high", "max"}:
            raise ValueError("unsupported reasoning effort")
        self.home = Path(home).expanduser().resolve()
        self.timeout = timeout
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.call_count = 0
        self.last_call: dict[str, Any] | None = None
        self._version_cache: str | None = None

    @staticmethod
    def _schema_path(directory: Path) -> Path:
        path = directory / "product-v2-output-schema.json"
        path.write_text(
            json.dumps(
                {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "facts": {"type": "array"},
                        "observations": {"type": "array"},
                        "relationships": {"type": "array"},
                        "attention": {"type": "array"},
                        "attachment_results": {"type": "array"},
                        "answer": {"type": "string"},
                        "source_refs": {"type": "array"},
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def _cli_version(self, cli: str) -> str | None:
        if self._version_cache is not None:
            return self._version_cache
        try:
            result = subprocess.run(
                [cli, "--version"],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        output = "\n".join(
            part
            for part in (_decode_process_output(result.stdout), _decode_process_output(result.stderr))
            if part
        )
        match = re.search(r"\b\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9.]+)?\b", output)
        self._version_cache = f"codex-cli {match.group(0)}" if match else None
        return self._version_cache

    def _invocation_summary(self, image_count: int) -> list[str]:
        command = [
            "exec",
            "--ephemeral",
            "--json",
            "--model",
            self.model,
            "-c",
            f"model_reasoning_effort={self.reasoning_effort}",
            "-s",
            "read-only",
            "--ignore-rules",
            "--skip-git-repo-check",
            "-C",
            "<isolated-workspace>",
            "--add-dir",
            "<blackhole-home>",
            "--output-schema",
            "<temporary-schema>",
        ]
        for _ in range(image_count):
            command.extend(["--image", "<stored-image>"])
        command.extend(["-o", "<temporary-output>", "-"])
        return command

    def _call(self, prompt: str, *, image_paths: list[str] | None = None) -> dict[str, Any]:
        cli = shutil.which("codex")
        if not cli:
            raise ProductProviderUnavailableError("provider unavailable: Codex CLI not found")
        self.call_count += 1
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="blackhole-product-provider-") as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            schema = self._schema_path(workspace)
            output = Path(directory) / "last-message.json"
            command = [
                cli,
                "exec",
                "--ephemeral",
                "--json",
                "--model",
                self.model,
                "-c",
                f"model_reasoning_effort={self.reasoning_effort}",
                "-s",
                "read-only",
                "--ignore-rules",
                "--skip-git-repo-check",
                "-C",
                str(workspace),
                "--add-dir",
                str(self.home),
                "--output-schema",
                str(schema),
            ]
            for image_path in image_paths or []:
                command.extend(["--image", image_path])
            command.extend(["-o", str(output), "-"])
            self.last_call = {
                "call_number": self.call_count,
                "executable": str(Path(cli).resolve()),
                "cli_version": self._cli_version(cli),
                "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "invocation": self._invocation_summary(len(image_paths or [])),
                "image_count": len(image_paths or []),
                "returncode": None,
                "timed_out": False,
            }
            try:
                completed = subprocess.run(
                    command,
                    input=prompt.encode("utf-8"),
                    capture_output=True,
                    timeout=self.timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                self.last_call.update(
                    {
                        "duration_seconds": round(time.monotonic() - started, 3),
                        "timed_out": True,
                        "stdout": _sanitize_provider_output(getattr(error, "stdout", None)),
                        "stderr": _sanitize_provider_output(getattr(error, "stderr", None)),
                    }
                )
                raise ProductProviderExecutionError(
                    "semantic provider timed out; retry available",
                    diagnostic=self.last_call,
                ) from error
            except OSError as error:
                self.last_call.update(
                    {
                        "duration_seconds": round(time.monotonic() - started, 3),
                        "error_type": type(error).__name__,
                        "stderr": _sanitize_provider_output(str(error)),
                    }
                )
                raise ProductProviderExecutionError(
                    "semantic provider could not start; retry available",
                    diagnostic=self.last_call,
                ) from error
            stdout = _decode_process_output(completed.stdout)
            stderr = _decode_process_output(completed.stderr)
            self.last_call.update(
                {
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "returncode": completed.returncode,
                    "stdout": _sanitize_provider_output(stdout),
                    "stderr": _sanitize_provider_output(stderr),
                }
            )
            if completed.returncode != 0:
                detail = self.last_call.get("stderr") or self.last_call.get("stdout") or f"exit code {completed.returncode}"
                raise ProductProviderExecutionError(
                    f"semantic provider failed (exit code {completed.returncode}): {detail}; retry available",
                    diagnostic=self.last_call,
                )
            try:
                raw_text = output.read_text(encoding="utf-8") if output.exists() else ""
            except OSError as error:
                raise ProductProviderExecutionError(
                    "semantic provider output could not be read; retry available",
                    diagnostic=self.last_call,
                ) from error
            parsed = _parse_model_json(raw_text)
            if parsed is None:
                for line in reversed(stdout.splitlines()):
                    candidate = _parse_model_json(line)
                    if candidate is not None:
                        parsed = candidate
                        break
            if parsed is None:
                self.last_call["error_type"] = "unreadable_json"
                raise ProductProviderExecutionError(
                    "semantic provider returned unreadable JSON; retry available",
                    diagnostic=self.last_call,
                )
            return parsed

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "runtime" / "product-v2.md"
        instruction = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else (
            "Extract only supported facts from the supplied captures. Return JSON."
        )
        images = [
            str(attachment["path"])
            for event in events
            for attachment in event.get("attachments", [])
            if isinstance(attachment, dict)
            and str(attachment.get("mime_type", "")).casefold().startswith("image/")
            and isinstance(attachment.get("path"), str)
        ]
        payload = {
            "time_context": time_context,
            "contract": contract,
            "prior_memory": prior_memory,
            "captures": events,
        }
        return self._call(instruction + "\n\nINPUT:\n" + json.dumps(payload, ensure_ascii=False, indent=2), image_paths=images)

    def answer(
        self,
        *,
        question: str,
        context: dict[str, Any],
        time_context: dict[str, Any],
    ) -> dict[str, Any]:
        instruction = (
            "You are Blackhole's bounded personal-memory answerer. Answer the question concisely "
            "using only the supplied structured memory and source references. Do not invent facts. "
            "Return one JSON object with a short string `answer` and an array `source_refs`; include "
            "only references present in the context. If the context is insufficient, say so explicitly."
        )
        payload = {"question": question, "time_context": time_context, "context": context}
        return self._call(instruction + "\n\nINPUT:\n" + json.dumps(payload, ensure_ascii=False, indent=2))

    def close(self) -> None:
        return None


def _provider_unavailable(status: Any) -> str:
    if isinstance(status, ProviderStatus):
        if status.status == "MISSING":
            return "provider unavailable: Codex CLI not found"
        if status.status == "INSTALLED_NOT_AUTHENTICATED":
            return "provider unavailable: Codex CLI is not authenticated"
    return "provider unavailable: configured semantic provider is not ready"


class ProductRuntime:
    """Product V2 facade with durable background ingestion and retrieval Ask."""

    def __init__(
        self,
        home: str | Path,
        *,
        db_path: str | Path | None = None,
        provider: ProductSemanticProvider | Any | None = None,
        provider_factory: Callable[[], Any] | None = None,
        discovery_fn: Callable[..., Any] | None = None,
        model: str = DEFAULT_MODEL,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        lease_seconds: int = 120,
        start_worker: bool = True,
        auto_start_on_capture: bool | None = None,
        store: ProductStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.home = Path(home).expanduser().resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self.batch_size = batch_size
        self.lease_seconds = lease_seconds
        self.provider = provider
        self.provider_factory = provider_factory
        self.discovery_fn = discovery_fn
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.store = store or ProductStore(
            db_path or product_database_path(self.home),
            home=self.home,
            legacy_database_path=self.home / "blackhole.db",
        )
        self._owns_store = store is None
        self._owner_id = f"product-worker-{uuid.uuid4().hex}"
        self._capture_lock = threading.RLock()
        self._provider_lock = threading.RLock()
        self._worker_stop = threading.Event()
        self._worker_wake = threading.Event()
        self._worker: threading.Thread | None = None
        self._closed = False
        self._auto_start_on_capture = start_worker if auto_start_on_capture is None else auto_start_on_capture
        self.last_provider_diagnostic: dict[str, Any] | None = None
        if start_worker:
            self.start_worker()

    def start_worker(self) -> None:
        with self._capture_lock:
            if self._closed:
                raise RuntimeError("ProductRuntime is closed")
            self.store.recover_stale_processing()
            if self._worker is not None and self._worker.is_alive():
                return
            self._worker_stop.clear()
            self._worker = threading.Thread(
                target=self._worker_loop,
                name="blackhole-product-worker",
                daemon=True,
            )
            self._worker.start()

    def close(self) -> None:
        with self._capture_lock:
            if self._closed:
                return
            self._closed = True
            self._worker_stop.set()
            self._worker_wake.set()
            worker = self._worker
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=min(max(self.timeout_seconds, 1), 5))
        if (worker is None or not worker.is_alive()) and self._owns_store:
            self.store.close()

    def __enter__(self) -> "ProductRuntime":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _now(self) -> datetime:
        value = self.clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _attachment_input(item: Any) -> tuple[bytes, str | None, str]:
        if isinstance(item, bytes):
            return item, None, "application/octet-stream"
        if isinstance(item, (str, Path)):
            path = Path(item).expanduser().resolve()
            return path.read_bytes(), path.name, "application/octet-stream"
        if not isinstance(item, dict):
            raise ValueError("attachment must be bytes, a path, or an object")
        filename = item.get("filename", item.get("original_filename"))
        if filename is not None and (not isinstance(filename, str) or not filename.strip()):
            raise ValueError("attachment filename must be non-empty")
        if isinstance(filename, str):
            if (
                filename in {"", ".", ".."}
                or "/" in filename
                or "\\" in filename
                or "\x00" in filename
            ):
                raise ValueError("attachment filename is invalid")
        mime_type = item.get("mime_type", item.get("type", "application/octet-stream"))
        if not isinstance(mime_type, str) or not mime_type.strip():
            mime_type = "application/octet-stream"
        if isinstance(item.get("content"), bytes):
            return item["content"], filename, mime_type
        if isinstance(item.get("data"), bytes):
            return item["data"], filename, mime_type
        encoded = item.get("data_base64")
        if isinstance(encoded, str):
            try:
                return base64.b64decode(encoded, validate=True), filename, mime_type
            except (ValueError, base64.binascii.Error) as error:
                raise ValueError("attachment data_base64 is invalid") from error
        path_value = item.get("path")
        if isinstance(path_value, str):
            path = Path(path_value).expanduser().resolve()
            return path.read_bytes(), filename or path.name, mime_type
        raise ValueError("attachment content is required")

    def capture(
        self,
        text: str | None = None,
        *,
        attachments: Iterable[Any] | None = None,
        attachment: Any | None = None,
        source_type: str | None = None,
        event_id: str | None = None,
        captured_at: str | None = None,
        observed_at: str | None = None,
        timezone_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist a capture and return without waiting for semantic work."""

        if text is not None and (not isinstance(text, str) or not text.strip()):
            raise ValueError("capture text must not be empty")
        if isinstance(text, str) and len(text) > MAX_CAPTURE_TEXT:
            raise ValueError("capture text is too long")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("capture metadata must be an object")
        inputs = list(attachments or [])
        if attachment is not None:
            inputs.append(attachment)
        if text is None and not inputs:
            raise ValueError("capture requires text or at least one attachment")
        timezone_value, zone = resolve_timezone(timezone_name)
        capture_time = self._now().astimezone(zone)
        if captured_at is not None:
            parsed = parse_datetime(captured_at, zone=zone)
            if parsed is None:
                raise ValueError("captured_at must be an ISO timestamp")
            captured_value = captured_at
            capture_time = parsed
        else:
            captured_value = capture_time.isoformat()
        if observed_at is None:
            observed_at = capture_time.date().isoformat()
        if not isinstance(observed_at, str):
            raise ValueError("observed_at must be a date string")

        attachment_descriptors: list[dict[str, Any]] = []
        total_bytes = 0
        for index, item in enumerate(inputs):
            content, filename, mime_type = self._attachment_input(item)
            if len(content) > MAX_ATTACHMENT_BYTES:
                raise ValueError("attachment is too large")
            total_bytes += len(content)
            if total_bytes > MAX_TOTAL_ATTACHMENT_BYTES:
                raise ValueError("combined attachments are too large")
            digest, byte_length, _path = self.store.blobs.put(content)
            attachment_descriptors.append(
                {
                    "sha256": digest,
                    "blob_ref": f"sha256:{digest}",
                    "original_filename": filename,
                    "mime_type": mime_type,
                    "byte_length": byte_length,
                    "attachment_index": index,
                }
            )
        if source_type is None:
            if not text and attachment_descriptors and all(
                str(item["mime_type"]).casefold().startswith("image/") for item in attachment_descriptors
            ):
                source_type = "image"
            elif attachment_descriptors:
                source_type = "document"
            else:
                source_type = "text"
        if not isinstance(source_type, str) or not source_type.strip():
            raise ValueError("source_type must be non-empty")
        payload: dict[str, Any] = {}
        if text is not None:
            payload["text"] = text
        if attachment_descriptors:
            payload["attachments"] = attachment_descriptors
        event_id = event_id or f"capture-{uuid.uuid4().hex}"
        event = {
            "event_id": event_id,
            # ProductStore allocates this inside the same write transaction as
            # the source row, avoiding sequence races between Host instances.
            "sequence": None,
            "captured_at": captured_value,
            "timezone": timezone_value,
            "observed_at": observed_at,
            "source_type": source_type.strip(),
            "payload": payload,
            "metadata": copy.deepcopy(metadata or {}),
        }
        inserted = self.store.insert_capture(event, attachments=attachment_descriptors)
        if self._auto_start_on_capture:
            self.start_worker()
        self._worker_wake.set()
        processing = self.store.processing_status(event_id)
        return {
            "saved": True,
            "message": "Saved.",
            "event_id": event_id,
            "sequence": event["sequence"],
            "processing_status": (processing or {}).get("status", "pending"),
            "inserted": inserted,
            "attachments": [
                {
                    "sha256": item["sha256"],
                    "blob_ref": item["blob_ref"],
                    "original_filename": item["original_filename"],
                    "mime_type": item["mime_type"],
                    "byte_length": item["byte_length"],
                }
                for item in attachment_descriptors
            ],
        }

    def _provider(self) -> tuple[Any, bool]:
        if self.provider is not None:
            return self.provider, False
        if self.provider_factory is not None:
            return self.provider_factory(), True
        if self.discovery_fn is not None:
            try:
                status = self.discovery_fn(
                    configured_model=self.model,
                    configured_reasoning=self.reasoning_effort,
                )
                if isinstance(status, dict):
                    ready = bool(status.get("ready"))
                else:
                    ready = bool(getattr(status, "ready", False))
                if not ready:
                    raise ProductProviderUnavailableError(_provider_unavailable(status))
            except ProductProviderUnavailableError:
                raise
            except Exception as error:
                del error
                raise ProductProviderUnavailableError("provider unavailable: readiness check failed") from None
        return ProductCodexProvider(
            home=self.home,
            timeout=self.timeout_seconds,
            model=self.model,
            reasoning_effort=self.reasoning_effort,
        ), True

    @staticmethod
    def _extract_call(provider: Any, *, events: list[dict[str, Any]], prior_memory: dict[str, Any], time_context: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
        method = getattr(provider, "extract", None)
        if not callable(method):
            raise RuntimeError("semantic provider does not support extraction")
        try:
            parameters = inspect.signature(method).parameters
        except (TypeError, ValueError):
            parameters = {}
        if "prior_memory" in parameters or any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
        ):
            return method(events=events, prior_memory=prior_memory, time_context=time_context, contract=contract)
        # Compatibility adapter for the existing V1-style fake/provider seam;
        # Product V2 still normalizes the result into its open-world schema.
        return method(events=events, prior_snapshot=prior_memory, contract=contract)

    def _process_claimed(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        events = sorted(events, key=lambda item: (int(item["sequence"]), str(item["event_id"])))
        event_ids = [str(event["event_id"]) for event in events]
        max_sequence = max(int(event["sequence"]) for event in events)
        available_ids = {
            str(event.get("event_id"))
            for event in self.store.raw_events(max_sequence=max_sequence)
            if isinstance(event.get("event_id"), str)
        }
        snapshot = self.store.snapshot(now=self._now())
        prior_memory = {
            "entities": snapshot.get("entities", []),
            "current_facts": snapshot.get("current_facts", []),
            "attention": snapshot.get("attention", []),
            "recent_sources": snapshot.get("sources", [])[-20:],
        }
        time_context = {
            "now_utc": self._now().isoformat(),
            "captures": [time_context_for_event(event, now=self._now()) for event in events],
        }
        provider: Any | None = None
        try:
            with self._provider_lock:
                provider, owned = self._provider()
                try:
                    parsed = self._extract_call(
                        provider,
                        events=events,
                        prior_memory=prior_memory,
                        time_context=time_context,
                        contract={
                            "runtime": PRODUCT_RUNTIME_VERSION,
                            "prompt": PRODUCT_PROMPT_VERSION,
                            "open_world": True,
                            "known_inferred_unknown": True,
                        },
                    )
                finally:
                    if owned and callable(getattr(provider, "close", None)):
                        provider.close()
                    diagnostic = getattr(provider, "last_call", None)
                    if isinstance(diagnostic, dict):
                        self.last_provider_diagnostic = copy.deepcopy(diagnostic)
            facts, relations, attention, attachment_results = normalize_extraction(
                parsed,
                events=events,
                available_ids=available_ids,
                now=self._now(),
            )
            for event in events:
                event_results = [
                    item
                    for item in attachment_results
                    if item.get("event_id") in {None, event.get("event_id")}
                ]
                for result in event_results:
                    sha256 = result.get("sha256")
                    status = result.get("status")
                    if isinstance(sha256, str) and isinstance(status, str):
                        try:
                            self.store.record_attachment_processing(
                                str(event["event_id"]),
                                sha256,
                                status=status.casefold(),
                                detail=_clean_text(result.get("detail"), limit=500) or None,
                            )
                        except ValueError:
                            pass
            committed = self.store.commit_semantic(
                self._owner_id,
                event_ids,
                facts=facts,
                relations=relations,
                attention=attention,
                extractor_version=PRODUCT_EXTRACTOR_VERSION,
            )
            return {
                "requested": len(events),
                "processed": len(event_ids),
                "failed": 0,
                "event_ids": event_ids,
                "facts_added": committed["facts_added"],
                "relations_added": committed["relations_added"],
                "attention_added": committed["attention_added"],
                "semantic_effects": committed["facts_added"] + committed["relations_added"] + committed["attention_added"],
                "projection_run_id": committed["projection_run_id"],
            }
        except Exception as error:
            diagnostic = getattr(error, "diagnostic", None)
            if isinstance(diagnostic, dict):
                self.last_provider_diagnostic = copy.deepcopy(diagnostic)
            elif isinstance(getattr(provider, "last_call", None), dict):
                self.last_provider_diagnostic = copy.deepcopy(provider.last_call)
            if isinstance(error, ProductProviderUnavailableError):
                message = str(error)
            elif isinstance(error, ProductProviderExecutionError):
                message = str(error)
            else:
                message = "semantic provider failed; retry available"
            status = self.store.processing_status(event_ids[0]) if event_ids else None
            attempt = int(status.get("attempt_count", 1)) if status else 1
            retry_after = (
                AUTOMATIC_RETRY_BACKOFF_SECONDS[attempt - 1]
                if 1 <= attempt < MAX_AUTOMATIC_ATTEMPTS
                else 0
            )
            failed = self.store.mark_failed(
                self._owner_id,
                event_ids,
                error=message,
                retry_after_seconds=retry_after,
            )
            return {
                "requested": len(events),
                "processed": 0,
                "failed": failed,
                "event_ids": event_ids,
                "failed_event_ids": event_ids[:failed],
                "error": message,
                "semantic_effects": 0,
            }

    def _worker_loop(self) -> None:
        while not self._worker_stop.is_set():
            try:
                self.store.recover_stale_processing()
                events = self.store.claim_pending(
                    self._owner_id,
                    limit=self.batch_size,
                    lease_seconds=self.lease_seconds,
                )
                if not events:
                    # Failed work is retried only after its durable backoff;
                    # explicit retry_failed() clears that backoff immediately.
                    events = self.store.claim_failed(
                        self._owner_id,
                        limit=self.batch_size,
                        lease_seconds=self.lease_seconds,
                    )
                if events:
                    self._process_claimed(events)
                    continue
            except Exception:
                # A worker loop must stay alive for later captures.  Event
                # claims have leases and are recovered on the next iteration or
                # by the next runtime process.
                pass
            self._worker_wake.wait(0.15)
            self._worker_wake.clear()

    def processing_status(self, event_id: str | None = None) -> dict[str, Any] | None:
        self.store.recover_stale_processing()
        return self.store.processing_status(event_id)

    def process_pending(self, *, limit: int | None = None) -> dict[str, Any]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")
        requested_limit = limit if limit is not None else 2**31 - 1
        results: list[dict[str, Any]] = []
        while requested_limit > 0:
            events = self.store.claim_pending(
                self._owner_id,
                limit=min(self.batch_size, requested_limit),
                lease_seconds=self.lease_seconds,
            )
            if not events:
                break
            result = self._process_claimed(events)
            results.append(result)
            requested_limit -= len(events)
            if result.get("failed"):
                break
        aggregate = {
            "requested": sum(int(item.get("requested", 0)) for item in results),
            "processed": sum(int(item.get("processed", 0)) for item in results),
            "failed": sum(int(item.get("failed", 0)) for item in results),
            "facts_added": sum(int(item.get("facts_added", 0)) for item in results),
            "relations_added": sum(int(item.get("relations_added", 0)) for item in results),
            "attention_added": sum(int(item.get("attention_added", 0)) for item in results),
            "semantic_effects": sum(int(item.get("semantic_effects", 0)) for item in results),
            "batches": len(results),
            "errors": [item["error"] for item in results if item.get("error")],
            "processed_event_ids": [event_id for item in results for event_id in item.get("event_ids", []) if not item.get("failed")],
            "failed_event_ids": [event_id for item in results for event_id in item.get("failed_event_ids", [])],
        }
        status = self.processing_status() or {"counts": {}}
        aggregate.update(
            {
                "pending_count": status.get("counts", {}).get("pending", 0),
                "processing_count": status.get("counts", {}).get("processing", 0),
                "failed_count": status.get("counts", {}).get("failed", 0),
                "state_fresh": status.get("counts", {}).get("pending", 0) == 0
                and status.get("counts", {}).get("processing", 0) == 0
                and status.get("counts", {}).get("failed", 0) == 0,
            }
        )
        return aggregate

    def retry_failed(self, event_id: str | None = None, *, limit: int | None = None) -> dict[str, Any]:
        retried = self.store.retry_failed(event_id, limit=limit)
        if retried and self._auto_start_on_capture:
            self.start_worker()
        self._worker_wake.set()
        status = self.processing_status() or {"counts": {}}
        return {
            "retried": retried,
            "processed": 0,
            "failed": 0,
            "pending_count": status.get("counts", {}).get("pending", 0),
            "failed_count": status.get("counts", {}).get("failed", 0),
        }

    def retract(self, event_id: str, *, reason: str = "user undo") -> dict[str, Any]:
        result = self.store.retract(event_id, reason=reason)
        self._worker_wake.set()
        return result

    def set_attention_status(self, fingerprint: str, status: str, *, note: str | None = None) -> dict[str, Any]:
        return self.store.set_attention_status(fingerprint, status, note=note)

    def snapshot(self) -> dict[str, Any]:
        return self.store.snapshot(now=self._now())

    def state(self) -> dict[str, Any]:
        """Return memory and Attention without triggering semantic work."""

        return self.snapshot()

    def wait_for_idle(self, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + max(timeout, 0)
        while time.monotonic() < deadline:
            status = self.processing_status() or {"counts": {}}
            counts = status.get("counts", {})
            if int(counts.get("pending", 0)) == 0 and int(counts.get("processing", 0)) == 0:
                return True
            time.sleep(0.01)
        return False

    def _retrieval_context(self, question: str) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
        snapshot = self.store.snapshot(now=self._now())
        question_tokens = _tokens(question)
        facts = snapshot.get("current_facts", [])
        scored: list[tuple[int, dict[str, Any]]] = []
        for item in facts:
            searchable = " ".join(
                str(item.get(key, "")) for key in ("entity_key", "entity_label", "concept", "value", "unknown_reason")
            )
            overlap = len(question_tokens & _tokens(searchable))
            if overlap:
                scored.append((overlap, item))
        scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("entity_key", "")), str(pair[1].get("concept", ""))))
        selected_facts = [item for _score, item in scored[:MAX_ASK_CONTEXT_FACTS]]
        history = snapshot.get("fact_history", [])
        history_scored: list[tuple[int, int, dict[str, Any]]] = []
        for item in history:
            if item.get("retracted"):
                continue
            searchable = " ".join(str(item.get(key, "")) for key in ("entity_key", "entity_label", "concept", "value", "operation"))
            overlap = len(question_tokens & _tokens(searchable))
            if overlap:
                history_scored.append((overlap, -int(item.get("sequence", 0)), item))
        history_scored.sort(key=lambda pair: (-pair[0], pair[1]))
        selected_history = [item for _score, _sequence, item in history_scored[:MAX_ASK_CONTEXT_HISTORY]]
        recent_changes = [
            item
            for item in reversed(history)
            if not item.get("retracted")
            and item.get("operation") in {"correction", "supersede", "contradiction"}
        ]
        for item in recent_changes:
            if item not in selected_history:
                selected_history.append(item)
            if len(selected_history) >= MAX_ASK_CONTEXT_HISTORY:
                break
        broad_question = bool(
            question_tokens
            & {"locations", "location", "recorded", "remembered", "things", "items", "anything", "list"}
        )
        if not selected_facts and broad_question:
            selected_facts = list(facts[:MAX_ASK_CONTEXT_FACTS])
        text = " ".join(question_tokens)
        context = {
            "facts": selected_facts,
            "history": selected_history,
            "attention": snapshot.get("attention", [])[:MAX_ASK_CONTEXT_HISTORY],
            "relationships": snapshot.get("relationships", [])[:MAX_ASK_CONTEXT_HISTORY],
            "sources": snapshot.get("sources", [])[-MAX_ASK_CONTEXT_HISTORY:],
        }
        return context, selected_facts, text

    @staticmethod
    def _money_summary(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        totals: dict[tuple[str, str], Decimal] = {}
        for item in items:
            value = item.get("value")
            if not isinstance(value, dict):
                continue
            amount = value.get("amount", value.get("price", value.get("total")))
            currency = value.get("currency", value.get("currency_code"))
            if amount is None or not isinstance(currency, str):
                continue
            try:
                decimal = Decimal(str(amount))
            except (InvalidOperation, ValueError):
                continue
            period = str(value.get("billing_period", value.get("period", "")))
            totals[(currency.upper(), period)] = totals.get((currency.upper(), period), Decimal("0")) + decimal
        return [
            {"currency": currency, "billing_period": period, "total": format(total, "f")}
            for (currency, period), total in sorted(totals.items())
        ]

    @staticmethod
    def _source_refs(items: Iterable[dict[str, Any]]) -> list[str]:
        return sorted(
            {
                ref
                for item in items
                for ref in item.get("source_refs", [])
                if isinstance(ref, str) and ref
            }
        )

    def _deterministic_answer(
        self,
        question: str,
        snapshot: dict[str, Any],
        context: dict[str, Any],
        selected_facts: list[dict[str, Any]],
    ) -> tuple[str | None, str, list[dict[str, Any]], list[str]]:
        lowered = question.casefold()
        question_tokens = _tokens(question)
        attention = [item for item in snapshot.get("attention", []) if item.get("status") == "open"]
        is_today = bool(question_tokens & {"today", "dzisiaj", "dziś"})
        is_upcoming = bool(question_tokens & {"upcoming", "coming", "week", "tydzień", "tydzien", "nadchodzący", "nadchodzacy"})
        is_task = bool(question_tokens & {"need", "task", "tasks", "do", "todo", "muszę", "musze", "zrobić", "zrobic"})
        if (is_today and is_task) or (is_upcoming and is_task):
            now = self._now()
            horizon = now + timedelta(days=7 if is_upcoming else 1)
            selected_attention: list[dict[str, Any]] = []
            for item in attention:
                due_value = item.get("due_at") or item.get("starts_at")
                due = parse_datetime(due_value, zone=timezone.utc) if due_value else None
                if is_today:
                    if due is None or due.astimezone(now.tzinfo).date() != now.date():
                        continue
                elif due is not None and due > horizon:
                    continue
                selected_attention.append(item)
            if not selected_attention:
                return "Nothing matching that time window is currently open.", "attention", [], []
            labels = [item["title"] for item in selected_attention[:10]]
            return "Open items: " + "; ".join(labels) + ".", "attention", selected_attention, self._source_refs(selected_attention)

        is_time_question = bool(
            question_tokens
            & {"when", "kiedy", "deadline", "due", "date", "termin", "datę", "date", "until", "do"}
        )
        if attention and (is_time_question or is_task):
            attention_tokens = [
                item
                for item in attention
                if question_tokens
                & _tokens(" ".join(str(item.get(key, "")) for key in ("title", "kind", "details")))
            ]
            selected_attention = attention_tokens or attention[:MAX_ASK_CONTEXT_HISTORY]
            labels = [item["title"] for item in selected_attention[:10]]
            return "Relevant attention: " + "; ".join(labels) + ".", "attention", selected_attention, self._source_refs(selected_attention)

        is_change_marker = {"changed", "change", "changes", "recent", "correction", "zmieniło", "zmienilo", "zmiana", "ostatnio"}
        is_cost = bool(question_tokens & {"paying", "pay", "cost", "costs", "price", "prices", "subscription", "subscriptions", "billing", "płacę", "place", "koszt", "koszty"}) and not bool(question_tokens & is_change_marker)
        if is_cost:
            cost_facts = [
                item
                for item in snapshot.get("current_facts", [])
                if isinstance(item.get("value"), dict)
                and (
                    item.get("concept") in {"price", "cost", "monthly_cost", "subscription", "payment", "current_price", "historical_price"}
                    or any(key in item.get("value", {}) for key in ("amount", "price", "total"))
                )
            ]
            if not cost_facts:
                return "I do not have a supported payment or cost observation yet.", "costs", [], []
            def cost_description(item: dict[str, Any]) -> str:
                value = item.get("value")
                if isinstance(value, dict):
                    amount = value.get("amount", value.get("price", value.get("total")))
                    currency = value.get("currency", value.get("currency_code"))
                    period = value.get("billing_period", value.get("period"))
                    if amount is not None and currency:
                        suffix = f" per {period}" if period else ""
                        return f"{item.get('entity_label', item.get('entity_key'))}: {amount} {currency}{suffix}"
                return f"{item.get('entity_label', item.get('entity_key'))}: {value}"

            descriptions = [cost_description(item) for item in cost_facts[:10]]
            totals = self._money_summary(cost_facts)
            suffix = f" Deterministic totals: {totals}." if totals else ""
            return "Observed costs: " + "; ".join(descriptions) + "." + suffix, "costs", cost_facts, self._source_refs(cost_facts)

        is_change = bool(question_tokens & is_change_marker) and not (
            "how" in lowered and ("should" in lowered or "next" in lowered)
        )
        if is_change:
            changes = [
                item
                for item in context.get("history", [])
                if item.get("operation") in {"correction", "supersede", "contradiction"}
            ]
            changes.extend(
                item
                for item in context.get("relationships", [])
                if item.get("relation_type") in {"meaningful_change", "correction", "supersession"}
            )
            if not changes:
                return "I do not have a recorded recent change matching that question.", "changes", [], []
            history = context.get("history", [])
            change_keys = {
                (item.get("entity_key"), item.get("concept"))
                for item in changes
                if item.get("entity_key") is not None and item.get("concept") is not None
            }
            expanded_changes: list[dict[str, Any]] = []
            seen_change_items: set[tuple[Any, ...]] = set()
            for item in history:
                key = (item.get("entity_key"), item.get("concept"))
                if key not in change_keys:
                    continue
                identity = (
                    item.get("source_event_id"),
                    item.get("fact_id"),
                    item.get("operation"),
                    canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                )
                if identity not in seen_change_items:
                    expanded_changes.append(item)
                    seen_change_items.add(identity)
            expanded_changes.extend(
                item
                for item in changes
                if item not in expanded_changes
            )
            expanded_changes.sort(key=lambda item: int(item.get("sequence", 0)))

            def display_value(item: dict[str, Any]) -> str:
                if "value" in item:
                    value = item.get("value")
                    if isinstance(value, dict):
                        amount = value.get("amount", value.get("price", value.get("total")))
                        currency = value.get("currency", value.get("currency_code"))
                        if amount is not None and currency:
                            period = value.get("billing_period", value.get("period"))
                            suffix = f" per {period}" if period else ""
                            return f"{amount} {currency}{suffix}"
                        return json.dumps(value, ensure_ascii=False, sort_keys=True)
                    if isinstance(value, list):
                        return json.dumps(value, ensure_ascii=False, sort_keys=True)
                    return str(value)
                return str(item.get("unknown_reason", "unknown"))

            labels = []
            for item in expanded_changes[:10]:
                label = item.get("entity_label", item.get("source_entity_key", "memory"))
                operation = item.get("operation", item.get("relation_type"))
                labels.append(f"{label}: {operation} ({display_value(item)})")
            return "Recent changes: " + "; ".join(labels) + ".", "changes", expanded_changes, self._source_refs(expanded_changes)

        is_last = bool(question_tokens & {"last", "mention", "mentioned", "when", "kiedy", "wspomniałem", "wspomnialem"})
        if is_last:
            matches = context.get("history", []) or selected_facts
            if matches:
                if "last" not in question_tokens and selected_facts:
                    return (
                        "Relevant memory: " + "; ".join(
                            f"{item.get('entity_label', item.get('entity_key'))} {item.get('concept')}: {item.get('value', item.get('unknown_reason', 'unknown'))}"
                            for item in selected_facts[:10]
                        ) + ".",
                        "retrieval",
                        selected_facts,
                        self._source_refs(selected_facts),
                    )
                latest = sorted(matches, key=lambda item: int(item.get("sequence", 0)), reverse=True)[0]
                ref = latest.get("source_refs", [])
                source = next((item for item in snapshot.get("sources", []) if item.get("event_id") in ref), None)
                when = source.get("captured_at") if source else "an earlier capture"
                label = latest.get("entity_label", latest.get("entity_key", "that topic"))
                return f"The latest matching mention of {label} is {when}.", "last_mention", [latest], self._source_refs([latest])

        if (
            len(selected_facts) > 1
            and question_tokens & {"keys", "key", "klucze", "kluczyk"}
            and not question_tokens & {"basement", "piwnicy", "house", "home", "bike", "roweru"}
        ):
            refs = self._source_refs(selected_facts)
            if question_tokens & {"gdzie", "są", "jest"}:
                return "To jest niejednoznaczne — nie wiadomo, które klucze masz na myśli.", "retrieval", selected_facts, refs
            return "The question is ambiguous; I found more than one kind of key.", "retrieval", selected_facts, refs

        requires_synthesis = bool(
            question_tokens
            & {"summarize", "summary", "synthesize", "explain", "connect", "compare", "why", "how"}
        )
        about_tokens = question_tokens - {"what", "do", "know", "about", "my", "the", "i", "have", "anything", "coming", "up", "this", "week"}
        if about_tokens and selected_facts and not requires_synthesis:
            return (
                "Relevant memory: " + "; ".join(
                    f"{item.get('entity_label', item.get('entity_key'))} {item.get('concept')}: {item.get('value', item.get('unknown_reason', 'unknown'))}"
                    for item in selected_facts[:10]
                ) + ".",
                "retrieval",
                selected_facts,
                self._source_refs(selected_facts),
            )
        return None, "semantic", selected_facts, self._source_refs(selected_facts)

    def ask(self, question: str) -> dict[str, Any]:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must not be empty")
        question = question.strip()
        snapshot = self.store.snapshot(now=self._now())
        processing = snapshot.get("processing", {})
        counts = processing.get("counts", {}) if isinstance(processing, dict) else {}
        failed_count = int(counts.get("failed", 0) or 0)
        pending_count = int(counts.get("pending", 0) or 0)
        processing_count = int(counts.get("processing", 0) or 0)
        if failed_count:
            return {
                "question": question,
                "mode": "processing_failed",
                "status": "processing_failed",
                "answer": PROCESSING_FAILED_MESSAGE,
                "message": PROCESSING_FAILED_MESSAGE,
                "items": [],
                "source_refs": [],
                "provider_used": False,
                "processing": processing,
            }
        if pending_count or processing_count:
            return {
                "question": question,
                "mode": "processing",
                "status": "processing",
                "answer": PROCESSING_PENDING_MESSAGE,
                "message": PROCESSING_PENDING_MESSAGE,
                "items": [],
                "source_refs": [],
                "provider_used": False,
                "processing": processing,
            }
        context, selected_facts, _normalized = self._retrieval_context(question)
        deterministic, mode, items, refs = self._deterministic_answer(question, snapshot, context, selected_facts)
        if deterministic is not None:
            return {
                "question": question,
                "mode": mode,
                "answer": deterministic,
                "items": items,
                "source_refs": refs,
                "provider_used": False,
                "processing": snapshot.get("processing", {}),
            }
        provider_used = False
        answer: str | None = None
        provider: Any | None = None
        try:
            with self._provider_lock:
                provider, owned = self._provider()
                try:
                    method = getattr(provider, "answer", None)
                    if callable(method):
                        try:
                            parameters = inspect.signature(method).parameters
                        except (TypeError, ValueError):
                            parameters = {}
                        if "context" in parameters or any(
                            parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
                        ):
                            raw = method(
                                question=question,
                                context=context,
                                time_context={"now_utc": self._now().isoformat(), "timezone": local_timezone_name()},
                            )
                        else:
                            raw = method(question, context)
                        if isinstance(raw, str):
                            answer = raw.strip()
                            provider_refs: list[Any] = []
                        elif isinstance(raw, dict):
                            answer = _clean_text(raw.get("answer"), limit=4000)
                            provider_refs = raw.get("source_refs", []) if isinstance(raw.get("source_refs"), list) else []
                        else:
                            provider_refs = []
                        allowed_refs = set(refs) | {
                            reference
                            for item in context.get("sources", [])
                            for reference in [item.get("event_id")]
                            if isinstance(reference, str)
                        }
                        refs = sorted({reference for reference in provider_refs if isinstance(reference, str) and reference in allowed_refs} | set(refs))
                        provider_used = bool(answer)
                finally:
                    if owned and callable(getattr(provider, "close", None)):
                        provider.close()
        except (ProductProviderUnavailableError, RuntimeError) as error:
            diagnostic = getattr(error, "diagnostic", None)
            if isinstance(diagnostic, dict):
                self.last_provider_diagnostic = copy.deepcopy(diagnostic)
            elif isinstance(getattr(provider, "last_call", None), dict):
                self.last_provider_diagnostic = copy.deepcopy(provider.last_call)
            answer = None
        if not answer:
            answer = (
                "I found no matching structured memory yet."
                if not selected_facts
                else "I found relevant memory, but it needs a bounded semantic summary."
            )
        return {
            "question": question,
            "mode": "semantic" if provider_used else "retrieval",
            "answer": answer,
            "items": selected_facts,
            "source_refs": refs,
            "provider_used": provider_used,
            "processing": snapshot.get("processing", {}),
        }

    def attachment_bytes(self, sha256: str) -> tuple[bytes, dict[str, Any]]:
        return self.store.attachment_bytes(sha256)


__all__ = [
    "MAX_ATTACHMENT_BYTES",
    "MAX_CAPTURE_TEXT",
    "PRODUCT_DATABASE_NAME",
    "PRODUCT_EXTRACTOR_VERSION",
    "PRODUCT_PROCESSING_VERSION",
    "PRODUCT_PROMPT_VERSION",
    "PRODUCT_RUNTIME_VERSION",
    "ProductCodexProvider",
    "ProductProviderExecutionError",
    "ProductProviderUnavailableError",
    "ProductRuntime",
    "ProductSemanticProvider",
    "local_timezone_name",
    "normalize_extraction",
    "normalize_timestamp",
    "product_database_path",
    "resolve_timezone",
    "time_context_for_event",
]
