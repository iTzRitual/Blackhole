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
import hashlib
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

from app.ask_planner import AskPlan, plan_ask, search_terms
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


PRODUCT_RUNTIME_VERSION = "blackhole-product-v2-runtime-v2"
PRODUCT_DATABASE_NAME = "blackhole-v2.db"
PRODUCT_PROMPT_VERSION = "blackhole-product-v2-prompt-v4"
PROCESSING_PENDING_MESSAGE = "Still understanding your recent captures."
PROCESSING_FAILED_MESSAGE = "Some recent captures couldn't be understood yet. Your captures are still saved."
MAX_CAPTURE_TEXT = 100_000
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 25 * 1024 * 1024
MAX_ASK_CONTEXT_FACTS = 40
MAX_ASK_CONTEXT_HISTORY = 20
# A language the optional lexical planner cannot identify still needs a
# provider candidate set.  These are structured projections only, never raw
# capture replay.  The limits keep difficult questions bounded even when a
# Home contains a long history.
MAX_ASK_FALLBACK_FACTS = 40
MAX_ASK_FALLBACK_HISTORY = 20
MAX_ASK_SUPPORTING_EVIDENCE_IDS = MAX_ASK_CONTEXT_FACTS + MAX_ASK_CONTEXT_HISTORY

_ANSWER_COPY = {
    "en": {
        "processing": PROCESSING_PENDING_MESSAGE,
        "processing_failed": PROCESSING_FAILED_MESSAGE,
        "no_data": "I do not have any processed memory yet.",
        "no_match": "No supporting evidence matches that question in processed memory.",
        "attention_no_match": "No supporting evidence matched that attention request among currently open items.",
        "open_items": "Open items: ",
        "cost_no_match": "No supporting payment or cost evidence matches that question.",
        "observed_costs": "Observed costs: ",
        "recorded_history": " Recorded history: ",
        "deterministic_totals": " Deterministic totals: ",
        "changes_no_match": "No recorded change evidence matches that question.",
        "recent_changes": "Recent changes: ",
        "last_mention_no_match": "No recorded mention evidence matches that question.",
        "latest_mention": "The latest matching mention of ",
        "latest_mention_at": " is ",
        "relevant_memory": "Relevant memory: ",
        "relevant_attention": "Relevant attention: ",
    },
    "pl": {
        "processing": "Nadal analizuję Twoje ostatnie zapisy.",
        "processing_failed": "Niektórych ostatnich zapisów nie udało się jeszcze zrozumieć. Twoje zapisy są zachowane.",
        "no_data": "Nie mam jeszcze żadnych przetworzonych wspomnień.",
        "no_match": "W przetworzonej pamięci nie ma dowodów pasujących do tego pytania.",
        "attention_no_match": "Nie znaleziono dowodów pasujących do tej prośby wśród otwartych spraw.",
        "open_items": "Otwarte sprawy: ",
        "cost_no_match": "Nie znaleziono dowodów płatności ani kosztów pasujących do tego pytania.",
        "observed_costs": "Zaobserwowane koszty: ",
        "recorded_history": " Zapisana historia: ",
        "deterministic_totals": " Sumy obliczone deterministycznie: ",
        "changes_no_match": "Nie znaleziono zapisanych zmian pasujących do tego pytania.",
        "recent_changes": "Najnowsze zmiany: ",
        "last_mention_no_match": "Nie znaleziono zapisanej wzmianki pasującej do tego pytania.",
        "latest_mention": "Najnowsza pasująca wzmianka o ",
        "latest_mention_at": " jest z ",
        "relevant_memory": "Pasujące wspomnienia: ",
        "relevant_attention": "Pasujące sprawy: ",
    },
}


def _answer_copy(plan: AskPlan, key: str) -> str:
    """Return localized fast-path copy; unknown languages use provider copy."""

    language_copy = _ANSWER_COPY.get(plan.language, _ANSWER_COPY["en"])
    return language_copy[key]


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
    """Compatibility wrapper for the Product V2 retrieval tokenizer."""

    return search_terms(value)


def _searchable_text(item: dict[str, Any], keys: Iterable[str]) -> str:
    parts: list[str] = []
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
        else:
            parts.append(str(value))
    return " ".join(parts)


def _is_cost_fact(item: dict[str, Any]) -> bool:
    value = item.get("value")
    return isinstance(value, dict) and (
        item.get("concept")
        in {
            "price",
            "cost",
            "monthly_cost",
            "recurring_cost",
            "subscription",
            "payment",
            "current_price",
            "historical_price",
        }
        or any(key in value for key in ("amount", "price", "total"))
    )


def _display_fact_value(item: dict[str, Any]) -> str:
    metadata = item.get("metadata", item.get("semantic_metadata", {}))
    if not isinstance(metadata, dict):
        metadata = {}
    if item.get("knowledge_status") == "unknown":
        reason = item.get("unknown_reason", "not stated")
        conflicts = item.get("conflicting_values", metadata.get("conflicting_values", []))
        if reason == "conflicting" and isinstance(conflicts, list):
            alternatives: list[str] = []
            for conflict in conflicts:
                if not isinstance(conflict, dict) or conflict.get("value") is None:
                    continue
                alternative = str(conflict["value"])
                if conflict.get("negated"):
                    alternative = f"not {alternative}"
                alternatives.append(alternative)
            if alternatives:
                return f"unknown (conflicting evidence: {'; '.join(alternatives)})"
        return f"unknown ({reason})"
    value = item.get("value")
    negated = bool(item.get("negated") or metadata.get("negated"))
    if negated and value is True:
        concept = str(item.get("concept") or "fact").replace("_", " ")
        display = f"not {concept}"
    else:
        display = None
    if display is None:
        if isinstance(value, dict):
            amount = value.get("amount", value.get("price", value.get("total")))
            currency = value.get("currency", value.get("currency_code"))
            if amount is not None and currency:
                period = value.get("billing_period", value.get("period"))
                suffix = f" per {period}" if period else ""
                display = f"{amount} {currency}{suffix}"
            else:
                display = json.dumps(value, ensure_ascii=False, sort_keys=True)
        elif isinstance(value, list):
            display = json.dumps(value, ensure_ascii=False, sort_keys=True)
        elif value is None:
            display = "unknown"
        else:
            display = str(value)
    if negated and display is not None and not display.startswith("not "):
        display = f"not {display}"
    if item.get("knowledge_status") == "inferred":
        display = f"possibly {display} (not confirmed)"
    attribution = item.get("attribution", metadata.get("attribution"))
    if attribution is not None:
        if isinstance(attribution, dict):
            attribution_label = attribution.get("name") or attribution.get("role") or attribution.get("organization")
        else:
            attribution_label = attribution
        if attribution_label:
            display += f" (reported by {attribution_label})"
    return display


def _fact_summary(item: dict[str, Any]) -> str:
    label = item.get("entity_label") or item.get("entity_key") or "memory"
    concept = item.get("concept") or "fact"
    display = _display_fact_value(item)
    temporal = item.get("temporal")
    if not isinstance(temporal, dict):
        temporal = {}
    normalized = temporal.get("normalized")
    if isinstance(normalized, str) and normalized not in display:
        display += f" at {normalized}"
    elif temporal.get("expression") and temporal.get("precision"):
        display += f" ({temporal['precision']}: {temporal['expression']})"
    return f"{label} {concept}: {display}"


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
        nested = value.get("relative")
        if nested is not value:
            nested_delta = _relative_delta(nested)
            if nested_delta is not None:
                return nested_delta
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


def _temporal_fold(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = normalized.translate(
        str.maketrans({"ł": "l", "đ": "d", "ð": "d", "þ": "th", "ß": "ss"})
    )
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _weekday_index(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and 0 <= value <= 6:
        return value
    if isinstance(value, float) and value.is_integer() and 0 <= value <= 6:
        return int(value)
    if isinstance(value, dict):
        for key in ("weekday_index", "day_of_week_index", "weekday_number"):
            if key in value:
                parsed = _weekday_index(value[key])
                if parsed is not None:
                    return parsed
        for key in ("weekday", "day_of_week", "day"):
            if key in value:
                parsed = _weekday_index(value[key])
                if parsed is not None:
                    return parsed
        return None
    if not isinstance(value, str):
        return None
    folded = _temporal_fold(value).strip()
    if folded.isdigit() and 0 <= int(folded) <= 6:
        return int(folded)
    return None


def _local_time(value: Any) -> tuple[int, int] | None:
    if isinstance(value, dict):
        for key in ("local_time", "time", "at", "clock_time"):
            if key in value:
                parsed = _local_time(value[key])
                if parsed is not None:
                    return parsed
        hour = value.get("hour")
        minute = value.get("minute", 0)
        if isinstance(hour, (int, float)) and not isinstance(hour, bool) and isinstance(minute, (int, float)) and not isinstance(minute, bool):
            hour_int = int(hour)
            minute_int = int(minute)
            if 0 <= hour_int <= 23 and 0 <= minute_int <= 59:
                return hour_int, minute_int
        return None
    if not isinstance(value, str):
        return None
    text = _temporal_fold(value)
    match = re.search(r"(?<!\d)(\d{1,2})(?:\s*(?::|h|\.\s*)\s*(\d{2}))?\s*(am|pm)?(?!\d)", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)
    if match.group(2) is None and meridiem is None and not re.fullmatch(r"\s*\d{1,2}\s*", text):
        # Do not mistake the month or day in an ISO date for a clock time.
        return None
    if meridiem == "pm" and hour < 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    if hour > 23 or minute > 59:
        return None
    return hour, minute


def _weekday_datetime(value: Any, *, base: datetime) -> datetime | None:
    if isinstance(value, dict):
        day = _weekday_index(value)
        time_value = value.get("local_time", value.get("time", value))
        time_parts = _local_time(time_value)
        next_marker = bool(value.get("next", False))
    elif isinstance(value, str):
        day = _weekday_index(value)
        time_parts = _local_time(value)
        next_marker = bool(re.search(r"\bnext\b|\bnast[eę]pny\b|\bnaechste[nr]?\b", _temporal_fold(value)))
    else:
        return None
    if day is None:
        return None
    days_ahead = (day - base.weekday()) % 7
    if next_marker or days_ahead == 0:
        days_ahead = 7 if days_ahead == 0 else days_ahead
    target = base + timedelta(days=days_ahead)
    hour, minute = time_parts or (0, 0)
    return target.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _coarse_interval(value: Any, *, base: datetime) -> dict[str, Any] | None:
    """Return a coarse interval without pretending it is a point in time."""

    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    folded = _temporal_fold(text)
    if re.search(r"\bnext\s+week\b|\bnastepny\s+tydzien\b|\bnachste\s+woche\b", folded):
        start_date = (base - timedelta(days=base.weekday()) + timedelta(days=7)).date()
        end_date = start_date + timedelta(days=7)
        start = datetime.combine(start_date, datetime.min.time(), tzinfo=base.tzinfo)
        end = datetime.combine(end_date, datetime.min.time(), tzinfo=base.tzinfo)
        return {
            "interval_start": start.isoformat(),
            "interval_end": end.isoformat(),
            "precision": "week",
            "expression": text[:300],
        }

    month: int | None = None
    for alias, candidate in _MONTHS.items():
        if re.search(rf"\b{re.escape(_temporal_fold(alias))}\b", folded):
            month = candidate
            break
    has_day = bool(re.search(r"\b\d{1,2}(?:st|nd|rd|th)?\b", folded))
    if month is not None and not has_day:
        year = base.year
        start_date = date(year, month, 1)
        if start_date < base.date() and month != base.month:
            start_date = date(year + 1, month, 1)
        end_date = date(start_date.year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
        start = datetime.combine(start_date, datetime.min.time(), tzinfo=base.tzinfo)
        end = datetime.combine(end_date, datetime.min.time(), tzinfo=base.tzinfo)
        return {
            "interval_start": start.isoformat(),
            "interval_end": end.isoformat(),
            "precision": "month",
            "expression": text[:300],
        }

    if re.search(r"\b(?:tomorrow|jutro)\b", folded):
        tomorrow = (base + timedelta(days=1)).date().isoformat()
        return {"date": tomorrow, "precision": "day", "expression": text[:300]}
    if re.search(
        r"\b(?:around|about|approximately|approx|circa|okolo|około|ungef[aä]hr|alrededor|vers)\b",
        folded,
    ):
        return {"precision": "approximate", "expression": text[:300]}
    return None


def _natural_date(value: str, *, base: datetime) -> datetime | None:
    lowered = _temporal_fold(value).strip()
    if lowered in {"today", "dzisiaj", "dzis"}:
        return base.replace(hour=0, minute=0, second=0, microsecond=0)
    if lowered in {"tomorrow", "jutro"}:
        return (base + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    weekday = _weekday_datetime(value, base=base)
    if weekday is not None:
        return weekday
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
    weekday = _weekday_datetime(value, base=captured_at)
    if weekday is not None:
        return weekday.astimezone(zone).isoformat()
    parsed = parse_datetime(value, zone=zone)
    if parsed is not None:
        return parsed.isoformat()
    if isinstance(value, str):
        natural = _natural_date(value, base=captured_at)
        if natural is not None:
            return natural.astimezone(zone).isoformat()
    if isinstance(value, dict):
        for key in ("normalized", "iso", "datetime", "timestamp", "date", "value"):
            if key in value:
                normalized = normalize_timestamp(value[key], captured_at=captured_at, zone=zone)
                if normalized is not None:
                    return normalized
    return None


def normalize_temporal(
    value: Any,
    *,
    captured_at: datetime,
    zone: Any,
) -> dict[str, Any]:
    """Normalize temporal meaning while retaining coarse/ambiguous precision."""

    if value is None:
        return {}
    temporal = _safe_json_value(value) if isinstance(value, dict) else {"expression": _safe_json_value(value)}
    if not isinstance(temporal, dict):
        temporal = {"expression": str(value)[:300]}
    original = copy.deepcopy(temporal)
    for field in ("valid_from", "valid_to", "effective_at", "observed_at"):
        raw = temporal.get(field)
        if raw is None:
            continue
        normalized = normalize_timestamp(raw, captured_at=captured_at, zone=zone)
        if normalized is not None:
            temporal[field] = normalized
        else:
            temporal[f"{field}_expression"] = _safe_json_value(raw)
            temporal.pop(field, None)
    point_value = normalize_timestamp(value, captured_at=captured_at, zone=zone)
    if point_value is not None:
        # Strict provider schemas deliberately require nullable fields. A
        # present null is still an absent proposal at this boundary: replace
        # it with the deterministic result whenever structured temporal
        # fields make a point computable.
        temporal["normalized"] = point_value
        if temporal.get("precision") is None:
            temporal["precision"] = "minute" if _local_time(value) else "day"
    else:
        coarse = _coarse_interval(value, base=captured_at)
        if coarse is not None:
            for key, item in coarse.items():
                if temporal.get(key) is None:
                    temporal[key] = item
    if "expression" not in temporal and original != temporal:
        temporal["expression"] = original.get("expression", original)
    return _safe_json_value(temporal) or {}


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
    event: dict[str, Any] | None = None,
    now: datetime | None = None,
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
    certainty = item.get("certainty", item.get("epistemic_status"))
    certainty_text = _temporal_fold(certainty)
    claim_type = item.get("claim_type", item.get("claim_kind"))
    claim_type_text = _temporal_fold(claim_type)
    if status == "known" and (
        certainty_text in {"uncertain", "possible", "probable", "speculative", "unconfirmed", "maybe"}
        or claim_type_text in {"hypothesis", "speculation", "possible_diagnosis", "reported_speculation"}
    ):
        # A provider may be conservative in its prose but still emit a
        # legacy ``known`` status. Preserve the epistemic signal rather than
        # allowing a hypothesis to become a fact at the storage boundary.
        status = "inferred"
    has_value = "value" in item and item.get("value") is not None and not (
        isinstance(item.get("value"), str) and not item["value"].strip()
    )
    if status != "unknown" and not has_value:
        status = "unknown"
    raw_operation = item.get("operation", "set")
    operation_text = raw_operation.casefold().strip() if isinstance(raw_operation, str) else "set"
    semantic_relation = item.get("semantic_relation", item.get("relation"))
    if operation_text in {"change", "update", "observation", "resolve", "resolution"}:
        semantic_relation = semantic_relation or ("resolution" if operation_text in {"resolve", "resolution"} else operation_text)
        operation = "set"
    elif operation_text in {"set", "correction", "supersede", "contradiction", "duplicate"}:
        operation = operation_text
    else:
        operation = "set"
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
    for key in ("valid_from", "valid_to", "effective_at", "observed_at"):
        if key in item and key not in temporal:
            temporal[key] = item[key]
    event_context = event or {}
    timezone_name, zone = resolve_timezone(event_context.get("timezone"))
    captured = parse_datetime(event_context.get("captured_at"), zone=zone)
    if captured is None:
        captured = (now or datetime.now(timezone.utc)).astimezone(zone)
    normalized_temporal = normalize_temporal(temporal, captured_at=captured, zone=zone)
    if not normalized_temporal and concept_key in {
        "appointment",
        "meeting",
        "event",
        "deadline",
        "date",
        "time",
    } and has_value:
        # A compact provider may put a temporal expression in ``value``. The
        # semantic provider still owns understanding it; this boundary only
        # applies deterministic normalization once the concept is temporal.
        normalized_temporal = normalize_temporal(item.get("value"), captured_at=captured, zone=zone)
    negated = bool(item.get("negated", False))
    polarity = item.get("polarity")
    if isinstance(polarity, str) and _temporal_fold(polarity) in {"negative", "negated", "not", "false"}:
        negated = True
    confidence = item.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        confidence = None
    attribution = item.get("attribution")
    if attribution is None:
        attribution = item.get("reported_by", item.get("claimed_by", item.get("speaker")))
    attribution = _safe_json_value(attribution)
    metadata: dict[str, Any] = {}
    if attribution is not None:
        metadata["attribution"] = attribution
    if claim_type is not None:
        metadata["claim_type"] = _safe_json_value(claim_type)
    if certainty is not None:
        metadata["certainty"] = _safe_json_value(certainty)
    if confidence is not None:
        metadata["confidence"] = confidence
    if negated:
        metadata["negated"] = True
    if semantic_relation is not None:
        metadata["semantic_relation"] = _safe_json_value(semantic_relation)
    for key in ("actionable", "historical", "lifecycle_key"):
        if key in item:
            metadata[key] = _safe_json_value(item[key])
    result: dict[str, Any] = {
        "source_event_id": source_event_id,
        "entity_key": entity[0],
        "entity_label": entity[1],
        "concept": concept_key,
        "knowledge_status": status,
        "operation": operation,
        "source_refs": source_refs,
        "temporal": normalized_temporal,
        "metadata": metadata,
    }
    if status == "unknown":
        result["unknown_reason"] = _clean_text(item.get("unknown_reason"), limit=300) or "not_stated"
    else:
        result["value"] = _safe_json_value(item.get("value"))
    if supersedes is not None:
        result["supersedes_event_id"] = supersedes
    if attribution is not None:
        result["attribution"] = attribution
    if confidence is not None:
        result["confidence"] = confidence
    if claim_type is not None:
        result["claim_type"] = _safe_json_value(claim_type)
    if negated:
        result["negated"] = True
    if semantic_relation is not None:
        result["semantic_relation"] = _safe_json_value(semantic_relation)
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
    certainty = item.get("certainty", item.get("epistemic_status"))
    claim_type = item.get("claim_type", item.get("claim_kind"))
    if status.casefold() == "known" and (
        _temporal_fold(certainty) in {"uncertain", "possible", "probable", "speculative", "unconfirmed", "maybe"}
        or _temporal_fold(claim_type) in {"hypothesis", "speculation", "possible_diagnosis", "reported_speculation"}
    ):
        status = "inferred"
    source_refs_value = item.get("source_refs", [source_event_id])
    refs = {
        ref
        for ref in source_refs_value
        if isinstance(ref, str) and ref in available_ids
    } if isinstance(source_refs_value, list) else set()
    refs.add(source_event_id)
    attribution = item.get("attribution", item.get("reported_by", item.get("speaker")))
    confidence = item.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        confidence = None
    metadata: dict[str, Any] = {}
    if attribution is not None:
        metadata["attribution"] = _safe_json_value(attribution)
    if confidence is not None:
        metadata["confidence"] = confidence
    if "negated" in item:
        metadata["negated"] = bool(item.get("negated"))
    for key in ("semantic_relation", "claim_type", "certainty"):
        if key in item:
            metadata[key] = _safe_json_value(item[key])
    return {
        "source_event_id": source_event_id,
        "source_entity_key": _slug(source_entity) if isinstance(source_entity, str) and source_entity else None,
        "relation_type": _slug(relation_type),
        "target_entity_key": _slug(target_entity) if isinstance(target_entity, str) and target_entity else None,
        "target_event_id": target_event_id,
        "knowledge_status": status.casefold(),
        "value": _safe_json_value(item.get("value")),
        "source_refs": sorted(refs),
        "metadata": metadata,
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
    if item.get("actionable") is False:
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
    for key in (
        "lifecycle_key",
        "lifecycle_action",
        "supersedes_event_id",
        "related_event_id",
        "entity_key",
        "semantic_relation",
        "time_precision",
        "actionable",
    ):
        if key in item and key not in detail:
            detail[key] = _safe_json_value(item[key])
    lifecycle_action = _temporal_fold(detail.get("lifecycle_action"))
    if lifecycle_action in {"cancel", "cancelled", "canceled", "void"}:
        item_status = "cancelled"
    elif lifecycle_action in {"complete", "completed", "done", "finished"}:
        item_status = "completed"
    else:
        item_status = item.get("status")
    if raw_due is not None and due_at is None:
        coarse = normalize_temporal(raw_due, captured_at=captured, zone=zone)
        if coarse:
            detail["due_temporal"] = coarse
            detail["time_expression"] = _safe_json_value(raw_due)
            detail["time_status"] = "coarse_or_ambiguous"
        else:
            knowledge_status = "unknown"
            detail["time_expression"] = _safe_json_value(raw_due)
            detail["time_status"] = "unreadable_or_ambiguous"
    if raw_starts is not None and starts_at is None:
        coarse = normalize_temporal(raw_starts, captured_at=captured, zone=zone)
        if coarse:
            detail["starts_temporal"] = coarse
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
        "status": _attention_status(item_status),
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
    events_by_id = {
        str(event["event_id"]): event
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
        for normalized in [
            normalize_fact(
                item,
                batch_ids=batch_ids,
                available_ids=available_ids,
                event=events_by_id.get(str(item.get("event_id", item.get("source_event_id"))))
                if isinstance(item, dict)
                else None,
                now=now,
            )
        ]
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
                "actionable": fact.get("metadata", {}).get("actionable", True),
                "details": {
                    "lifecycle_key": fact.get("metadata", {}).get(
                        "lifecycle_key", f"{fact['entity_key']}:{fact['concept']}"
                    ),
                    "entity_key": fact["entity_key"],
                    "semantic_relation": fact.get("semantic_relation"),
                },
            }
            if isinstance(fact.get("value"), str):
                item["title"] = fact["value"]
            elif isinstance(fact.get("value"), dict):
                item.update(fact["value"])
            temporal = fact.get("temporal")
            if isinstance(temporal, dict):
                normalized_point = temporal.get("normalized")
                if normalized_point is not None and "due_at" not in item and "starts_at" not in item:
                    item["starts_at"] = normalized_point
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


def _redact_provider_text(value: str) -> str:
    value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value)
    value = re.sub(
        r'(?i)(["\']?\b(?:api[_-]?key|access[_-]?token|auth(?:orization)?|cookie|credential|password|secret|token)["\']?\s*:\s*)["\'][^"\']*["\']',
        r'\1"[REDACTED]"',
        value,
    )
    value = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", value)
    return value


def _diagnostic_key_is_secret(value: Any) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")
    return normalized in {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "auth_cookie",
        "credential",
        "credentials",
        "cookie",
        "password",
        "secret",
        "token",
    } or any(marker in normalized for marker in ("token", "secret", "password", "credential", "cookie"))


def _sanitize_diagnostic_value(value: Any, *, depth: int = 0) -> Any:
    """Bound and redact JSON values copied from provider diagnostics."""

    if depth > 5:
        return "[TRUNCATED]"
    if isinstance(value, str):
        return _redact_provider_text(value)[:500]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return [_sanitize_diagnostic_value(item, depth=depth + 1) for item in value[:20]]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:30]:
            safe_key = _redact_provider_text(str(key))[:120]
            result[safe_key] = (
                "[REDACTED]"
                if _diagnostic_key_is_secret(key)
                else _sanitize_diagnostic_value(item, depth=depth + 1)
            )
        return result
    return _redact_provider_text(str(value))[:500]


def _sanitize_provider_output(value: Any) -> str | None:
    """Keep only bounded diagnostic lines and redact credential-shaped values."""

    text = _decode_process_output(value)
    lines: list[str] = []
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate or not _DIAGNOSTIC_LINE.search(candidate):
            continue
        candidate = _redact_provider_text(candidate)
        lines.append(candidate[:500])
        if sum(len(item) for item in lines) >= 1000:
            break
    result = "\n".join(lines)[:1000]
    return result or None


def _sanitize_provider_tail(value: Any) -> str | None:
    """Retain a short, redacted tail even when lines have no diagnostic keyword."""

    text = _decode_process_output(value)
    lines = [_redact_provider_text(line.strip())[:500] for line in text.splitlines() if line.strip()]
    result = "\n".join(lines)[-1000:]
    return result or None


def _jsonl_objects(value: Any) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for line in _decode_process_output(value).splitlines():
        candidate = line.strip()
        if not candidate.startswith("{"):
            continue
        try:
            parsed = json.loads(candidate)
        except (TypeError, ValueError):
            continue
        if isinstance(parsed, dict):
            objects.append(parsed)
    return objects


def _terminal_json_event(value: Any) -> dict[str, Any] | None:
    """Return the last machine-readable failure event from Codex JSONL output."""

    events = _jsonl_objects(value)
    candidates = [
        event
        for event in reversed(events)
        if event.get("type") == "turn.failed"
    ]
    candidates.extend(
        event
        for event in reversed(events)
        if event.get("type") == "error"
    )
    candidates.extend(
        event
        for event in reversed(events)
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "error"
    )
    for event in candidates:
        sanitized = _sanitize_diagnostic_value(event)
        if not isinstance(sanitized, dict):
            continue
        raw_error = event.get("error")
        if isinstance(raw_error, dict) and isinstance(raw_error.get("message"), str):
            embedded = _parse_model_json(raw_error["message"])
            if isinstance(embedded, dict):
                sanitized["parsed_error"] = _sanitize_diagnostic_value(embedded)
        elif isinstance(event.get("message"), str):
            embedded = _parse_model_json(event["message"])
            if isinstance(embedded, dict):
                sanitized["parsed_error"] = _sanitize_diagnostic_value(embedded)
        return sanitized
    return None


def _terminal_error_detail(event: dict[str, Any] | None) -> str | None:
    """Extract a short human-readable detail from a terminal JSON event."""

    if not isinstance(event, dict):
        return None
    current: Any = event.get("parsed_error") or event.get("error") or event.get("message")
    status: Any = event.get("status")
    for _ in range(4):
        if isinstance(current, dict) and isinstance(current.get("error"), dict):
            status = current.get("status", status)
            current = current["error"]
            continue
        if isinstance(current, dict) and isinstance(current.get("message"), str):
            embedded = _parse_model_json(current["message"])
            if isinstance(embedded, dict):
                status = current.get("status", status)
                current = embedded
                continue
        break
    if isinstance(current, dict):
        parts = [
            event.get("type"),
            current.get("type"),
            current.get("code"),
            current.get("message"),
        ]
        detail = ": ".join(str(part) for part in parts if isinstance(part, str) and part.strip())
        if status is not None:
            detail = f"{detail} (status {status})" if detail else f"status {status}"
    elif isinstance(current, str):
        detail = current
    else:
        detail = None
    return _redact_provider_text(detail)[:1000] if detail else None


def _nullable_string_schema() -> dict[str, Any]:
    return {"anyOf": [{"type": "string"}, {"type": "null"}]}


def _nullable_number_schema() -> dict[str, Any]:
    return {"anyOf": [{"type": "number"}, {"type": "null"}]}


def _nullable_boolean_schema() -> dict[str, Any]:
    return {"anyOf": [{"type": "boolean"}, {"type": "null"}]}


def _attribution_schema() -> dict[str, Any]:
    attribution_properties = {
        "name": _nullable_string_schema(),
        "role": _nullable_string_schema(),
        "organization": _nullable_string_schema(),
        "relationship": _nullable_string_schema(),
    }
    return {
        "anyOf": [
            {"type": "string"},
            {"type": "null"},
            {
                "type": "object",
                "additionalProperties": False,
                "properties": attribution_properties,
                "required": list(attribution_properties),
            },
        ]
    }


def _temporal_semantics_schema() -> dict[str, Any]:
    properties = {
        "valid_from": _nullable_string_schema(),
        "valid_to": _nullable_string_schema(),
        "effective_at": _nullable_string_schema(),
        "observed_at": _nullable_string_schema(),
        "normalized": _nullable_string_schema(),
        "interval_start": _nullable_string_schema(),
        "interval_end": _nullable_string_schema(),
        "date": _nullable_string_schema(),
        "expression": _value_schema() if "_value_schema" in globals() else _nullable_string_schema(),
        "precision": _nullable_string_schema(),
        "weekday_index": _nullable_number_schema(),
        "weekday": _nullable_string_schema(),
        "local_time": _nullable_string_schema(),
        "timezone": _nullable_string_schema(),
        "next": _nullable_boolean_schema(),
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def _value_schema() -> dict[str, Any]:
    value_object_properties = {
        "amount": {"anyOf": [{"type": "number"}, {"type": "string"}, {"type": "null"}]},
        "currency": _nullable_string_schema(),
        "billing_period": _nullable_string_schema(),
        "title": _nullable_string_schema(),
        "text": _nullable_string_schema(),
        "task": _nullable_string_schema(),
        "due_at": _nullable_string_schema(),
        "deadline": _nullable_string_schema(),
        "starts_at": _nullable_string_schema(),
        "start_at": _nullable_string_schema(),
        "iso": _nullable_string_schema(),
        "datetime": _nullable_string_schema(),
        "timestamp": _nullable_string_schema(),
        "date": _nullable_string_schema(),
        "relative_minutes": _nullable_number_schema(),
        "relative_hours": _nullable_number_schema(),
        "relative_seconds": _nullable_number_schema(),
        "value": _nullable_string_schema(),
    }
    return {
        "anyOf": [
            {"type": "string"},
            {"type": "number"},
            {"type": "boolean"},
            {"type": "null"},
            {
                "type": "object",
                "additionalProperties": False,
                "properties": value_object_properties,
                "required": list(value_object_properties),
            },
            {
                "type": "array",
                "items": {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "boolean"}, {"type": "null"}]},
            },
        ]
    }


def _timestamp_schema() -> dict[str, Any]:
    properties = {
        "relative_seconds": _nullable_number_schema(),
        "relative_minutes": _nullable_number_schema(),
        "relative_hours": _nullable_number_schema(),
        "iso": _nullable_string_schema(),
        "datetime": _nullable_string_schema(),
        "timestamp": _nullable_string_schema(),
        "date": _nullable_string_schema(),
        "value": _nullable_string_schema(),
        "weekday_index": _nullable_number_schema(),
        "weekday": _nullable_string_schema(),
        "local_time": _nullable_string_schema(),
        "next": _nullable_boolean_schema(),
        "expression": _value_schema(),
    }
    return {
        "anyOf": [
            {"type": "string"},
            {"type": "null"},
            {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
                "required": list(properties),
            },
        ]
    }


def _semantic_output_schema() -> dict[str, Any]:
    entity = {
        "anyOf": [
            {"type": "string"},
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "key": _nullable_string_schema(),
                    "name": _nullable_string_schema(),
                    "label": _nullable_string_schema(),
                },
                "required": ["key", "name", "label"],
            },
        ]
    }
    fact_properties = {
        "event_id": {"type": "string"},
        "entity": entity,
        "concept": {"type": "string"},
        "knowledge_status": {"type": "string", "enum": ["known", "inferred", "unknown"]},
        "value": _value_schema(),
        "unknown_reason": _nullable_string_schema(),
        "operation": {"type": "string", "enum": ["set", "correction", "supersede", "contradiction", "duplicate"]},
        "supersedes_event_id": _nullable_string_schema(),
        "attribution": _attribution_schema(),
        "claim_type": _nullable_string_schema(),
        "certainty": _nullable_string_schema(),
        "confidence": _nullable_number_schema(),
        "negated": {"type": "boolean"},
        "semantic_relation": _nullable_string_schema(),
        "source_refs": {"type": "array", "items": {"type": "string"}},
        "temporal": _temporal_semantics_schema(),
    }
    relation_properties = {
        "source_event_id": {"type": "string"},
        "event_id": _nullable_string_schema(),
        "relation_type": {"type": "string"},
        "type": _nullable_string_schema(),
        "source_entity_key": _nullable_string_schema(),
        "target_entity_key": _nullable_string_schema(),
        "subject": _nullable_string_schema(),
        "target": _nullable_string_schema(),
        "reference": _nullable_string_schema(),
        "target_event_id": _nullable_string_schema(),
        "knowledge_status": {"type": "string", "enum": ["known", "inferred", "unknown"]},
        "value": _value_schema(),
        "attribution": _attribution_schema(),
        "claim_type": _nullable_string_schema(),
        "certainty": _nullable_string_schema(),
        "confidence": _nullable_number_schema(),
        "negated": {"type": "boolean"},
        "semantic_relation": _nullable_string_schema(),
        "source_refs": {"type": "array", "items": {"type": "string"}},
    }
    attention_properties = {
        "event_id": {"type": "string"},
        "source_event_id": _nullable_string_schema(),
        "title": {"type": "string"},
        "text": _nullable_string_schema(),
        "task": _nullable_string_schema(),
        "label": _nullable_string_schema(),
        "kind": {"type": "string"},
        "type": _nullable_string_schema(),
        "status": {"type": "string"},
        "knowledge_status": {"type": "string", "enum": ["known", "inferred", "unknown"]},
        "due_at": _timestamp_schema(),
        "deadline": _timestamp_schema(),
        "starts_at": _timestamp_schema(),
        "start_at": _timestamp_schema(),
        "relative_minutes": _nullable_number_schema(),
        "relative_hours": _nullable_number_schema(),
        "relative_seconds": _nullable_number_schema(),
        "value": _value_schema(),
        "actionable": _nullable_boolean_schema(),
        "details": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "note": _nullable_string_schema(),
                "time_expression": _value_schema(),
                "time_status": _nullable_string_schema(),
                "time_precision": _nullable_string_schema(),
                "due_temporal": _temporal_semantics_schema(),
                "starts_temporal": _temporal_semantics_schema(),
                "lifecycle_key": _nullable_string_schema(),
                "lifecycle_action": _nullable_string_schema(),
                "supersedes_event_id": _nullable_string_schema(),
                "related_event_id": _nullable_string_schema(),
                "entity_key": _nullable_string_schema(),
                "semantic_relation": _nullable_string_schema(),
                "actionable": _nullable_boolean_schema(),
            },
            "required": [
                "note",
                "time_expression",
                "time_status",
                "time_precision",
                "due_temporal",
                "starts_temporal",
                "lifecycle_key",
                "lifecycle_action",
                "supersedes_event_id",
                "related_event_id",
                "entity_key",
                "semantic_relation",
                "actionable",
            ],
        },
        "source_refs": {"type": "array", "items": {"type": "string"}},
    }
    attachment_properties = {
        "event_id": _nullable_string_schema(),
        "sha256": _nullable_string_schema(),
        "status": {"type": "string", "enum": ["read", "unsupported", "unreadable"]},
        "source_refs": {"type": "array", "items": {"type": "string"}},
    }

    def strict_items(properties: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": list(properties),
        }

    fact_items = strict_items(fact_properties)
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "facts": {"type": "array", "items": fact_items},
            "observations": {"type": "array", "items": fact_items},
            "relationships": {"type": "array", "items": strict_items(relation_properties)},
            "attention": {"type": "array", "items": strict_items(attention_properties)},
            "attachment_results": {"type": "array", "items": strict_items(attachment_properties)},
            "answer": _nullable_string_schema(),
            "source_refs": {"type": "array", "items": {"type": "string"}},
            "evidence_ids": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": MAX_ASK_SUPPORTING_EVIDENCE_IDS,
            },
        },
        "required": [
            "facts",
            "observations",
            "relationships",
            "attention",
            "attachment_results",
            "answer",
            "source_refs",
            "evidence_ids",
        ],
    }


def product_database_path(home: str | Path) -> Path:
    """Return the single authoritative Product V2 database for one Home."""

    return Path(home).expanduser().resolve() / PRODUCT_DATABASE_NAME


class ProductCodexProvider:
    """Bounded, ephemeral Codex CLI adapter for Product V2.

    The installed CLI surface observed for this runtime is ``codex exec`` with
    ``--image`` for direct image inputs.  Each call uses an ephemeral session,
    a read-only sandbox, the CLI's default approval mode, an isolated temporary
    workspace, and an additional Home directory for stored attachments.
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
        path.write_text(json.dumps(_semantic_output_schema(), ensure_ascii=False), encoding="utf-8")
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
                "cwd": str(Path.cwd()),
                "agent_cwd": str(workspace),
                "stdin_behavior": "UTF-8 prompt bytes via a subprocess pipe; argv '-' selects stdin",
                "environment": {"inherit": True, "modifications": []},
                "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "sandbox": "read-only",
                "approval_mode": "CLI default; no explicit approval flag",
                "config_overrides": [f"model_reasoning_effort={self.reasoning_effort}"],
                "feature_flags": {"shell_snapshot": "default-enabled; not explicitly disabled"},
                "output_mode": {
                    "stdout": "JSONL (--json)",
                    "last_message_file": "<temporary-output>",
                    "output_schema": "<temporary-schema>",
                },
                "timeout_seconds": self.timeout,
                "invocation": self._invocation_summary(len(image_paths or [])),
                "image_count": len(image_paths or []),
                "returncode": None,
                "timed_out": False,
                "terminal_event": None,
                "stdout_tail": None,
                "stderr_tail": None,
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
                        "stdout_tail": _sanitize_provider_output(getattr(error, "stdout", None)),
                        "stderr_tail": _sanitize_provider_tail(getattr(error, "stderr", None)),
                        "terminal_event": _terminal_json_event(getattr(error, "stdout", None)),
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
                        "stderr_tail": _sanitize_provider_tail(str(error)),
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
                    "stdout_tail": _sanitize_provider_output(stdout),
                    "stderr_tail": _sanitize_provider_tail(stderr),
                    "terminal_event": _terminal_json_event(stdout),
                }
            )
            if completed.returncode != 0:
                detail = (
                    _terminal_error_detail(self.last_call.get("terminal_event"))
                    or self.last_call.get("stderr_tail")
                    or self.last_call.get("stderr")
                    or self.last_call.get("stdout_tail")
                    or f"exit code {completed.returncode}"
                )
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
            "Respond in the same language as the current question unless the question explicitly "
            "requests another language. Mixed-language questions should be answered in the language "
            "of the request's main conversational wording. Keep proper names, numbers, currencies, "
            "dates, times, units, and filenames unchanged where appropriate. Do not translate an "
            "evidence string and present it as if it were the original capture. Every candidate item "
            "has an `evidence_id`; return those IDs in `evidence_ids` for the facts, history, "
            "relationships, attention items, or source metadata actually used to support the rendered "
            "answer. Validate your selection against the supplied IDs and never invent one. Return "
            "only the smallest materially supporting set, including multiple IDs when the answer "
            "reports a correction, historical value, conflict, or uncertainty. Never cite every "
            "candidate merely because it was supplied. The runtime ignores top-level `source_refs` "
            "for answer provenance, so return `source_refs: []` here. If the context is insufficient, "
            "say so explicitly and select only evidence that supports that limitation."
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
            "fact_history": snapshot.get("fact_history", [])[-MAX_ASK_CONTEXT_HISTORY:],
            "relationships": snapshot.get("relationships", [])[-MAX_ASK_CONTEXT_HISTORY:],
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

    def _retrieval_context(
        self,
        question: str,
        plan: AskPlan | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
        """Return only state that is relevant to one inspected Ask plan.

        The provider receives this bounded context, never the raw capture
        history. Current facts remain the primary retrieval surface; history
        and relations are added only when they match the query or the plan
        explicitly asks about change. A difficult or unrecognized-language
        query receives a separately bounded structured candidate set.
        """

        plan = plan or plan_ask(question)
        snapshot = self.store.snapshot(now=self._now())
        query_terms = set(plan.query_terms)
        topic_terms = set(plan.topic_terms)

        def ranked(
            collection: Any,
            keys: tuple[str, ...],
            *,
            limit: int,
            expand_entities: bool = False,
        ) -> list[dict[str, Any]]:
            if not isinstance(collection, list) or not query_terms:
                return []
            scored: list[tuple[int, int, str, str, dict[str, Any]]] = []
            for item in collection:
                if not isinstance(item, dict) or item.get("retracted"):
                    continue
                searchable = search_terms(_searchable_text(item, keys))
                overlap = query_terms & searchable
                if not overlap:
                    continue
                topic_overlap = overlap & topic_terms
                score = len(overlap) + (2 * len(topic_overlap))
                scored.append(
                    (
                        score,
                        int(item.get("sequence", item.get("latest_sequence", 0)) or 0),
                        str(item.get("entity_key", item.get("source_entity_key", ""))),
                        str(item.get("concept", item.get("relation_type", ""))),
                        item,
                    )
                )
            scored.sort(key=lambda row: (-row[0], -row[1], row[2], row[3]))
            if scored:
                qualified = scored
                if plan.intent == "generic" and len(topic_terms) >= 2:
                    # Multiple content terms normally describe one requested
                    # object.  Requiring two matching terms prevents a generic
                    # multi-term object query from falling back to a merely
                    # related object. Keep the full scored set for entity
                    # expansion, so a second fact about the winning entity can
                    # still be returned even if it only matches the entity.
                    qualified = [
                        row
                        for row in scored
                        if len(query_terms & search_terms(_searchable_text(row[4], keys)) & topic_terms) >= 2
                    ]
                if not qualified and plan.lexical_gap:
                    # Cross-language questions often preserve one canonical
                    # semantic key term while the other surface words are
                    # inflected or untranslated. If the strongest overlap
                    # identifies exactly one entity, retain that winner. A
                    # tied result still stays ambiguous rather than leaking
                    # an unrelated fact.
                    best_score = scored[0][0]
                    best_entities = {row[2] for row in scored if row[0] == best_score}
                    if len(best_entities) != 1:
                        return []
                    qualified = [row for row in scored if row[2] in best_entities]
                if not qualified:
                    return []
                best_score = qualified[0][0]
                leaders = [row for row in qualified if row[0] == best_score]
                if expand_entities:
                    # A question can ask for several properties of one
                    # entity (for example a gift and a dietary constraint).
                    # Retrieve the entity's other current facts without
                    # broadening to unrelated entities.
                    leader_entities = {row[2] for row in leaders}
                    scored = [row for row in scored if row[2] in leader_entities]
                else:
                    # Keep tied best candidates for honest ambiguity handling,
                    # but do not leak a weaker accidental overlap into the
                    # answer.
                    scored = leaders
            return [item for _score, _sequence, _entity, _concept, item in scored[:limit]]

        facts = [item for item in snapshot.get("current_facts", []) if isinstance(item, dict)]
        if plan.broad:
            selected_facts = facts[:MAX_ASK_CONTEXT_FACTS]
        elif plan.intent == "generic" and query_terms == {"location"}:
            # A plural location request is a field-oriented list query.  Some
            # provider facts expose the location as a concept; others retain
            # a useful observation sentence, so accept either representation.
            def location_like(item: dict[str, Any]) -> bool:
                concept_terms = search_terms(str(item.get("concept", "")))
                if concept_terms & {"location", "entrance", "address", "place"}:
                    return True
                value = _searchable_text(item, ("entity_label", "value", "unknown_reason"))
                return bool(re.search(r"\b(?:in|at|inside|near|by|on|under|from)\b", value, flags=re.IGNORECASE))

            selected_facts = [item for item in facts if location_like(item)][:MAX_ASK_CONTEXT_FACTS]
        else:
            selected_facts = ranked(
                facts,
                (
                    "entity_key",
                    "entity_label",
                    "concept",
                    "value",
                    "unknown_reason",
                    "operation",
                    "metadata",
                    "semantic_metadata",
                    "temporal",
                    "conflicting_values",
                    "uncertainty",
                    "attribution",
                    "negated",
                ),
                limit=MAX_ASK_CONTEXT_FACTS,
                expand_entities=plan.intent == "generic",
            )
        if plan.intent == "costs" and not topic_terms:
            selected_facts = [item for item in facts if _is_cost_fact(item)][:MAX_ASK_CONTEXT_FACTS]

        history = [item for item in snapshot.get("fact_history", []) if isinstance(item, dict)]
        selected_history = ranked(
            history,
            (
                "entity_key",
                "entity_label",
                "concept",
                "value",
                "unknown_reason",
                "operation",
                "supersedes_event_id",
                "semantic_metadata",
                "temporal",
                "attribution",
                "negated",
            ),
            limit=MAX_ASK_CONTEXT_HISTORY,
            expand_entities=plan.intent == "generic",
        )

        def append_unique(target: list[dict[str, Any]], items: Iterable[dict[str, Any]]) -> None:
            seen = {
                (
                    item.get("fact_id"),
                    item.get("relation_id"),
                    item.get("source_event_id"),
                    item.get("operation"),
                    canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                )
                for item in target
            }
            for item in items:
                identity = (
                    item.get("fact_id"),
                    item.get("relation_id"),
                    item.get("source_event_id"),
                    item.get("operation"),
                    canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                )
                if identity in seen:
                    continue
                target.append(item)
                seen.add(identity)
                if len(target) >= MAX_ASK_CONTEXT_HISTORY:
                    break

        selected_keys = {
            (item.get("entity_key"), item.get("concept"))
            for item in selected_facts
            if item.get("entity_key") is not None and item.get("concept") is not None
        }
        if plan.history_requested or plan.intent in {"changes", "costs"}:
            changed_keys = {
                (item.get("entity_key"), item.get("concept"))
                for item in history
                if item.get("operation") in {"correction", "supersede", "contradiction"}
                and item.get("entity_key") is not None
                and item.get("concept") is not None
            }
            related_history = [
                item
                for item in history
                if not item.get("retracted")
                and (
                    (
                        (item.get("entity_key"), item.get("concept")) in selected_keys
                        and (plan.intent != "changes" or bool(topic_terms))
                    )
                    or (
                        plan.intent == "changes"
                        and not topic_terms
                        and (item.get("entity_key"), item.get("concept")) in changed_keys
                    )
                    or (
                        plan.intent == "costs"
                        and not topic_terms
                        and _is_cost_fact(item)
                    )
                )
            ]
            related_history.sort(key=lambda item: int(item.get("sequence", 0)))
            append_unique(selected_history, related_history)

        relations = [item for item in snapshot.get("relationships", []) if isinstance(item, dict)]
        selected_relations = ranked(
            relations,
            ("source_entity_key", "relation_type", "target_entity_key", "value", "source_event_id", "target_event_id"),
            limit=MAX_ASK_CONTEXT_HISTORY,
        )
        if plan.intent == "changes":
            change_relations = [
                item
                for item in relations
                if not item.get("retracted")
                and item.get("relation_type") in {"meaningful_change", "correction", "supersession"}
                and (
                    not topic_terms
                    or topic_terms
                    & search_terms(
                        _searchable_text(
                            item,
                            ("source_entity_key", "relation_type", "target_entity_key", "value"),
                        )
                    )
                )
            ]
            append_unique(selected_relations, change_relations)

        attention = [item for item in snapshot.get("attention", []) if isinstance(item, dict)]
        open_attention = [item for item in attention if item.get("status") == "open"]
        if plan.intent == "attention":
            if topic_terms:
                selected_attention = ranked(
                    open_attention,
                    ("title", "kind", "details", "due_at", "starts_at"),
                    limit=MAX_ASK_CONTEXT_HISTORY,
                )
            else:
                selected_attention = open_attention[:MAX_ASK_CONTEXT_HISTORY]
        else:
            selected_attention = ranked(
                attention,
                ("title", "kind", "details", "due_at", "starts_at"),
                limit=MAX_ASK_CONTEXT_HISTORY,
            )

        def newest(items: Iterable[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
            candidates = [item for item in items if isinstance(item, dict) and not item.get("retracted")]
            candidates.sort(
                key=lambda item: int(item.get("latest_sequence", item.get("sequence", 0)) or 0),
                reverse=True,
            )
            return candidates[:limit]

        def merge_bounded(
            preferred: Iterable[dict[str, Any]],
            fallback: Iterable[dict[str, Any]],
            limit: int,
        ) -> list[dict[str, Any]]:
            result: list[dict[str, Any]] = []
            seen: set[tuple[Any, ...]] = set()
            for item in [*preferred, *fallback]:
                if not isinstance(item, dict) or item.get("retracted"):
                    continue
                identity = (
                    item.get("fact_id"),
                    item.get("relation_id"),
                    item.get("source_event_id"),
                    item.get("fingerprint"),
                    item.get("operation"),
                    canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                )
                if identity in seen:
                    continue
                result.append(item)
                seen.add(identity)
                if len(result) >= limit:
                    break
            return result

        # An unknown or mixed-language question cannot safely be reduced by
        # the optional lexical fast path. Give the general semantic provider
        # a bounded candidate set of structured state instead of returning
        # ``no_match`` merely because the query and source use different
        # surface languages. This never includes raw capture text or the
        # complete unbounded history.
        fallback_facts: list[dict[str, Any]] = []
        fallback_history: list[dict[str, Any]] = []
        fallback_relations: list[dict[str, Any]] = []
        fallback_attention: list[dict[str, Any]] = []
        provider_facts = selected_facts
        provider_history = selected_history
        provider_relations = selected_relations
        provider_attention = selected_attention
        if plan.semantic_fallback:
            fallback_facts = merge_bounded(
                selected_facts,
                newest(facts, MAX_ASK_FALLBACK_FACTS),
                MAX_ASK_FALLBACK_FACTS,
            )
            fallback_history = merge_bounded(
                selected_history,
                newest(history, MAX_ASK_FALLBACK_HISTORY),
                MAX_ASK_FALLBACK_HISTORY,
            )
            fallback_relations = merge_bounded(
                selected_relations,
                newest(relations, MAX_ASK_FALLBACK_HISTORY),
                MAX_ASK_FALLBACK_HISTORY,
            )
            fallback_attention = merge_bounded(
                selected_attention,
                newest(attention, MAX_ASK_FALLBACK_HISTORY),
                MAX_ASK_FALLBACK_HISTORY,
            )
            provider_facts = fallback_facts
            provider_history = fallback_history
            provider_relations = fallback_relations
            provider_attention = fallback_attention

        # Candidate IDs are provider-facing only. They let synthesis select a
        # structured item without allowing a source-reference list to stand in
        # for that selection.
        provider_facts = self._tag_candidates("facts", provider_facts)
        provider_history = self._tag_candidates("history", provider_history)
        provider_relations = self._tag_candidates("relationships", provider_relations)
        provider_attention = self._tag_candidates("attention", provider_attention)
        fallback_facts = self._tag_candidates("facts", fallback_facts)
        fallback_history = self._tag_candidates("history", fallback_history)
        fallback_relations = self._tag_candidates("relationships", fallback_relations)
        fallback_attention = self._tag_candidates("attention", fallback_attention)

        selected_items = [*provider_facts, *provider_history, *provider_relations, *provider_attention]
        reference_ids = self._source_refs(selected_items)
        source_limit = (
            MAX_ASK_FALLBACK_FACTS + MAX_ASK_FALLBACK_HISTORY
            if plan.semantic_fallback
            else MAX_ASK_CONTEXT_HISTORY
        )
        selected_sources = [
            item
            for item in snapshot.get("sources", [])
            if isinstance(item, dict)
            and item.get("event_id") in reference_ids
            and not item.get("retracted")
        ][:source_limit]
        selected_sources = self._tag_candidates("sources", selected_sources)
        context = {
            "facts": provider_facts,
            "history": provider_history[:MAX_ASK_CONTEXT_HISTORY],
            "attention": provider_attention,
            "relationships": provider_relations[:MAX_ASK_CONTEXT_HISTORY],
            "sources": selected_sources,
            "plan": plan.as_dict(),
            "response_language": plan.language if plan.language in {"en", "pl"} else "same_as_question",
        }
        if plan.language == "unknown":
            context["candidate_facts"] = fallback_facts
            context["candidate_history"] = fallback_history
            context["candidate_relationships"] = fallback_relations
            context["candidate_attention"] = fallback_attention
        return context, selected_facts, " ".join(sorted(query_terms))

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
        refs: set[str] = set()
        for item in items:
            refs.update(
                ref
                for ref in item.get("source_refs", [])
                if isinstance(ref, str) and ref
            )
            for key in ("event_id", "source_event_id"):
                reference = item.get(key)
                if isinstance(reference, str) and reference:
                    refs.add(reference)
        return sorted(refs)

    @staticmethod
    def _candidate_evidence_id(collection: str, item: dict[str, Any]) -> str:
        """Return a stable, typed ID for one bounded Ask candidate.

        These IDs are an internal bridge between provider selection and source
        provenance. They deliberately identify the retrieved structured item,
        not an arbitrary provider-supplied source reference.
        """

        if collection == "facts":
            entity_key = _clean_text(item.get("entity_key"), limit=160)
            concept = _clean_text(item.get("concept"), limit=160)
            if entity_key and concept:
                return f"current_fact:{_slug(entity_key)}:{_slug(concept)}"
        elif collection == "history":
            fact_id = item.get("fact_id")
            if isinstance(fact_id, (int, str)) and not isinstance(fact_id, bool) and str(fact_id):
                return f"fact:{fact_id}"
        elif collection == "relationships":
            relation_id = item.get("relation_id")
            if isinstance(relation_id, (int, str)) and not isinstance(relation_id, bool) and str(relation_id):
                return f"relation:{relation_id}"
        elif collection == "attention":
            fingerprint = item.get("fingerprint")
            if isinstance(fingerprint, str) and fingerprint:
                return f"attention:{fingerprint}"
        elif collection == "sources":
            event_id = item.get("event_id")
            if isinstance(event_id, str) and event_id:
                return f"source:{event_id}"
        digest = hashlib.sha256(canonical_json(item).encode("utf-8")).hexdigest()[:24]
        return f"{collection}:{digest}"

    @classmethod
    def _tag_candidates(
        cls,
        collection: str,
        items: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Copy bounded candidates and expose only an internal evidence ID."""

        tagged: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            candidate = copy.deepcopy(item)
            candidate["evidence_id"] = cls._candidate_evidence_id(collection, candidate)
            tagged.append(candidate)
        return tagged

    @staticmethod
    def _evidence_lookup(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Index exactly the candidate objects exposed to the provider."""

        lookup: dict[str, dict[str, Any]] = {}
        for collection in (
            "facts",
            "candidate_facts",
            "history",
            "candidate_history",
            "relationships",
            "candidate_relationships",
            "attention",
            "candidate_attention",
            "sources",
        ):
            values = context.get(collection, [])
            if not isinstance(values, list):
                continue
            for item in values:
                evidence_id = item.get("evidence_id") if isinstance(item, dict) else None
                if isinstance(evidence_id, str) and evidence_id and evidence_id not in lookup:
                    lookup[evidence_id] = item
        return lookup

    @classmethod
    def _validated_supporting_evidence(
        cls,
        context: dict[str, Any],
        evidence_ids: Iterable[Any],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Keep only provider IDs that name an exposed candidate object."""

        lookup = cls._evidence_lookup(context)
        selected_ids: list[str] = []
        selected_items: list[dict[str, Any]] = []
        for evidence_id in evidence_ids:
            if not isinstance(evidence_id, str) or evidence_id not in lookup or evidence_id in selected_ids:
                continue
            selected_ids.append(evidence_id)
            selected_items.append(lookup[evidence_id])
            if len(selected_ids) >= MAX_ASK_SUPPORTING_EVIDENCE_IDS:
                break
        return selected_ids, selected_items

    @staticmethod
    def _public_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove the provider-only candidate ID from returned Ask items."""

        public: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            value = copy.deepcopy(item)
            value.pop("evidence_id", None)
            public.append(value)
        return public

    def _deterministic_answer(
        self,
        question: str,
        snapshot: dict[str, Any],
        context: dict[str, Any],
        selected_facts: list[dict[str, Any]],
        plan: AskPlan | None = None,
    ) -> tuple[str | None, str, list[dict[str, Any]], list[str]]:
        plan = plan or plan_ask(question)

        # Deterministic rendering is an optimization for the languages whose
        # high-confidence fast paths are understood locally. Unknown or
        # mixed-language questions must reach the provider-directed semantic
        # renderer so their answer follows the question language.
        if plan.language not in {"en", "pl"} or (
            plan.intent == "costs" and plan.semantic_fallback
        ):
            return None, "semantic", selected_facts, self._source_refs(
                selected_facts
            )

        if plan.intent == "attention":
            attention = [
                item
                for item in context.get("attention", [])
                if isinstance(item, dict) and item.get("status") == "open"
            ]
            if plan.topic_terms:
                attention = [
                    item
                    for item in attention
                    if plan.topic_terms
                    & search_terms(_searchable_text(item, ("title", "kind", "details", "due_at", "starts_at")))
                ]
            now = self._now()
            if plan.time_window in {"today", "tomorrow", "upcoming"}:
                target_date = now.date()
                if plan.time_window == "tomorrow":
                    target_date += timedelta(days=1)
                horizon = now + timedelta(days=7)
                filtered: list[dict[str, Any]] = []
                for item in attention:
                    due_value = item.get("due_at") or item.get("starts_at")
                    due = parse_datetime(due_value, zone=timezone.utc) if due_value else None
                    if plan.time_window in {"today", "tomorrow"}:
                        if due is None or due.astimezone(now.tzinfo).date() != target_date:
                            continue
                    elif due is not None and due > horizon:
                        continue
                    filtered.append(item)
                attention = filtered
            if not attention:
                return _answer_copy(plan, "attention_no_match"), "no_match", [], []
            labels = [str(item.get("title") or item.get("kind") or "open item") for item in attention[:10]]
            answer = _answer_copy(plan, "open_items") + "; ".join(labels) + "."
            return answer, "attention", attention, self._source_refs(attention)

        if plan.intent == "costs":
            all_costs = [
                item for item in snapshot.get("current_facts", [])
                if isinstance(item, dict) and _is_cost_fact(item)
            ]
            cost_facts = [item for item in selected_facts if _is_cost_fact(item)]
            if not plan.topic_terms:
                cost_facts = all_costs[:MAX_ASK_CONTEXT_FACTS]
            history_costs = [
                item
                for item in context.get("history", [])
                if isinstance(item, dict) and _is_cost_fact(item)
            ]
            selected_keys = {
                (item.get("entity_key"), item.get("concept"))
                for item in cost_facts
            }
            if plan.topic_terms:
                history_costs = [
                    item
                    for item in history_costs
                    if (item.get("entity_key"), item.get("concept")) in selected_keys
                    or plan.topic_terms
                    & search_terms(_searchable_text(item, ("entity_key", "entity_label", "concept", "value")))
            ]
            if not cost_facts and not history_costs:
                return _answer_copy(plan, "cost_no_match"), "no_match", [], []

            descriptions = [_fact_summary(item) for item in cost_facts[:10]]
            items = list(cost_facts[:10])
            if plan.history_requested:
                seen = {
                    (
                        item.get("source_event_id"),
                        item.get("fact_id"),
                        canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                    )
                    for item in items
                }
                for item in sorted(history_costs, key=lambda value: int(value.get("sequence", 0))):
                    identity = (
                        item.get("source_event_id"),
                        item.get("fact_id"),
                        canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                    )
                    if identity not in seen:
                        items.append(item)
                        seen.add(identity)
                history_descriptions = [_fact_summary(item) for item in items[len(cost_facts[:10]) :10]]
            else:
                history_descriptions = []
            answer = _answer_copy(plan, "observed_costs") + "; ".join(descriptions or [_fact_summary(item) for item in items[:10]]) + "."
            if history_descriptions:
                answer += _answer_copy(plan, "recorded_history") + "; ".join(history_descriptions) + "."
            totals = self._money_summary(cost_facts)
            if totals:
                answer += _answer_copy(plan, "deterministic_totals") + f"{totals}."
            return answer, "costs", items[:MAX_ASK_CONTEXT_FACTS], self._source_refs(items)

        if plan.intent == "changes":
            history_markers = {
                "previous",
                "earlier",
                "before",
                "history",
                "historical",
                "poprzedni",
                "poprzednia",
                "wczesniej",
                "historia",
            }
            change_markers = {
                "change",
                "correction",
                "replacement",
                "superseded",
            }
            if plan.history_requested and plan.topic_terms and set(plan.query_terms) & history_markers and not (
                set(plan.query_terms) & change_markers
            ):
                historical = [
                    item
                    for item in context.get("history", [])
                    if isinstance(item, dict)
                    and (item.get("superseded") or item.get("resolved"))
                ]
                if plan.topic_terms:
                    matching_historical = [
                        item
                        for item in historical
                        if plan.topic_terms
                        & search_terms(
                            _searchable_text(
                                item,
                                (
                                    "entity_key",
                                    "entity_label",
                                    "concept",
                                    "value",
                                    "unknown_reason",
                                    "semantic_metadata",
                                    "temporal",
                                ),
                            )
                        )
                    ]
                    if matching_historical:
                        historical = matching_historical
                historical.sort(key=lambda item: int(item.get("sequence", 0) or 0), reverse=True)
                if not historical:
                    return _answer_copy(plan, "changes_no_match"), "no_match", [], []
                return (
                    _answer_copy(plan, "relevant_memory")
                    + "; ".join(_fact_summary(item) for item in historical[:10])
                    + ".",
                    "changes",
                    historical[:MAX_ASK_CONTEXT_HISTORY],
                    self._source_refs(historical),
                )
            changes = [
                item
                for item in context.get("history", [])
                if isinstance(item, dict)
                and item.get("operation") in {"correction", "supersede", "contradiction"}
            ]
            changes.extend(
                item
                for item in context.get("relationships", [])
                if isinstance(item, dict)
                and item.get("relation_type") in {"meaningful_change", "correction", "supersession"}
            )
            if not changes:
                return _answer_copy(plan, "changes_no_match"), "no_match", [], []
            change_keys = {
                (item.get("entity_key"), item.get("concept"))
                for item in changes
                if item.get("entity_key") is not None and item.get("concept") is not None
            }
            expanded_changes: list[dict[str, Any]] = []
            seen_change_items: set[tuple[Any, ...]] = set()
            for item in context.get("history", []):
                if not isinstance(item, dict):
                    continue
                key = (item.get("entity_key"), item.get("concept"))
                if change_keys and key not in change_keys:
                    continue
                identity = (
                    item.get("source_event_id"),
                    item.get("fact_id"),
                    item.get("relation_id"),
                    item.get("operation"),
                    canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                )
                if identity not in seen_change_items:
                    expanded_changes.append(item)
                    seen_change_items.add(identity)
            for item in changes:
                identity = (
                    item.get("source_event_id"),
                    item.get("fact_id"),
                    item.get("relation_id"),
                    item.get("operation", item.get("relation_type")),
                    canonical_json(item.get("value")) if "value" in item else item.get("unknown_reason"),
                )
                if identity not in seen_change_items:
                    expanded_changes.append(item)
                    seen_change_items.add(identity)
            expanded_changes.sort(key=lambda item: int(item.get("sequence", 0)))
            labels = []
            for item in expanded_changes[:10]:
                label = item.get("entity_label", item.get("source_entity_key", "memory"))
                operation = item.get("operation", item.get("relation_type", "change"))
                labels.append(f"{label}: {operation} ({_fact_summary(item)})")
            return _answer_copy(plan, "recent_changes") + "; ".join(labels) + ".", "changes", expanded_changes, self._source_refs(expanded_changes)

        if plan.intent == "last_mention":
            matches = context.get("history", []) or selected_facts
            if matches:
                latest = sorted(matches, key=lambda item: int(item.get("sequence", 0)), reverse=True)[0]
                refs = latest.get("source_refs", [])
                source = next(
                    (item for item in snapshot.get("sources", []) if item.get("event_id") in refs),
                    None,
                )
                when = source.get("captured_at") if source else "an earlier capture"
                label = latest.get("entity_label", latest.get("entity_key", "that topic"))
                return (
                    _answer_copy(plan, "latest_mention")
                    + f"{label}"
                    + _answer_copy(plan, "latest_mention_at")
                    + f"{when}.",
                    "last_mention",
                    [latest],
                    self._source_refs([latest]),
                )
            return _answer_copy(plan, "last_mention_no_match"), "no_match", [], []

        if plan.intent == "generic" and not plan.broad and len(plan.topic_terms) <= 1:
            singular_question = bool(
                re.match(r"^(?:where|who|which|whose|gdzie|kto|ktore|które)\b", question.casefold().strip())
            )
            if singular_question:
                candidates: list[tuple[int, dict[str, Any]]] = []
                for item in selected_facts:
                    overlap = plan.query_terms & search_terms(
                        _searchable_text(item, ("entity_key", "entity_label", "concept", "value", "unknown_reason"))
                    )
                    score = len(overlap) + (2 * len(overlap & set(plan.topic_terms)))
                    candidates.append((score, item))
                top_score = max((score for score, _item in candidates), default=0)
                leaders = [item for score, item in candidates if score == top_score and score > 0]
                leader_entities = {item.get("entity_key") for item in leaders}
                if len(leader_entities) > 1:
                    message = (
                        "Pytanie jest niejednoznaczne; znalazłem kilka pasujących wspomnień."
                        if plan.language == "pl"
                        else "The question is ambiguous; I found several matching memories."
                    )
                    return message, "ambiguous", selected_facts, self._source_refs(selected_facts)

        if plan.requires_synthesis and not (plan.semantic_fallback and selected_facts):
            return None, "semantic", selected_facts, self._source_refs(
                [*selected_facts, *context.get("history", []), *context.get("relationships", [])]
            )

        if selected_facts:
            return (
                _answer_copy(plan, "relevant_memory")
                + "; ".join(_fact_summary(item) for item in selected_facts[:10])
                + ".",
                "retrieval",
                selected_facts,
                self._source_refs(selected_facts),
            )
        history = [item for item in context.get("history", []) if isinstance(item, dict)]
        if history:
            return (
                _answer_copy(plan, "relevant_memory")
                + "; ".join(_fact_summary(item) for item in history[:10])
                + ".",
                "retrieval",
                history[:MAX_ASK_CONTEXT_HISTORY],
                self._source_refs(history),
            )
        attention = [item for item in context.get("attention", []) if isinstance(item, dict)]
        if attention:
            labels = [str(item.get("title") or item.get("kind") or "open item") for item in attention[:10]]
            return _answer_copy(plan, "relevant_attention") + "; ".join(labels) + ".", "retrieval", attention, self._source_refs(attention)
        return None, "generic", [], []

    def ask(self, question: str) -> dict[str, Any]:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must not be empty")
        question = question.strip()
        plan = plan_ask(question)
        snapshot = self.store.snapshot(now=self._now())
        processing = snapshot.get("processing", {})
        counts = processing.get("counts", {}) if isinstance(processing, dict) else {}
        failed_count = int(counts.get("failed", 0) or 0)
        pending_count = int(counts.get("pending", 0) or 0)
        processing_count = int(counts.get("processing", 0) or 0)
        if failed_count:
            message = _answer_copy(plan, "processing_failed")
            return {
                "question": question,
                "mode": "processing_failed",
                "status": "processing_failed",
                "answer": message,
                "message": message,
                "items": [],
                "source_refs": [],
                "provider_used": False,
                "answer_language": plan.language if plan.language in {"en", "pl"} else "same_as_question",
                "processing": processing,
            }
        if pending_count or processing_count:
            message = _answer_copy(plan, "processing")
            return {
                "question": question,
                "mode": "processing",
                "status": "processing",
                "answer": message,
                "message": message,
                "items": [],
                "source_refs": [],
                "provider_used": False,
                "answer_language": plan.language if plan.language in {"en", "pl"} else "same_as_question",
                "processing": processing,
            }
        context, selected_facts, _normalized = self._retrieval_context(question, plan)
        deterministic, mode, items, refs = self._deterministic_answer(
            question,
            snapshot,
            context,
            selected_facts,
            plan,
        )
        if deterministic is not None:
            return {
                "question": question,
                "mode": mode,
                "status": "no_match" if mode == "no_match" else "ready",
                "answer": deterministic,
                "items": items,
                "source_refs": refs,
                "provider_used": False,
                "answer_language": plan.language,
                "processing": snapshot.get("processing", {}),
            }

        # The deterministic result above already derives refs from the facts it
        # rendered. Once synthesis is needed, every retrieval item is only a
        # candidate until the provider selects its explicit evidence IDs.
        refs = []
        relevant_items = [
            item
            for collection in (
                selected_facts,
                context.get("facts", []),
                context.get("candidate_facts", []),
                context.get("history", []),
                context.get("candidate_history", []),
                context.get("relationships", []),
                context.get("candidate_relationships", []),
                context.get("attention", []),
                context.get("candidate_attention", []),
            )
            for item in collection
            if isinstance(item, dict)
        ]
        has_processed_memory = any(
            isinstance(snapshot.get(name), list) and bool(snapshot.get(name))
            for name in ("current_facts", "fact_history", "relationships", "attention")
        )
        if not relevant_items:
            if not has_processed_memory:
                message = _answer_copy(plan, "no_data")
                mode = "no_data"
            else:
                message = _answer_copy(plan, "no_match")
                mode = "no_match"
            return {
                "question": question,
                "mode": mode,
                "status": mode,
                "answer": message,
                "items": [],
                "source_refs": [],
                "provider_used": False,
                "answer_language": plan.language if plan.language in {"en", "pl"} else "same_as_question",
                "processing": snapshot.get("processing", {}),
            }
        provider_used = False
        answer: str | None = None
        supporting_items: list[dict[str, Any]] = []
        provider: Any | None = None
        if plan.requires_synthesis:
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
                                    time_context={
                                        "now_utc": self._now().isoformat(),
                                        "timezone": local_timezone_name(),
                                        "response_language": context.get("response_language", "same_as_question"),
                                    },
                                )
                            else:
                                raw = method(question, context)
                            if isinstance(raw, str):
                                answer = raw.strip()
                                provider_evidence_ids: list[Any] = []
                            elif isinstance(raw, dict):
                                answer = _clean_text(raw.get("answer"), limit=4000)
                                provider_evidence_ids = (
                                    raw.get("evidence_ids", [])
                                    if isinstance(raw.get("evidence_ids"), list)
                                    else []
                                )
                            else:
                                provider_evidence_ids = []
                            selected_evidence_ids, supporting_items = self._validated_supporting_evidence(
                                context,
                                provider_evidence_ids,
                            )
                            if answer and provider_evidence_ids and not selected_evidence_ids:
                                # A provider answer backed only by invented or
                                # stale IDs cannot safely be rendered. Empty
                                # IDs remain valid for an explicit limitation
                                # answer such as "no supporting evidence".
                                answer = None
                                supporting_items = []
                            refs = self._source_refs(supporting_items) if answer else []
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
                supporting_items = []
                refs = []
        if not answer:
            fallback_items = selected_facts or (
                [] if plan.semantic_fallback else context.get("facts", [])
            ) or ([] if plan.semantic_fallback else context.get("history", []))
            if not fallback_items:
                message = _answer_copy(plan, "no_match")
                return {
                    "question": question,
                    "mode": "no_match",
                    "status": "no_match",
                    "answer": message,
                    "items": [],
                    "source_refs": [],
                    "provider_used": False,
                    "answer_language": plan.language if plan.language in {"en", "pl"} else "same_as_question",
                    "processing": snapshot.get("processing", {}),
                }
            answer = _answer_copy(plan, "relevant_memory") + "; ".join(
                _fact_summary(item) for item in fallback_items[:10]
            ) + "."
            supporting_items = list(fallback_items)
            refs = self._source_refs(supporting_items)
        result_items = self._public_items(supporting_items)
        return {
            "question": question,
            "mode": "semantic" if provider_used else "retrieval",
            "status": "ready",
            "answer": answer,
            "items": result_items[:MAX_ASK_SUPPORTING_EVIDENCE_IDS],
            "source_refs": refs,
            "provider_used": provider_used,
            "answer_language": plan.language if plan.language in {"en", "pl"} else "same_as_question",
            "processing": snapshot.get("processing", {}),
        }

    def attachment_bytes(self, sha256: str) -> tuple[bytes, dict[str, Any]]:
        return self.store.attachment_bytes(sha256)


__all__ = [
    "MAX_ATTACHMENT_BYTES",
    "MAX_CAPTURE_TEXT",
    "MAX_ASK_SUPPORTING_EVIDENCE_IDS",
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
    "normalize_temporal",
    "normalize_timestamp",
    "product_database_path",
    "resolve_timezone",
    "time_context_for_event",
]
