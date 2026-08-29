"""Generic raw-source completeness evidence and selective verification helpers.

This module identifies structural anchors and conservative coverage gaps. It
does not read the evaluator, benchmark expected output, or any holdout data.
The deterministic completion pass may add derived observations only when a
lexical mapping is unambiguous. A provider verifier is intentionally scoped to
one capture and is biased toward no change.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from app.contract import canonical_predicate, canonical_subject, canonical_value, normalize_text


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PROMPT_PATH = ROOT / "prompts" / "runtime" / "advanced-e004-verifier-v1.md"
EVIDENCE_SCANNER_VERSION = "experiment-004-evidence-scanner-v1"
DETERMINISTIC_COMPLETION_VERSION = "experiment-004-deterministic-completion-v1"
VERIFIER_VERSION = "experiment-004-selective-verifier-v1"

_DATE_RE = re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b")
_CURRENCY_CODES = (
    "EUR|USD|GBP|CHF|CAD|AUD|NZD|JPY|CNY|SEK|NOK|DKK|PLN|CZK|HUF|INR"
)
_AMOUNT_RE = re.compile(
    rf"(?P<number>\d{{1,9}}(?:[.,]\d{{1,2}})?)\s*(?P<currency>{_CURRENCY_CODES})\b"
    rf"|(?P<currency_before>{_CURRENCY_CODES})\s*(?P<number_before>\d{{1,9}}(?:[.,]\d{{1,2}})?)\b",
    re.IGNORECASE,
)
_CURRENCY_RE = re.compile(rf"\b(?:{_CURRENCY_CODES})\b", re.IGNORECASE)
_IDENTIFIER_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,15}[-_][A-Z0-9]{1,15}\b")

_CUES: tuple[tuple[str, str], ...] = (
    ("temporal_cue", "signed"),
    ("temporal_cue", "effective"),
    ("temporal_cue", "starts"),
    ("temporal_cue", "expires"),
    ("temporal_cue", "expiry"),
    ("temporal_cue", "renewal"),
    ("temporal_cue", "renews"),
    ("temporal_cue", "due"),
    ("temporal_cue", "deadline"),
    ("temporal_cue", "cancelled"),
    ("temporal_cue", "canceled"),
    ("temporal_cue", "completed"),
    ("temporal_cue", "replaced"),
    ("temporal_cue", "reopen"),
    ("temporal_cue", "reopened"),
    ("temporal_cue", "ends"),
    ("temporal_cue", "through"),
    ("temporal_cue", "monthly"),
    ("temporal_cue", "per month"),
    ("lifecycle_cue", "proposal"),
    ("lifecycle_cue", "proposed"),
    ("lifecycle_cue", "prepare"),
    ("lifecycle_cue", "prepared"),
    ("lifecycle_cue", "withdraw"),
    ("lifecycle_cue", "withdrawn"),
    ("lifecycle_cue", "active"),
    ("lifecycle_cue", "current"),
    ("lifecycle_cue", "draft"),
    ("lifecycle_cue", "no request"),
    ("lifecycle_cue", "not sent"),
    ("lifecycle_cue", "do not send"),
    ("lifecycle_cue", "should ask"),
    ("action_cue", "send"),
    ("action_cue", "pay"),
    ("action_cue", "transfer"),
    ("action_cue", "cancel"),
    ("action_cue", "sign"),
    ("action_cue", "approve"),
    ("action_cue", "approval"),
    ("action_cue", "execute"),
    ("action_cue", "request"),
)


def _payload_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return ""
    preferred = ("text", "content", "body", "transcript", "ocr_text")
    parts = [str(payload[key]) for key in preferred if isinstance(payload.get(key), str)]
    return "\n".join(parts)


def _context(text: str, start: int, end: int, radius: int = 48) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return text[left:right].strip()


def _cue_matches(text: str) -> list[tuple[int, int, str, str]]:
    matches: list[tuple[int, int, str, str]] = []
    for cue_type, cue in _CUES:
        pattern = re.compile(r"(?<!\w)" + re.escape(cue) + r"(?!\w)", re.IGNORECASE)
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), cue_type, normalize_text(match.group())))
    return matches


def _nearest_cue(
    cue_matches: list[tuple[int, int, str, str]],
    start: int,
    end: int,
) -> tuple[str, str] | None:
    nearby = [item for item in cue_matches if item[0] <= end + 48 and item[1] >= start - 48]
    if not nearby:
        return None
    chosen = min(nearby, key=lambda item: min(abs(item[1] - start), abs(item[0] - end)))
    return chosen[2], chosen[3]


def scan_raw_evidence(event: dict[str, Any]) -> dict[str, Any]:
    """Return structural anchors without interpreting a complete semantic fact."""

    event_id = event.get("event_id")
    text = _payload_text(event.get("payload"))
    cue_matches = _cue_matches(text)
    anchors: list[tuple[int, str, dict[str, Any]]] = []

    for match in _DATE_RE.finditer(text):
        try:
            date.fromisoformat(match.group())
        except ValueError:
            continue
        cue = _nearest_cue(cue_matches, match.start(), match.end())
        anchor: dict[str, Any] = {
            "type": "date",
            "raw_value": match.group(),
            "context": _context(text, match.start(), match.end()),
        }
        if cue is not None:
            anchor["cue_type"], anchor["cue"] = cue
        anchors.append((match.start(), "date", anchor))

    for match in _AMOUNT_RE.finditer(text):
        number = match.group("number") or match.group("number_before")
        currency = match.group("currency") or match.group("currency_before")
        if number is None or currency is None:
            continue
        anchor = {
            "type": "amount",
            "raw_value": number,
            "currency": normalize_text(currency),
            "context": _context(text, match.start(), match.end()),
        }
        anchors.append((match.start(), "amount", anchor))
        anchors.append(
            (
                match.start(),
                "currency",
                {
                    "type": "currency",
                    "raw_value": normalize_text(currency),
                    "context": _context(text, match.start(), match.end()),
                },
            )
        )

    amount_spans = [(start, end) for start, end in ((match.start(), match.end()) for match in _AMOUNT_RE.finditer(text))]
    for match in _CURRENCY_RE.finditer(text):
        if any(start <= match.start() < end for start, end in amount_spans):
            continue
        anchors.append(
            (
                match.start(),
                "currency",
                {
                    "type": "currency",
                    "raw_value": normalize_text(match.group()),
                    "context": _context(text, match.start(), match.end()),
                },
            )
        )

    for match in _IDENTIFIER_RE.finditer(text):
        cue = _nearest_cue(cue_matches, match.start(), match.end())
        anchor = {
            "type": "identifier",
            "raw_value": match.group(),
            "context": _context(text, match.start(), match.end()),
        }
        if cue is not None:
            anchor["cue_type"], anchor["cue"] = cue
        anchors.append((match.start(), "identifier", anchor))

    for start, end, cue_type, cue in cue_matches:
        anchors.append(
            (
                start,
                cue,
                {
                    "type": cue_type,
                    "raw_value": cue,
                    "context": _context(text, start, end),
                },
            )
        )

    anchors.sort(key=lambda item: (item[0], item[1], json.dumps(item[2], sort_keys=True)))
    return {
        "event_id": event_id,
        "text_length": len(text),
        "anchors": [item[2] for item in anchors],
    }


def _subject_kinds(contract: dict[str, Any]) -> dict[str, str]:
    return {
        item["id"]: item.get("kind", "")
        for item in contract.get("public_ontology", {}).get("subjects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _history(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in snapshot.get("history", []) if isinstance(item, dict)]


def _event_observations(snapshot: dict[str, Any], event_id: str) -> list[dict[str, Any]]:
    return [item for item in _history(snapshot) if item.get("event_id") == event_id]


def _value_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [part for child in value.values() for part in _value_strings(child)]
    if isinstance(value, list):
        return [part for child in value for part in _value_strings(child)]
    return []


def _known_observation(item: dict[str, Any]) -> bool:
    return item.get("knowledge_status") in {"known", "inferred"} and "value" in item


def _event_has_value(event_observations: list[dict[str, Any]], raw_value: str) -> bool:
    raw = normalize_text(raw_value)
    for item in event_observations:
        if not _known_observation(item):
            continue
        if any(raw == normalize_text(value) or raw in normalize_text(value) for value in _value_strings(item.get("value"))):
            return True
    return False


def _decimal(value: Any) -> Decimal | None:
    try:
        result = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return result if result.is_finite() else None


def _amount_represented(event_observations: list[dict[str, Any]], raw_amount: str, currency: str) -> bool:
    expected_amount = _decimal(raw_amount)
    expected_currency = normalize_text(currency)
    for item in event_observations:
        if not _known_observation(item):
            continue
        value = item.get("value")
        if not isinstance(value, dict) or _decimal(value.get("amount")) != expected_amount:
            continue
        if normalize_text(str(value.get("currency", ""))) == expected_currency:
            return True
    return False


def _subject_has_value(
    snapshot: dict[str, Any],
    subject: str,
    predicate: str,
    raw_value: str,
) -> bool:
    for item in _history(snapshot):
        if item.get("subject") != subject or item.get("predicate") != predicate or not _known_observation(item):
            continue
        if _event_has_value([item], raw_value):
            return True
    for item in snapshot.get("current_facts", []):
        if not isinstance(item, dict) or item.get("subject") != subject or item.get("predicate") != predicate:
            continue
        if _known_observation(item) and _event_has_value([item], raw_value):
            return True
    return False


def _subject_for_kind(subjects: list[str], kinds: dict[str, str], allowed: set[str]) -> list[str]:
    return [subject for subject in subjects if kinds.get(subject) in allowed]


def _date_predicate(anchor: dict[str, Any]) -> str | None:
    cue = normalize_text(str(anchor.get("cue", "")))
    if cue == "signed":
        return "signed_date"
    if cue == "effective" or cue == "starts":
        return "effective_date"
    if cue in {"expires", "expiry", "ends", "through"}:
        return "expiry_date"
    if cue in {"renewal", "renews"}:
        return "next_renewal"
    if cue in {"due", "deadline"}:
        return "deadline"
    return None


def _identifier_predicate(anchor: dict[str, Any], subject_kind: str) -> str | None:
    context = normalize_text(str(anchor.get("context", "")))
    if subject_kind == "contract" and (
        any(term in context for term in ("contract", "agreement", "identif", "replacement", "current"))
        or normalize_text(str(anchor.get("cue", ""))) in {"signed", "effective", "renewal", "renews"}
    ):
        return "contract_id"
    if subject_kind == "insurance" and any(term in context for term in ("policy", "document", "card", "current")):
        return "policy_id"
    return None


def _lifecycle_hint(text: str, kind: str, anchors: list[dict[str, Any]]) -> str | None:
    lower = normalize_text(text)
    cues = {normalize_text(str(anchor.get("raw_value", ""))) for anchor in anchors}
    if kind == "task":
        if "reopen" in cues or "reopened" in cues:
            return "open"
        if "completed" in cues:
            return "completed"
        if "cancelled" in cues or "canceled" in cues:
            return "cancelled"
        return None
    if kind == "action":
        if "withdraw" in cues or "withdrawn" in cues or "withdraw" in lower:
            return "withdrawn"
        if any(cue in cues for cue in {"proposal", "proposed", "prepare", "prepared", "draft", "no request", "not sent", "do not send", "should ask"}):
            return "proposed"
    return None


def _event_subjects(event_observations: list[dict[str, Any]]) -> list[str]:
    return sorted({str(item.get("subject")) for item in event_observations if isinstance(item.get("subject"), str)})


def detect_coverage_gaps(
    event: dict[str, Any],
    evidence: dict[str, Any],
    snapshot: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Compare anchors to same-event observations using conservative heuristics."""

    event_id = str(event.get("event_id", ""))
    text = _payload_text(event.get("payload"))
    event_observations = _event_observations(snapshot, event_id)
    subjects = _event_subjects(event_observations)
    kinds = _subject_kinds(contract)
    reasons: list[str] = []
    mappings: list[dict[str, Any]] = []
    anchors = [item for item in evidence.get("anchors", []) if isinstance(item, dict)]

    for anchor in anchors:
        if anchor.get("type") != "date":
            continue
        predicate = _date_predicate(anchor)
        if predicate is None:
            continue
        allowed = {"contract", "insurance", "task", "subscription", "action"}
        for subject in _subject_for_kind(subjects, kinds, allowed):
            if _event_has_value(event_observations, str(anchor.get("raw_value", ""))) or _subject_has_value(
                snapshot, subject, predicate, str(anchor.get("raw_value", ""))
            ):
                continue
            mappings.append(
                {
                    "kind": "date",
                    "subject": subject,
                    "predicate": predicate,
                    "raw_value": anchor.get("raw_value"),
                    "reason": f"explicit {predicate} not represented",
                }
            )
            reasons.append(f"explicit {predicate} not represented")

    for anchor in anchors:
        if anchor.get("type") != "identifier":
            continue
        for subject in subjects:
            predicate = _identifier_predicate(anchor, kinds.get(subject, ""))
            if predicate is None or _event_has_value(event_observations, str(anchor.get("raw_value", ""))):
                continue
            if _subject_has_value(snapshot, subject, predicate, str(anchor.get("raw_value", ""))):
                continue
            mappings.append(
                {
                    "kind": "identifier",
                    "subject": subject,
                    "predicate": predicate,
                    "raw_value": anchor.get("raw_value"),
                    "reason": f"explicit {predicate} not represented",
                }
            )
            reasons.append(f"explicit {predicate} not represented")

    period_cue = next(
        (
            anchor
            for anchor in anchors
            if anchor.get("type") == "temporal_cue" and anchor.get("raw_value") in {"monthly", "per month"}
        ),
        None,
    )
    for item in event_observations:
        if not _known_observation(item) or not isinstance(item.get("value"), dict):
            continue
        value = item["value"]
        if period_cue is not None and "amount" in value and "billing_period" not in value:
            mappings.append(
                {
                    "kind": "billing_period",
                    "subject": item.get("subject"),
                    "predicate": item.get("predicate"),
                    "raw_value": "month",
                    "reason": "explicit monthly cue not represented in amount object",
                }
            )
            reasons.append("explicit monthly cue not represented in amount object")
        for anchor in anchors:
            if anchor.get("type") != "amount" or "currency" in value:
                continue
            if _decimal(value.get("amount")) != _decimal(anchor.get("raw_value")):
                continue
            mappings.append(
                {
                    "kind": "currency",
                    "subject": item.get("subject"),
                    "predicate": item.get("predicate"),
                    "raw_value": anchor.get("currency"),
                    "reason": "explicit currency not represented in amount object",
                }
            )
            reasons.append("explicit currency not represented in amount object")
            break

    for subject in _subject_for_kind(subjects, kinds, {"action", "task"}):
        if any(
            item.get("subject") == subject
            and item.get("predicate") == "status"
            and item.get("knowledge_status") in {"known", "inferred"}
            for item in event_observations
        ):
            continue
        hint = _lifecycle_hint(text, kinds.get(subject, ""), anchors)
        if hint is None:
            continue
        mappings.append(
            {
                "kind": "lifecycle",
                "subject": subject,
                "predicate": "status",
                "raw_value": hint,
                "reason": f"lifecycle cue supports status {hint}",
            }
        )
        reasons.append(f"lifecycle cue supports status {hint}")

    return {
        "event_id": event_id,
        "subjects": subjects,
        "reasons": list(dict.fromkeys(reasons)),
        "mappings": mappings,
        "existing_observations": [
            {
                key: item[key]
                for key in ("subject", "predicate", "knowledge_status", "operation", "value", "unknown_reason")
                if key in item
            }
            for item in event_observations
        ],
    }


def _existing_event_value(
    observations: list[dict[str, Any]],
    subject: str,
    predicate: str,
) -> dict[str, Any] | None:
    for item in observations:
        if item.get("subject") == subject and item.get("predicate") == predicate and _known_observation(item):
            return item
    return None


def deterministic_completions(
    event: dict[str, Any],
    gap: dict[str, Any],
    snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return only unambiguous derived observations for a flagged capture."""

    event_id = str(event.get("event_id", ""))
    observations = _event_observations(snapshot, event_id)
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for mapping in gap.get("mappings", []):
        subject = mapping.get("subject")
        predicate = mapping.get("predicate")
        if not isinstance(subject, str) or not isinstance(predicate, str):
            continue
        raw_value = mapping.get("raw_value")
        if not isinstance(raw_value, str):
            continue
        key = (subject, predicate, normalize_text(raw_value))
        if key in seen:
            continue
        seen.add(key)
        existing = _existing_event_value(observations, subject, predicate)
        if mapping.get("kind") == "billing_period":
            if existing is None or not isinstance(existing.get("value"), dict):
                continue
            value = copy.deepcopy(existing["value"])
            if "billing_period" in value:
                continue
            value["billing_period"] = "month"
            operation = "correction"
        elif mapping.get("kind") == "currency":
            if existing is None or not isinstance(existing.get("value"), dict) or "currency" in existing["value"]:
                continue
            value = copy.deepcopy(existing["value"])
            value["currency"] = normalize_text(raw_value)
            operation = "correction"
        else:
            if _subject_has_value(snapshot, subject, predicate, raw_value):
                continue
            value = raw_value if mapping.get("kind") != "identifier" else normalize_text(raw_value)
            operation = "correction" if existing is not None else "set"
        result.append(
            {
                "event_id": event_id,
                "subject": subject,
                "predicate": predicate,
                "knowledge_status": "known",
                "value": value,
                "operation": operation,
                "source_refs": [event_id],
                "completion_reason": mapping.get("reason", "deterministic evidence completion"),
                "completion_version": DETERMINISTIC_COMPLETION_VERSION,
            }
        )
    return result


def relevant_subject_state(snapshot: dict[str, Any], subjects: list[str]) -> list[dict[str, Any]]:
    allowed = set(subjects)
    return [
        copy.deepcopy(item)
        for item in snapshot.get("current_facts", [])
        if isinstance(item, dict) and item.get("subject") in allowed
    ]


def verification_prompt(
    event: dict[str, Any],
    gap: dict[str, Any],
    evidence: dict[str, Any],
    snapshot: dict[str, Any],
    contract: dict[str, Any],
) -> str:
    """Build a one-capture verifier prompt with no expected/evaluator data."""

    event_id = str(event.get("event_id", ""))
    public_contract = {
        "public_ontology": contract.get("public_ontology", {}),
        "predicate_value_shapes": contract.get("predicate_value_shapes", {}),
        "unknown_reason": contract.get("unknown_reason", {}),
    }
    return (
        VERIFIER_PROMPT_PATH.read_text(encoding="utf-8")
        + "\n\nPUBLIC ONTOLOGY AND VALUE SHAPES:\n"
        + json.dumps(public_contract, ensure_ascii=False, indent=2)
        + "\n\nONE RAW CAPTURE:\n"
        + json.dumps(event, ensure_ascii=False, indent=2)
        + "\n\nEXISTING OBSERVATIONS FOR THIS CAPTURE:\n"
        + json.dumps(gap.get("existing_observations", []), ensure_ascii=False, indent=2)
        + "\n\nSTRUCTURAL EVIDENCE ANCHORS:\n"
        + json.dumps(evidence.get("anchors", []), ensure_ascii=False, indent=2)
        + "\n\nCURRENT STATE FOR SUBJECTS IN THIS CAPTURE:\n"
        + json.dumps(relevant_subject_state(snapshot, gap.get("subjects", [])), ensure_ascii=False, indent=2)
        + f"\n\nVERIFICATION TARGET EVENT ID: {event_id}\n"
        + "\n\nReturn only the specified JSON object."
    )


def _value_has_anchor(value: Any, anchors: list[dict[str, Any]]) -> bool:
    values = [normalize_text(item) for item in _value_strings(value)]
    for anchor in anchors:
        raw = normalize_text(str(anchor.get("raw_value", "")))
        if raw and any(raw == value or raw in value for value in values):
            return True
        if anchor.get("type") == "amount" and isinstance(value, dict):
            if _decimal(value.get("amount")) == _decimal(anchor.get("raw_value")) and normalize_text(str(value.get("currency", ""))) == normalize_text(str(anchor.get("currency", ""))):
                return True
    return False


def _status_supported(value: Any, anchors: list[dict[str, Any]]) -> bool:
    status = normalize_text(str(value))
    cues = {normalize_text(str(anchor.get("raw_value", ""))) for anchor in anchors}
    return (
        (status == "proposed" and cues & {"proposal", "proposed", "prepare", "prepared", "draft", "no request", "not sent", "do not send", "should ask"})
        or (status == "open" and cues & {"reopen", "reopened"})
        or (status == "withdrawn" and cues & {"withdraw", "withdrawn"})
        or (status == "completed" and "completed" in cues)
        or (status in {"cancelled", "canceled"} and cues & {"cancelled", "canceled"})
        or (status in {"active", "current"} and cues & {"active", "current"})
    )


def prepare_verifier_observations(
    parsed: Any,
    *,
    event_id: str,
    evidence: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Validate verifier proposals before normal runner canonicalization."""

    if not isinstance(parsed, dict):
        return {"items": [], "no_change": True, "rejected": ["verifier output is not an object"]}
    rejected: list[str] = []
    accepted: list[dict[str, Any]] = []
    anchors = [item for item in evidence.get("anchors", []) if isinstance(item, dict)]
    for field, default_operation in (("add_observations", "set"), ("replace_observations", "correction")):
        raw_items = parsed.get(field, [])
        if not isinstance(raw_items, list):
            rejected.append(f"{field} is not an array")
            continue
        for index, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, dict):
                rejected.append(f"{field}[{index}] is not an object")
                continue
            if "state_key" in raw_item or any(key in raw_item for key in ("expected", "score", "evaluator")):
                rejected.append(f"{field}[{index}] contains prohibited field")
                continue
            item = copy.deepcopy(raw_item)
            supplied_event = item.get("event_id", event_id)
            if supplied_event != event_id:
                rejected.append(f"{field}[{index}] references another event")
                continue
            subject = canonical_subject(item.get("subject"), contract)
            predicate = canonical_predicate(item.get("predicate"), contract)
            status = normalize_text(item.get("knowledge_status", "")) if isinstance(item.get("knowledge_status"), str) else ""
            if subject is None or predicate is None or status not in {"known", "inferred", "unknown"}:
                rejected.append(f"{field}[{index}] has invalid public identity/status")
                continue
            if status == "unknown":
                if "unknown_reason" not in item or "value" in item:
                    rejected.append(f"{field}[{index}] has invalid unknown shape")
                    continue
            elif "value" not in item:
                rejected.append(f"{field}[{index}] has no value")
                continue
            if status != "unknown" and predicate == "status":
                if not _status_supported(item.get("value"), anchors):
                    rejected.append(f"{field}[{index}] status is not supported by anchors")
                    continue
            elif status != "unknown" and not _value_has_anchor(item.get("value"), anchors):
                rejected.append(f"{field}[{index}] value is not supported by anchors")
                continue
            item["event_id"] = event_id
            item["subject"] = subject
            item["predicate"] = predicate
            item["knowledge_status"] = status
            item["operation"] = default_operation
            item["source_refs"] = [event_id]
            item["verification_version"] = VERIFIER_VERSION
            accepted.append(item)
    no_change = bool(parsed.get("no_change")) or not accepted
    return {"items": accepted, "no_change": no_change, "rejected": rejected}


def evidence_digest(evidence: dict[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


__all__ = [
    "DETERMINISTIC_COMPLETION_VERSION",
    "EVIDENCE_SCANNER_VERSION",
    "VERIFIER_VERSION",
    "detect_coverage_gaps",
    "deterministic_completions",
    "evidence_digest",
    "prepare_verifier_observations",
    "relevant_subject_state",
    "scan_raw_evidence",
    "verification_prompt",
]
