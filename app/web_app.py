"""Local same-origin PWA transport for the Blackhole Host.

The HTTP layer validates requests and maps safe domain responses. HostRuntime
owns persistence, deferred processing, provider selection, and state freshness;
this module never opens the demo database or constructs provider commands.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from app.host import HOST_VERSION, HostRuntime
from app.query_service import answer_question_from_snapshot, build_state_view
from app.runtime_config import RuntimeConfig, resolve_home


WEB_ROOT = Path(__file__).resolve().parent / "web"
MAX_BODY_BYTES = 1_000_000
MAX_CAPTURE_TEXT = 100_000
MAX_QUESTION_LENGTH = 4_000
SUPPORTED_SOURCE_TYPES = frozenset({"text", "image", "document"})
STATIC_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def _is_loopback(host: str) -> bool:
    if host.casefold().rstrip(".") == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _validate_bind(host: str, *, trusted_lan_demo: bool) -> None:
    if not _is_loopback(host) and not trusted_lan_demo:
        raise ValueError(
            "non-loopback bind refused; pass --trusted-lan-demo only on a trusted private network"
        )


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class HostServer(ThreadingHTTPServer):
    """Threaded server carrying only explicit Host construction settings."""

    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        *,
        home: Path,
        database_path: Path | None = None,
        contract: dict[str, Any] | None = None,
        provider: Any = None,
        discovery_fn: Any = None,
        trusted_lan_demo: bool = False,
    ) -> None:
        self.home = resolve_home(home)
        self.database_path = database_path.resolve() if database_path is not None else None
        if self.database_path is not None:
            try:
                self.database_path.relative_to(self.home)
            except ValueError as error:
                raise ValueError("database must remain inside BLACKHOLE_HOME") from error
        self.contract = contract
        self.provider = provider
        self.discovery_fn = discovery_fn
        self.trusted_lan_demo = trusted_lan_demo
        self.request_lock = threading.RLock()
        super().__init__(address, handler)

    def open_runtime(self) -> HostRuntime:
        """Open a request-scoped HostRuntime on the configured Blackhole Home."""

        config = RuntimeConfig.load_or_create(self.home)
        if self.database_path is not None:
            config.database_path = self.database_path
        return HostRuntime(
            config,
            contract=self.contract,
            provider=self.provider,
            discovery_fn=self.discovery_fn,
        )


class HostRequestHandler(BaseHTTPRequestHandler):
    server_version = "BlackholeHost/1.0"

    @property
    def host_server(self) -> HostServer:
        return self.server  # type: ignore[return-value]

    def _send_bytes(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, value: Any, status: int = 200) -> None:
        self._send_bytes(_json_bytes(value), "application/json; charset=utf-8", status)

    def _error(
        self,
        message: str,
        status: int = 400,
        *,
        code: str = "bad_request",
        **extra: Any,
    ) -> None:
        payload: dict[str, Any] = {"ok": False, "code": code, "error": message, "message": message}
        payload.update(extra)
        self._send_json(payload, status)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("invalid content length") from error
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body is too large")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("request body must be valid JSON") from error
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    @staticmethod
    def _limit(value: Any, field: str) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
        return value

    def _static_file(self, request_path: str) -> tuple[Path, str] | None:
        decoded = unquote(request_path)
        if "\x00" in decoded or "\\" in decoded:
            return None
        if decoded == "/":
            decoded = "/index.html"
        if not decoded.startswith("/") or any(part == ".." for part in decoded.split("/")):
            return None
        relative = decoded.lstrip("/")
        candidate = (WEB_ROOT / relative).resolve()
        try:
            candidate.relative_to(WEB_ROOT.resolve())
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        content_type = STATIC_CONTENT_TYPES.get(candidate.suffix.casefold())
        if content_type is None:
            return None
        return candidate, content_type

    def _with_host(self) -> HostRuntime:
        return self.host_server.open_runtime()

    def _state_response(self) -> None:
        with self.host_server.request_lock, self._with_host() as host:
            state = build_state_view(host.snapshot(), contract=host.contract)
        self._send_json({"ok": True, "state": state})

    def _query_response(self, question: Any) -> None:
        if not isinstance(question, str) or not question.strip():
            self._error("question must not be empty", 400, code="invalid_question")
            return
        if len(question) > MAX_QUESTION_LENGTH:
            self._error("question is too long", 400, code="invalid_question")
            return
        with self.host_server.request_lock, self._with_host() as host:
            before = host.processing_status() or {"counts": {}}
            before_pending = int(before.get("counts", {}).get("pending", 0))
            freshness = host.ensure_state_fresh()
            if before_pending and not freshness.get("fresh", False):
                detail = str(freshness.get("error") or "")
                provider_failure = "provider unavailable" in detail.casefold()
                message = (
                    "Blackhole couldn't process new captures yet."
                    if provider_failure
                    else "Blackhole couldn't update its memory yet."
                )
                code = "provider_unavailable" if provider_failure else "processing_failed"
                self._send_json(
                    {
                        "ok": False,
                        "code": "state_not_fresh",
                        "error": message,
                        "message": message,
                        "state_available": True,
                        "failure_code": code,
                        "processing": freshness,
                    },
                    409,
                )
                return
            try:
                answer = answer_question_from_snapshot(
                    question,
                    host.snapshot(),
                    contract=host.contract,
                )
            except ValueError as error:
                self._error(str(error), 400, code="invalid_question")
                return
            except Exception:
                self._error(
                    "Blackhole couldn't answer that yet.",
                    500,
                    code="query_failed",
                    state_available=True,
                )
                return
        self._send_json({"ok": True, "answer": answer, "processing": freshness})

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            # Health is intentionally a process/transport check. It does not
            # open HostRuntime or perform provider discovery on every poll.
            self._send_json({"ok": True, "host": True, "version": HOST_VERSION})
            return
        if parsed.path == "/api/host/status":
            with self.host_server.request_lock, self._with_host() as host:
                self._send_json({"ok": True, "status": host.status()})
            return
        if parsed.path == "/api/processing":
            with self.host_server.request_lock, self._with_host() as host:
                self._send_json({"ok": True, "processing": host.processing_status()})
            return
        if parsed.path == "/api/state":
            self._state_response()
            return
        if parsed.path == "/api/query":
            from urllib.parse import parse_qs

            self._query_response(parse_qs(parsed.query).get("q", [""])[0])
            return
        static = self._static_file(parsed.path)
        if static is None:
            self._error("not found", 404, code="not_found")
            return
        filename, content_type = static
        try:
            self._send_bytes(filename.read_bytes(), content_type)
        except OSError:
            self._error("Host assets are unavailable", 500, code="asset_unavailable")

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        try:
            body = self._read_json()
            if parsed.path == "/api/capture":
                text = body.get("text")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("text is required")
                if len(text) > MAX_CAPTURE_TEXT:
                    raise ValueError("capture text is too long")
                source_type = body.get("source_type", "text")
                filename = body.get("filename")
                if not isinstance(source_type, str) or source_type not in SUPPORTED_SOURCE_TYPES:
                    raise ValueError("source_type must be text, image, or document")
                if filename is not None:
                    if not isinstance(filename, str) or not filename.strip() or len(filename) > 255:
                        raise ValueError("filename must be a non-empty string")
                    if "/" in filename or "\\" in filename or "\x00" in filename:
                        raise ValueError("filename must be a file name")
                metadata = {"filename": filename} if filename else None
                with self.host_server.request_lock, self._with_host() as host:
                    capture = host.capture(text, source_type=source_type, metadata=metadata)
                    processing = host.processing_status(capture["event_id"])
                self._send_json(
                    {
                        "ok": True,
                        "saved": True,
                        "message": "Saved.",
                        "capture": {
                            "event_id": capture["event_id"],
                            "sequence": capture["sequence"],
                        },
                        "processing": {"status": (processing or {}).get("status", "pending")},
                    }
                )
                return
            if parsed.path == "/api/process":
                limit = self._limit(body.get("limit"), "limit")
                with self.host_server.request_lock, self._with_host() as host:
                    result = host.process_pending(limit=limit)
                self._processing_result(result)
                return
            if parsed.path == "/api/retry":
                event_id = body.get("event_id")
                if event_id is not None and (not isinstance(event_id, str) or not event_id.strip()):
                    raise ValueError("event_id must be a non-empty string")
                limit = self._limit(body.get("limit"), "limit")
                with self.host_server.request_lock, self._with_host() as host:
                    result = host.retry_failed(event_id, limit=limit)
                self._processing_result(result)
                return
            if parsed.path == "/api/query":
                self._query_response(body.get("question"))
                return
            self._error("not found", 404, code="not_found")
        except ValueError as error:
            self._error(str(error), 400, code="invalid_request")
        except Exception:
            # HostRuntime and its provider wrapper already redact domain
            # failures. Keep transport failures equally implementation-free.
            self._error("Host request failed", 500, code="host_failure")

    def _processing_result(self, result: dict[str, Any]) -> None:
        failed = bool(result.get("failed") or result.get("failed_count"))
        if not failed:
            self._send_json({"ok": True, "processing": result})
            return
        detail = str(result.get("error") or "")
        code = "provider_unavailable" if "provider unavailable" in detail.casefold() else "processing_failed"
        message = (
            "Blackhole couldn't process new captures yet."
            if code == "provider_unavailable"
            else "Blackhole couldn't update its memory yet."
        )
        self._send_json(
            {
                "ok": False,
                "code": code,
                "error": message,
                "message": message,
                "processing": result,
            },
            503 if code == "provider_unavailable" else 500,
        )

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    db_path: Path | None = None,
    *,
    home: str | Path | None = None,
    contract: dict[str, Any] | None = None,
    provider: Any = None,
    discovery_fn: Any = None,
    trusted_lan_demo: bool = False,
) -> HostServer:
    """Create a Host-backed server without seeding or provider work."""

    _validate_bind(host, trusted_lan_demo=trusted_lan_demo)
    if db_path is not None and home is not None:
        raise ValueError("pass home or db_path, not both")
    if db_path is not None:
        database_path = Path(db_path).expanduser().resolve()
        resolved_home = database_path.parent
    else:
        resolved_home = resolve_home(home)
        database_path = None
    return HostServer(
        (host, port),
        HostRequestHandler,
        home=resolved_home,
        database_path=database_path,
        contract=contract,
        provider=provider,
        discovery_fn=discovery_fn,
        trusted_lan_demo=trusted_lan_demo,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local Blackhole Host PWA.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--home", type=Path, help="Blackhole data directory (or use BLACKHOLE_HOME)")
    parser.add_argument(
        "--trusted-lan-demo",
        action="store_true",
        help="explicitly allow a non-loopback bind on a trusted private hackathon network",
    )
    args = parser.parse_args(argv)
    try:
        server = create_server(
            args.host,
            args.port,
            home=args.home,
            trusted_lan_demo=args.trusted_lan_demo,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
        return 2
    print(f"Blackhole Host running at http://{args.host}:{args.port}")
    print(f"Blackhole Home: {server.home}")
    if not _is_loopback(args.host):
        print("WARNING: trusted-LAN demo has no device authentication; use only on a trusted private network, never the public Internet or a tunnel.")
    print("Capture saves raw evidence immediately; Ask may process pending captures through the local Codex CLI.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["HostRequestHandler", "HostServer", "create_server", "main"]
