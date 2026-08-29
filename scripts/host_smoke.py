"""Run a neutral real HTTP/Host/Codex smoke and emit a safe JSON trace."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from threading import Thread
from typing import Any

from app.web_app import create_server


def request_json(base_url: str, path: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method=method,
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=1_800) as response:
            payload = json.loads(response.read().decode("utf-8"))
            status = response.status
    except urllib.error.HTTPError as error:
        with error:
            payload = json.loads(error.read().decode("utf-8"))
            status = error.code
    return {"status": status, "duration_seconds": round(time.perf_counter() - started, 3), "payload": payload}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--home", type=Path)
    args = parser.parse_args()
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if args.home is None:
        temporary = tempfile.TemporaryDirectory(prefix="blackhole-neutral-smoke-")
        home = Path(temporary.name)
    else:
        home = args.home
        home.mkdir(parents=True, exist_ok=True)

    server = create_server("127.0.0.1", 0, home=home)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    captures = [
        "Northstar Cloud costs 18 EUR per month.",
        "Northstar Cloud will cost 22 EUR per month from 2027-03-01.",
    ]
    try:
        health = request_json(base_url, "/api/health")
        host_status_before = request_json(base_url, "/api/host/status")
        capture_steps = []
        for text in captures:
            capture_steps.append(
                {
                    "request": {"path": "/api/capture", "method": "POST", "body": {"text": text}},
                    "response": request_json(base_url, "/api/capture", method="POST", body={"text": text}),
                }
            )
        ask_question = "What subscription price changes do I know?"
        trace: dict[str, Any] = {
            "kind": "neutral-real-host-pwa-equivalent-smoke",
            "home": str(home),
            "base_url": base_url,
            "provider_usage": "not exposed by the safe HTTP transport",
            "health": health,
            "host_status_before": host_status_before,
            "captures": capture_steps,
            "processing_before_ask": request_json(base_url, "/api/processing"),
        }
        trace["ask"] = {
            "request": {"path": "/api/query", "method": "POST", "body": {"question": ask_question}},
            "response": request_json(base_url, "/api/query", method="POST", body={"question": ask_question}),
        }
        trace["state_after_ask"] = request_json(base_url, "/api/state")
        trace["processing_after_ask"] = request_json(base_url, "/api/processing")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        server.shutdown()
        thread.join(timeout=10)
        server.server_close()
        if temporary is not None:
            temporary.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
