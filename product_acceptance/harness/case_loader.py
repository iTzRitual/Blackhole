"""Load and validate the public Product V2 acceptance-case format.

The repository deliberately avoids a third-party JSON-Schema dependency in the
CI harness.  ``case.schema.json`` remains the machine-readable contract; this
module implements the small semantic checks that JSON Schema cannot express
alone, such as duplicate IDs, timezone-aware timestamps, and fixture paths.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_DIR = PACKAGE_ROOT / "cases"
DEFAULT_FIXTURES_DIR = PACKAGE_ROOT / "fixtures"
CASE_ID_RE = re.compile(r"^[A-Z][A-Z0-9]{1,7}-[0-9]{3}$")
STEP_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
LOCALE_RE = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")
TIMEZONE_RE = re.compile(r"^[A-Za-z]+(?:/[A-Za-z0-9_.+-]+)+$")
STEP_TYPES = {
    "capture",
    "advance_time",
    "ask",
    "attention",
    "memory",
    "undo",
    "process",
    "retry",
    "restart",
    "set_provider",
    "health",
}
EXPECTATION_KEYS = {
    "saved",
    "durable",
    "processing",
    "message",
    "include",
    "exclude",
    "evidence",
    "uncertainty",
    "actionable",
    "not_urgent",
    "empty",
    "outcome",
    "removed_from_active",
    "raw_preserved",
    "state_preserved",
    "attachment_persisted",
    "duplicate",
}
STEP_KEYS = {
    "id",
    "type",
    "capture_id",
    "target_capture_id",
    "at",
    "to",
    "text",
    "attachment",
    "idempotency_key",
    "question",
    "availability",
    "expect",
}
CASE_KEYS = {
    "case_id",
    "title",
    "locale",
    "tags",
    "initial_time",
    "timezone",
    "user_outcome",
    "steps",
    "manual_observations",
}


class CaseValidationError(ValueError):
    """Raised when an acceptance case violates the public case contract."""


def parse_timestamp(value: Any, *, label: str) -> datetime:
    """Parse an RFC 3339-like timestamp and require an explicit UTC offset."""

    if not isinstance(value, str) or not value.strip():
        raise CaseValidationError(f"{label} must be a non-empty timestamp string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise CaseValidationError(f"{label} is not a valid ISO timestamp: {value!r}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CaseValidationError(f"{label} must include an explicit UTC offset: {value!r}")
    return parsed


def validate_timezone(value: Any, *, label: str = "timezone") -> str:
    if not isinstance(value, str) or not TIMEZONE_RE.fullmatch(value):
        raise CaseValidationError(f"{label} must be an IANA timezone name")
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as error:
        raise CaseValidationError(f"{label} is not available: {value!r}") from error
    return value


def resolve_fixture(reference: Any, fixtures_dir: Path = DEFAULT_FIXTURES_DIR) -> Path:
    """Resolve a case fixture without allowing absolute paths or traversal."""

    if not isinstance(reference, str) or not reference.strip():
        raise CaseValidationError("attachment.fixture must be a non-empty relative path")
    relative = Path(reference)
    if relative.is_absolute() or ".." in relative.parts:
        raise CaseValidationError(f"attachment.fixture must stay under fixtures/: {reference!r}")
    root = fixtures_dir.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise CaseValidationError(f"attachment.fixture escapes fixtures/: {reference!r}") from error
    if not candidate.is_file():
        raise CaseValidationError(f"attachment fixture does not exist: {reference!r}")
    return candidate


def _non_empty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CaseValidationError(f"{label} must be a non-empty string")


def _validate_expectation(value: Any, *, label: str) -> None:
    if not isinstance(value, dict):
        raise CaseValidationError(f"{label} must be an object")
    unknown = set(value) - EXPECTATION_KEYS
    if unknown:
        raise CaseValidationError(f"{label} has unsupported keys: {sorted(unknown)}")
    for key in ("include", "exclude", "removed_from_active"):
        if key in value:
            items = value[key]
            if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
                raise CaseValidationError(f"{label}.{key} must be a list of strings")
    for key in ("saved", "durable", "actionable", "not_urgent", "empty", "raw_preserved", "state_preserved", "attachment_persisted", "duplicate"):
        if key in value and not isinstance(value[key], bool):
            raise CaseValidationError(f"{label}.{key} must be boolean")
    if "message" in value:
        _non_empty_string(value["message"], f"{label}.message")
    if "processing" in value and value["processing"] not in {"pending", "processed", "failed", "fresh", "retryable"}:
        raise CaseValidationError(f"{label}.processing has an unsupported value")
    if "evidence" in value and value["evidence"] not in {"required", "not_required", "if_available"}:
        raise CaseValidationError(f"{label}.evidence has an unsupported value")
    if "uncertainty" in value and value["uncertainty"] not in {"required", "not_required", "if_relevant"}:
        raise CaseValidationError(f"{label}.uncertainty has an unsupported value")
    if "outcome" in value and value["outcome"] not in {"processed", "failed", "retryable", "fresh", "no_duplicate"}:
        raise CaseValidationError(f"{label}.outcome has an unsupported value")


def _validate_attachment(value: Any, *, label: str, fixtures_dir: Path) -> None:
    if not isinstance(value, dict):
        raise CaseValidationError(f"{label} must be an object")
    allowed = {"fixture", "mime_type", "filename"}
    unknown = set(value) - allowed
    if unknown:
        raise CaseValidationError(f"{label} has unsupported keys: {sorted(unknown)}")
    _non_empty_string(value.get("fixture"), f"{label}.fixture")
    _non_empty_string(value.get("mime_type"), f"{label}.mime_type")
    if "filename" in value:
        _non_empty_string(value["filename"], f"{label}.filename")
        if any(char in value["filename"] for char in ("/", "\\", "\x00")):
            raise CaseValidationError(f"{label}.filename must be a file name")
    resolve_fixture(value["fixture"], fixtures_dir)


def _validate_step(
    step: Any,
    *,
    case_label: str,
    index: int,
    fixtures_dir: Path,
    known_capture_refs: set[str],
) -> None:
    label = f"{case_label}.steps[{index}]"
    if not isinstance(step, dict):
        raise CaseValidationError(f"{label} must be an object")
    unknown = set(step) - STEP_KEYS
    if unknown:
        raise CaseValidationError(f"{label} has unsupported keys: {sorted(unknown)}")
    step_id = step.get("id")
    if not isinstance(step_id, str) or not STEP_ID_RE.fullmatch(step_id):
        raise CaseValidationError(f"{label}.id must be a lower-case kebab-case identifier")
    step_type = step.get("type")
    if step_type not in STEP_TYPES:
        raise CaseValidationError(f"{label}.type is unsupported: {step_type!r}")

    if step_type not in {"advance_time", "set_provider"}:
        if "at" not in step:
            raise CaseValidationError(f"{label}.at is required for {step_type}")
        parse_timestamp(step["at"], label=f"{label}.at")
    if "expect" in step:
        _validate_expectation(step["expect"], label=f"{label}.expect")

    if step_type == "capture":
        has_text = isinstance(step.get("text"), str) and bool(step["text"].strip())
        has_attachment = "attachment" in step
        if not has_text and not has_attachment:
            raise CaseValidationError(f"{label} needs text, attachment, or both")
        if "text" in step and not has_text:
            raise CaseValidationError(f"{label}.text must be a non-empty string when present")
        if has_attachment:
            _validate_attachment(step["attachment"], label=f"{label}.attachment", fixtures_dir=fixtures_dir)
        _non_empty_string(step.get("idempotency_key"), f"{label}.idempotency_key")
        capture_ref = step.get("capture_id", step_id)
        if not isinstance(capture_ref, str) or not STEP_ID_RE.fullmatch(capture_ref):
            raise CaseValidationError(f"{label}.capture_id must be a lower-case identifier")
        if capture_ref in known_capture_refs:
            raise CaseValidationError(f"{label} duplicates capture reference {capture_ref!r}")
        known_capture_refs.add(capture_ref)
        if "expect" not in step:
            raise CaseValidationError(f"{label}.expect is required for capture")
    elif step_type == "advance_time":
        if "to" not in step:
            raise CaseValidationError(f"{label}.to is required for advance_time")
        parse_timestamp(step["to"], label=f"{label}.to")
    elif step_type == "ask":
        _non_empty_string(step.get("question"), f"{label}.question")
        if "expect" not in step:
            raise CaseValidationError(f"{label}.expect is required for ask")
    elif step_type in {"attention", "memory"}:
        if "expect" not in step:
            raise CaseValidationError(f"{label}.expect is required for {step_type}")
    elif step_type == "undo":
        target = step.get("target_capture_id")
        _non_empty_string(target, f"{label}.target_capture_id")
        if target not in known_capture_refs:
            raise CaseValidationError(f"{label} references unknown earlier capture {target!r}")
        if "expect" not in step:
            raise CaseValidationError(f"{label}.expect is required for undo")
    elif step_type in {"process", "retry", "restart", "health"}:
        if "expect" not in step:
            raise CaseValidationError(f"{label}.expect is required for {step_type}")
    elif step_type == "set_provider":
        if step.get("availability") not in {"available", "unavailable", "fail_once"}:
            raise CaseValidationError(f"{label}.availability must be available, unavailable, or fail_once")


def validate_case(case: Any, *, source: str, fixtures_dir: Path = DEFAULT_FIXTURES_DIR) -> dict[str, Any]:
    """Validate one case and return it unchanged."""

    if not isinstance(case, dict):
        raise CaseValidationError(f"{source} case must be an object")
    unknown = set(case) - CASE_KEYS
    if unknown:
        raise CaseValidationError(f"{source} has unsupported keys: {sorted(unknown)}")
    case_id = case.get("case_id")
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        raise CaseValidationError(f"{source}.case_id must match PREFIX-000")
    for key in ("title", "user_outcome"):
        _non_empty_string(case.get(key), f"{source}.{key}")
    locale = case.get("locale")
    if not isinstance(locale, str) or not LOCALE_RE.fullmatch(locale):
        raise CaseValidationError(f"{source}.locale is invalid")
    tags = case.get("tags")
    if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        raise CaseValidationError(f"{source}.tags must be a non-empty list of strings")
    parse_timestamp(case.get("initial_time"), label=f"{source}.initial_time")
    validate_timezone(case.get("timezone"), label=f"{source}.timezone")
    steps = case.get("steps")
    if not isinstance(steps, list) or not steps:
        raise CaseValidationError(f"{source}.steps must be a non-empty list")
    if "manual_observations" in case:
        observations = case["manual_observations"]
        if not isinstance(observations, list) or not all(isinstance(item, str) and item.strip() for item in observations):
            raise CaseValidationError(f"{source}.manual_observations must be a list of non-empty strings")

    seen_step_ids: set[str] = set()
    known_capture_refs: set[str] = set()
    for index, step in enumerate(steps):
        if isinstance(step, dict) and step.get("id") in seen_step_ids:
            raise CaseValidationError(f"{source}.steps duplicates step id {step.get('id')!r}")
        if isinstance(step, dict):
            seen_step_ids.add(step.get("id"))
        _validate_step(
            step,
            case_label=source,
            index=index,
            fixtures_dir=fixtures_dir,
            known_capture_refs=known_capture_refs,
        )
    return case


def iter_case_files(cases_dir: Path = DEFAULT_CASES_DIR) -> Iterable[Path]:
    if not cases_dir.is_dir():
        raise CaseValidationError(f"case directory does not exist: {cases_dir}")
    files = sorted(path for path in cases_dir.glob("*.json") if path.is_file())
    if not files:
        raise CaseValidationError(f"case directory contains no JSON files: {cases_dir}")
    return files


def load_cases(
    cases_dir: Path = DEFAULT_CASES_DIR,
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR,
) -> list[dict[str, Any]]:
    """Parse all case collection files and reject duplicate case IDs."""

    loaded: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for path in iter_case_files(cases_dir):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CaseValidationError(f"could not parse {path}: {error}") from error
        if not isinstance(document, list):
            raise CaseValidationError(f"{path} must contain a JSON array of cases")
        for index, case in enumerate(document):
            source = f"{path.name}[{index}]"
            validated = validate_case(case, source=source, fixtures_dir=fixtures_dir)
            case_id = validated["case_id"]
            if case_id in seen_case_ids:
                raise CaseValidationError(f"duplicate case_id across files: {case_id}")
            seen_case_ids.add(case_id)
            loaded.append(validated)
    return loaded
