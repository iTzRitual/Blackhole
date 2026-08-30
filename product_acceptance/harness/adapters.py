"""Black-box Host adapters used by the Product V2 acceptance harness.

The HTTP adapter only speaks public JSON over HTTP and never imports ``app``.
The mock adapter is deliberately small: it exercises capture durability,
idempotency, attachment persistence, provider failure/retry, and restart
plumbing, while leaving semantic surfaces unsupported so the report cannot
pretend that a stub is product evidence.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _response(*, supported: bool, ok: bool, status: int | None = None, **payload: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"_supported": supported, "ok": ok}
    if status is not None:
        result["_status"] = status
    result.update(payload)
    return result


def _unsupported(reason: str) -> dict[str, Any]:
    return _response(supported=False, ok=False, reason=reason)


class MockHostAdapter:
    """Deterministic transport stub for CI and local harness tests."""

    name = "mock"

    def __init__(self) -> None:
        self.case_id = ""
        self.current_time = None
        self.provider_mode = "available"
        self.provider_calls = 0
        self.captures: dict[str, dict[str, Any]] = {}
        self.by_idempotency_key: dict[str, str] = {}

    def begin_case(self, case_id: str) -> None:
        self.__init__()
        self.case_id = case_id

    def set_time(self, timestamp: Any) -> dict[str, Any]:
        self.current_time = timestamp
        return _response(supported=True, ok=True, time=timestamp.isoformat())

    def set_provider(self, availability: str) -> dict[str, Any]:
        self.provider_mode = availability
        return _response(supported=True, ok=True, provider_mode=availability)

    def capture(self, step: dict[str, Any], *, fixture_path: Path | None = None) -> dict[str, Any]:
        key = step["idempotency_key"]
        capture_ref = step.get("capture_id", step["id"])
        if key in self.by_idempotency_key:
            existing_ref = self.by_idempotency_key[key]
            existing = self.captures[existing_ref]
            return _response(
                supported=True,
                ok=True,
                saved=True,
                message="Saved.",
                capture={
                    "event_id": existing["event_id"],
                    "capture_id": existing_ref,
                    "duplicate": True,
                },
                processing={"status": existing["status"]},
            )

        attachment: dict[str, Any] | None = None
        if fixture_path is not None:
            content = fixture_path.read_bytes()
            attachment_spec = step["attachment"]
            attachment = {
                "filename": attachment_spec.get("filename", fixture_path.name),
                "mime_type": attachment_spec["mime_type"],
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
            }
        event_id = f"mock-{self.case_id}-{capture_ref}"
        self.by_idempotency_key[key] = capture_ref
        self.captures[capture_ref] = {
            "event_id": event_id,
            "text": step.get("text"),
            "attachment": attachment,
            "status": "pending",
            "active": True,
            "attempts": 0,
        }
        return _response(
            supported=True,
            ok=True,
            saved=True,
            message="Saved.",
            capture={
                "event_id": event_id,
                "capture_id": capture_ref,
                "duplicate": False,
                "attachment": attachment,
            },
            processing={"status": "pending"},
        )

    def _counts(self) -> dict[str, int]:
        counts = {"pending": 0, "failed": 0, "processed": 0, "active": 0}
        for capture in self.captures.values():
            counts[capture["status"]] += 1
            if capture["active"]:
                counts["active"] += 1
        return counts

    def process(self) -> dict[str, Any]:
        pending = [capture for capture in self.captures.values() if capture["status"] == "pending"]
        if not pending:
            counts = self._counts()
            return _response(
                supported=True,
                ok=True,
                processing={"status": "fresh", "processed": 0, "pending": counts["pending"], "failed": counts["failed"]},
            )
        for capture in pending:
            capture["attempts"] += 1
        self.provider_calls += 1
        if self.provider_mode in {"unavailable", "fail_once"}:
            for capture in pending:
                capture["status"] = "failed"
            if self.provider_mode == "fail_once":
                self.provider_mode = "available"
            counts = self._counts()
            return _response(
                supported=True,
                ok=False,
                status=503,
                code="provider_unavailable",
                error="provider unavailable; retry available",
                processing={"status": "failed", "failed": len(pending), "failed_count": counts["failed"], "pending": counts["pending"]},
            )
        for capture in pending:
            capture["status"] = "processed"
        counts = self._counts()
        return _response(
            supported=True,
            ok=True,
            processing={"status": "processed", "processed": len(pending), "pending": counts["pending"], "failed": counts["failed"]},
        )

    def retry(self) -> dict[str, Any]:
        failed = [capture for capture in self.captures.values() if capture["status"] == "failed"]
        if not failed:
            counts = self._counts()
            return _response(
                supported=True,
                ok=True,
                processing={"status": "fresh", "processed": 0, "pending": counts["pending"], "failed": counts["failed"]},
            )
        for capture in failed:
            capture["status"] = "pending"
        return self.process()

    def ask(self, _question: str) -> dict[str, Any]:
        return _unsupported("mock semantic Ask surface is intentionally not implemented")

    def attention(self) -> dict[str, Any]:
        return _unsupported("mock semantic Attention surface is intentionally not implemented")

    def memory(self) -> dict[str, Any]:
        return _unsupported("mock semantic Memory surface is intentionally not implemented")

    def undo(self, capture_ref: str) -> dict[str, Any]:
        capture = self.captures.get(capture_ref)
        if capture is None:
            return _response(supported=True, ok=False, status=404, error="capture not found")
        capture["active"] = False
        return _response(
            supported=True,
            ok=True,
            undo={"capture_id": capture_ref, "active": False, "raw_preserved": True},
        )

    def restart(self) -> dict[str, Any]:
        counts = self._counts()
        return _response(supported=True, ok=True, restart={"state_preserved": True, "counts": counts})

    def health(self) -> dict[str, Any]:
        return _response(supported=True, ok=True, health={"ready": True})


class HttpHostAdapter:
    """HTTP-only adapter for a Product V2 Host or compatible local transport."""

    name = "http"

    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def begin_case(self, _case_id: str) -> None:
        # A Host restart or data reset is intentionally not inferred from HTTP.
        # The human/integration runner owns isolation for a real target.
        return None

    def set_time(self, _timestamp: Any) -> dict[str, Any]:
        return _unsupported("HTTP target does not expose a test clock")

    def set_provider(self, _availability: str) -> dict[str, Any]:
        return _unsupported("provider fault injection is target-owned")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                status = response.status
        except HTTPError as error:
            raw = error.read()
            status = error.code
        except URLError as error:
            return _response(supported=False, ok=False, error=f"HTTP target unavailable: {error.reason}")
        except OSError as error:
            return _response(supported=False, ok=False, error=f"HTTP target unavailable: {error}")
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            body = {"body": raw.decode("utf-8", errors="replace")}
        if not isinstance(body, dict):
            body = {"body": body}
        # A 404/405 means the logical V2 surface is not exposed by this target;
        # other HTTP failures are real target failures and therefore remain
        # supported so the report can mark them FAIL.
        supported = status not in {404, 405}
        result = _response(supported=supported, ok=200 <= status < 300, status=status, **body)
        if not result["ok"] and "error" not in result:
            result["error"] = f"HTTP {status}"
        return result

    def capture(self, step: dict[str, Any], *, fixture_path: Path | None = None) -> dict[str, Any]:
        attachment_spec = step.get("attachment")
        attachment = None
        if attachment_spec is not None and fixture_path is not None:
            attachment = {
                "filename": attachment_spec.get("filename", fixture_path.name),
                "mime_type": attachment_spec["mime_type"],
                "content_base64": base64.b64encode(fixture_path.read_bytes()).decode("ascii"),
            }
        source_type = "text"
        if attachment_spec is not None:
            source_type = "image" if attachment_spec["mime_type"].startswith("image/") else "document"
        payload: dict[str, Any] = {
            "text": step.get("text"),
            "source_type": source_type,
            "captured_at": step["at"],
            "idempotency_key": step["idempotency_key"],
        }
        if attachment is not None:
            payload["attachment"] = attachment
        return self._request("POST", "/api/capture", payload)

    def process(self) -> dict[str, Any]:
        return self._request("POST", "/api/process", {})

    def retry(self) -> dict[str, Any]:
        return self._request("POST", "/api/retry", {})

    def ask(self, question: str) -> dict[str, Any]:
        return self._request("POST", "/api/query", {"question": question})

    def attention(self) -> dict[str, Any]:
        return self._request("GET", "/api/attention")

    def memory(self) -> dict[str, Any]:
        return self._request("GET", "/api/memory")

    def undo(self, capture_ref: str) -> dict[str, Any]:
        return self._request("POST", "/api/undo", {"capture_id": capture_ref})

    def restart(self) -> dict[str, Any]:
        return _unsupported("restart is a human/integration operation, not an HTTP route")

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/health")
