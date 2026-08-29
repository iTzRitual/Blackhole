"""Public response-contract helpers for the advanced runtime.

This module intentionally consumes only the public response contract. It does
not import the evaluator or any development expected output.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


ALLOWED_STATUS = {"known", "inferred", "unknown"}
ORDER_INSENSITIVE_KEYS = {"changed_fields", "observed_periods", "missing_periods", "unobserved_periods"}
DECIMAL_KEYS = {"amount", "total", "amount_eur", "cost_eur", "price_eur", "monthly_cost_eur"}
DATE_KEYS = {
    "date",
    "deadline",
    "due",
    "due_date",
    "effective_date",
    "effective_from",
    "effective_until",
    "expiry_date",
    "renewal_date",
    "signed_date",
    "termination_date",
    "price_effective",
    "observed_at",
}

UNKNOWN_REASON_ALIASES = {
    "conflicting": ("conflict", "contradict", "disagree", "different amounts"),
    "ambiguous_person": ("ambiguous", "unresolved", "could be jordan lee", "could be jordan kim"),
    "unreadable": ("unreadable", "illegible", "cannot read", "can't read"),
    "not_available": ("not available", "unavailable", "not provided", "not present"),
    "no_capture_for_period": ("no capture", "no bill", "no invoice", "missing period", "period not observed"),
    "no_consumption_observation": ("consumption", "consumed", "usage"),
    "not_stated": ("not stated", "not specified", "not mentioned"),
    "missing": ("missing", "no record", "no evidence", "unknown", "not recorded"),
}


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


def token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize_text(value)).strip()


def slug(value: str) -> str:
    return token(value).replace(" ", "_")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _alias_map(contract: dict[str, Any], section: str) -> dict[str, str]:
    result: dict[str, str] = {}
    entries = contract.get("public_ontology", {}).get(section, [])
    if not isinstance(entries, list):
        return result
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        canonical = entry["id"]
        for alias in [canonical, *entry.get("aliases", [])]:
            if isinstance(alias, str) and alias.strip():
                result[token(alias)] = canonical
    return result


def _object_key_alias_map(contract: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    aliases = contract.get("value_normalization", {}).get("object_field_aliases", {})
    if not isinstance(aliases, dict):
        return result
    for canonical, values in aliases.items():
        if not isinstance(canonical, str):
            continue
        result[slug(canonical)] = canonical
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str):
                    result[slug(value)] = canonical
    return result


def _enum_value_alias_map(contract: dict[str, Any], context_key: str | None) -> dict[str, str]:
    if not context_key:
        return {}
    aliases = contract.get("value_normalization", {}).get("enum_field_aliases", {})
    values = aliases.get(context_key) if isinstance(aliases, dict) else None
    if not isinstance(values, dict):
        return {}
    result: dict[str, str] = {}
    for canonical, options in values.items():
        if not isinstance(canonical, str):
            continue
        result[token(canonical)] = canonical
        if isinstance(options, list):
            for option in options:
                if isinstance(option, str):
                    result[token(option)] = canonical
    return result


def canonical_subject(value: Any, contract: dict[str, Any]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    aliases = _alias_map(contract, "subjects")
    normalized = token(value)
    if normalized in aliases:
        return aliases[normalized]
    match = re.fullmatch(r"(?:capture\s+)?(evt\s*[-_]?\s*\d+)", normalized)
    if match:
        event_id = re.sub(r"\s+", "", match.group(1)).replace("_", "-")
        if event_id.startswith("evt") and not event_id.startswith("evt-"):
            event_id = "evt-" + event_id[3:]
        return f"capture:{event_id}"
    return slug(value)


def canonical_predicate(value: Any, contract: dict[str, Any]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return _alias_map(contract, "predicates").get(token(value), slug(value))


def canonical_decimal(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        try:
            decimal = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return normalize_text(str(value)) if isinstance(value, str) else value
        if not decimal.is_finite():
            return value
        rendered = format(decimal, "f")
        if "." in rendered:
            rendered = rendered.rstrip("0").rstrip(".")
        return rendered or "0"
    return value


def canonical_date(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    match = re.fullmatch(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", value.strip())
    if not match:
        return normalize_text(value)
    try:
        if match.group(3) is None:
            return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}"
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
    except ValueError:
        return normalize_text(value)


def canonical_value(value: Any, contract: dict[str, Any], context_key: str | None = None) -> Any:
    key = slug(context_key) if context_key else None
    if isinstance(value, dict):
        aliases = _object_key_alias_map(contract)
        result: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            normalized_key = aliases.get(slug(raw_key), slug(raw_key)) if isinstance(raw_key, str) else str(raw_key)
            result[normalized_key] = canonical_value(raw_value, contract, normalized_key)
        return {name: result[name] for name in sorted(result)}
    if isinstance(value, list):
        result = [canonical_value(item, contract, context_key) for item in value]
        if key in {slug(item) for item in ORDER_INSENSITIVE_KEYS}:
            return sorted(result, key=canonical_json)
        return result
    if key in {slug(item) for item in DECIMAL_KEYS}:
        return canonical_decimal(value)
    if key in {slug(item) for item in DATE_KEYS}:
        return canonical_date(value)
    if isinstance(value, str):
        return _enum_value_alias_map(contract, context_key).get(token(value), normalize_text(value))
    return value


def canonical_unknown_reason(value: Any, contract: dict[str, Any]) -> str:
    normalized = normalize_text(str(value))
    allowed = contract.get("unknown_reason", {}).get("allowed_categories", [])
    allowed_set = {item for item in allowed if isinstance(item, str)}
    if normalized in allowed_set:
        return normalized
    for category, phrases in UNKNOWN_REASON_ALIASES.items():
        if category in allowed_set and any(phrase in normalized for phrase in phrases):
            return category
    return normalized


class PublicContract:
    """Canonicalize model proposals into the public v2 response shape."""

    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document

    def sanitize_assertion(self, value: Any, event_ids: set[str]) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None
        subject = canonical_subject(value.get("subject"), self.document)
        predicate = canonical_predicate(value.get("predicate"), self.document)
        status = normalize_text(value.get("knowledge_status", "")) if isinstance(value.get("knowledge_status"), str) else ""
        if subject is None or predicate is None or status not in ALLOWED_STATUS:
            return None
        refs_value = value.get("source_refs", [])
        if not isinstance(refs_value, list):
            refs_value = []
        refs = sorted({ref for ref in refs_value if isinstance(ref, str) and ref in event_ids})
        result: dict[str, Any] = {
            "subject": subject,
            "predicate": predicate,
            "knowledge_status": status,
            "source_refs": refs,
        }
        if status == "unknown":
            if "unknown_reason" not in value:
                return None
            result["unknown_reason"] = canonical_unknown_reason(value["unknown_reason"], self.document)
        else:
            if "value" not in value:
                return None
            result["value"] = canonical_value(value["value"], self.document, predicate)
            if "confirmation_ref" in value and isinstance(value["confirmation_ref"], str):
                result["confirmation_ref"] = normalize_text(value["confirmation_ref"])
        return result

    def sanitize_response(
        self,
        value: Any,
        *,
        scenario_id: str,
        checkpoint: int,
        query_ids: list[str],
        event_ids: set[str],
    ) -> dict[str, Any]:
        raw_queries: Any = value.get("queries") if isinstance(value, dict) else None
        if isinstance(raw_queries, list):
            raw_queries = {
                item.get("query_id"): {"assertions": item.get("assertions", [])}
                for item in raw_queries
                if isinstance(item, dict) and isinstance(item.get("query_id"), str)
            }
        if not isinstance(raw_queries, dict):
            raw_queries = {}
        queries: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for query_id in query_ids:
            query_value = raw_queries.get(query_id, {})
            raw_assertions = query_value.get("assertions", []) if isinstance(query_value, dict) else []
            if not isinstance(raw_assertions, list):
                raw_assertions = []
            assertions = [self.sanitize_assertion(item, event_ids) for item in raw_assertions]
            queries[query_id] = {"assertions": [item for item in assertions if item is not None]}
        return {
            "response_contract": self.document.get("response_contract"),
            "scenario_id": scenario_id,
            "checkpoint": checkpoint,
            "queries": queries,
        }
