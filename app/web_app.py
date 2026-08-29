"""Minimal local web demo for Blackhole.

The server is intentionally small and local-only. It exposes the deterministic
demo projections and an append-only raw capture endpoint; it does not invoke an
LLM, inspect credentials, or perform consequential actions.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.demo import (
    DEFAULT_DB_PATH,
    answer_question,
    append_capture,
    build_view,
    seed_database,
)


WEB_ROOT = Path(__file__).resolve().parent / "web"
MAX_BODY_BYTES = 1_000_000
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json; charset=utf-8"),
    "/sw.js": ("sw.js", "application/javascript; charset=utf-8"),
    "/icons/icon.svg": ("icons/icon.svg", "image/svg+xml"),
    "/icons/icon-maskable.svg": ("icons/icon-maskable.svg", "image/svg+xml"),
}


class DemoServer(ThreadingHTTPServer):
    """HTTP server carrying the explicitly selected demo database path."""

    daemon_threads = True

    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler], db_path: Path) -> None:
        self.db_path = Path(db_path)
        super().__init__(address, handler)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class DemoRequestHandler(BaseHTTPRequestHandler):
    server_version = "BlackholeDemo/1.0"

    @property
    def db_path(self) -> Path:
        return self.server.db_path  # type: ignore[attr-defined]

    def _send_bytes(self, payload: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, value: Any, status: int = 200) -> None:
        self._send_bytes(_json_bytes(value), "application/json; charset=utf-8", status)

    def _error(self, message: str, status: int = 400) -> None:
        self._send_json({"error": message}, status)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid content length") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request body is too large")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("request body must be valid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("request body must be a JSON object")
        return value

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"ok": True, "demo": True})
            return
        if parsed.path == "/api/state":
            self._send_json({"ok": True, "state": build_view(self.db_path)})
            return
        if parsed.path == "/api/query":
            question = parse_qs(parsed.query).get("q", [""])[0]
            try:
                self._send_json({"ok": True, "answer": answer_question(question, self.db_path)})
            except ValueError as exc:
                self._error(str(exc), 400)
            return
        static = STATIC_FILES.get(parsed.path)
        if static is None:
            self._error("not found", 404)
            return
        filename, content_type = static
        try:
            payload = (WEB_ROOT / filename).read_bytes()
        except OSError:
            self._error("demo assets are unavailable", 500)
            return
        self._send_bytes(payload, content_type)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        try:
            body = self._read_json()
            if parsed.path == "/api/capture":
                text = body.get("text")
                if not isinstance(text, str):
                    raise ValueError("text is required")
                source_type = body.get("source_type", "text")
                filename = body.get("filename")
                if not isinstance(source_type, str):
                    raise ValueError("source_type must be a string")
                if filename is not None and not isinstance(filename, str):
                    raise ValueError("filename must be a string")
                capture = append_capture(
                    text,
                    self.db_path,
                    source_type=source_type,
                    filename=filename,
                )
                self._send_json({"ok": True, "saved": True, "message": "Saved.", "capture": capture})
                return
            if parsed.path == "/api/reset":
                self._send_json({"ok": True, "reset": seed_database(self.db_path)})
                return
            self._error("not found", 404)
        except ValueError as exc:
            self._error(str(exc), 400)
        except Exception:
            # Keep implementation details out of the user-facing demo response.
            self._error("demo request failed", 500)

    def log_message(self, format: str, *args: object) -> None:
        # Keep the terminal useful for the run command rather than request noise.
        return


def create_server(host: str = "127.0.0.1", port: int = 8080, db_path: Path = DEFAULT_DB_PATH) -> DemoServer:
    db_path = Path(db_path)
    if not db_path.exists():
        seed_database(db_path)
    return DemoServer((host, port), DemoRequestHandler, db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Blackhole demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    server = create_server(args.host, args.port, args.db)
    print(f"Blackhole demo running at http://{args.host}:{args.port}")
    print("Captures are stored as immutable raw events; semantic interpretation is not run by this demo.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
