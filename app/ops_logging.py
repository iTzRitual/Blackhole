"""Small, privacy-preserving operational logging for local Product V2 runs.

This is intentionally a line-oriented helper rather than an observability
framework.  Product V2 passes identifiers, counts, statuses, durations, and
bounded error summaries; capture/question content and provider payloads never
cross this boundary.
"""

from __future__ import annotations

import os
import re
import sys
import threading
from datetime import datetime, timezone
from typing import Any, TextIO


_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|authorization|bearer|cookie|credential|password|secret|token)\b\s*[:=]\s*)([^\s,;]+)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
_SECRET_COMPOUND = re.compile(r"(?i)\bsecret(?:[-_][A-Za-z0-9._~+/=-]+)+")
_SENSITIVE_FIELD = re.compile(
    r"(?i)(?:token|secret|password|credential|cookie|api[_-]?key|access[_-]?token|authorization|prompt|payload|content|capture[_-]?text|question|stdout|stderr)"
)
_IDENTIFIER_SAFE = re.compile(r"[^A-Za-z0-9_.:@/-]+")
_EVENT_SAFE = re.compile(r"[^A-Za-z0-9_.:@/ -]+")


def sanitize_error(value: Any, *, limit: int = 240) -> str:
    """Return one bounded, single-line error summary with credential redaction."""

    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    text = _BEARER.sub("Bearer [REDACTED]", text)
    text = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", text)
    text = _SECRET_COMPOUND.sub("[REDACTED]", text)
    return text[:limit] or "operation failed"


def sanitize_identifier(value: Any, *, limit: int = 96) -> str:
    """Keep IDs useful in a terminal without allowing arbitrary multiline text."""

    text = str(value or "").replace("\r", "").replace("\n", "")
    text = _BEARER.sub("Bearer [REDACTED]", text)
    text = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", text)
    text = _SECRET_COMPOUND.sub("[REDACTED]", text)
    return _IDENTIFIER_SAFE.sub("_", text)[:limit] or "unknown"


def sanitize_event_name(value: Any, *, limit: int = 80) -> str:
    """Keep event labels readable while removing control and arbitrary text."""

    text = str(value or "").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = _BEARER.sub("Bearer [REDACTED]", text)
    text = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", text)
    text = _SECRET_COMPOUND.sub("[REDACTED]", text)
    return _EVENT_SAFE.sub("", text)[:limit] or "operation"


def _format_value(key: str, value: Any) -> str:
    if _SENSITIVE_FIELD.search(key):
        return "[REDACTED]"
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if key in {"event", "request", "owner", "code", "status", "path", "provider", "type", "readiness", "mode"}:
        return sanitize_identifier(value)
    if key in {"error", "detail", "reason"}:
        return sanitize_error(value)
    return sanitize_identifier(value, limit=180)


class ProductOpsLogger:
    """Write concise timestamped operational events to a terminal stream."""

    def __init__(self, *, stream: TextIO | None = None, level: str | None = None) -> None:
        configured = (level or os.environ.get("BLACKHOLE_LOG_LEVEL", "info")).casefold().strip()
        self.level = "debug" if configured == "debug" else "info"
        self.stream = stream or sys.stderr
        self._lock = threading.RLock()

    def event(self, component: str, event_name: str, *, debug: bool = False, **fields: Any) -> None:
        if debug and self.level != "debug":
            return
        prefix = f"[{sanitize_identifier(component, limit=32)}] {sanitize_event_name(event_name)}"
        rendered = [prefix]
        for key, value in fields.items():
            safe_key = sanitize_identifier(key, limit=48)
            rendered.append(f"{safe_key}={_format_value(safe_key, value)}")
        timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")
        with self._lock:
            self.stream.write(f"{timestamp} {' '.join(rendered)}\n")
            self.stream.flush()


__all__ = ["ProductOpsLogger", "sanitize_error", "sanitize_event_name", "sanitize_identifier"]
