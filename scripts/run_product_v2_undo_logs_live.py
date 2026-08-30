"""Run the bounded Product V2 permanent-Undo and operational-log live smoke.

This runner uses the normal web launcher with a fresh BLACKHOLE_HOME. It is a
non-scored product smoke only: three prescribed captures, one immediate Undo,
two prescribed Ask requests, and no manual processing or retry request.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


RESULT_PATH = ROOT / "trajectories" / "coding" / "041-product-v2-undo-and-ops-logs" / "live-validation.json"
BASE_SHA = "05c337b46798031adea8ee0f1cf6b34b40572bc1"
CAPTURE_TEXTS = [
    "Klucze do piwnicy są u mamy.",
    "To jest informacja którą zaraz usunę przez Undo.",
    "Odbieram dzieci za 10 minut.",
]
ASK_QUESTIONS = [
    "Gdzie są klucze do piwnicy?",
    "Co mam niedługo do zrobienia?",
]
POLL_SECONDS = 300


def http_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    data = None
    headers: dict[str, str] = {}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(base_url + path, data=data, method=method, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            status = response.status
    except HTTPError as error:
        with error:
            raw = error.read()
            status = error.code
    except (URLError, OSError) as error:
        return 0, {"ok": False, "error_type": type(error).__name__}
    try:
        value = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, {"ok": False, "error_type": "invalid_json"}
    return status, value if isinstance(value, dict) else {"payload": value}


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def processing_summary(payload: dict[str, object]) -> dict[str, object]:
    value = payload.get("processing")
    return value if isinstance(value, dict) else {}


def state_summary(payload: dict[str, object]) -> dict[str, object]:
    state = payload.get("state")
    if not isinstance(state, dict):
        return {"valid": False}
    sources = state.get("sources")
    source_ids = [
        str(item.get("event_id"))
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("event_id"), str)
    ] if isinstance(sources, list) else []
    attention = state.get("attention")
    attention_items = [
        {
            "kind": item.get("kind"),
            "title": item.get("title"),
            "source_refs": item.get("source_refs", []),
            "state": item.get("state"),
        }
        for item in attention
        if isinstance(item, dict)
    ] if isinstance(attention, list) else []
    current_facts = state.get("current_facts")
    fact_history = state.get("fact_history")
    return {
        "valid": True,
        "source_event_ids": source_ids,
        "current_fact_count": len(current_facts) if isinstance(current_facts, list) else 0,
        "fact_history_count": len(fact_history) if isinstance(fact_history, list) else 0,
        "attention": attention_items,
        "retracted_event_ids": state.get("retracted_event_ids", []),
    }


def run() -> dict[str, object]:
    started_at = datetime.now(timezone.utc).isoformat()
    port = free_port()
    capture_ids = ["live-keys", "live-undo", "live-children"]
    process: subprocess.Popen[str] | None = None
    output_lines: list[str] = []
    reader: threading.Thread | None = None
    captures: list[dict[str, object]] = []
    undo: dict[str, object] = {}
    asks: list[dict[str, object]] = []
    processing: dict[str, object] = {}
    final_state: dict[str, object] = {}
    launch_error: str | None = None

    with tempfile.TemporaryDirectory(prefix="blackhole-product-v2-undo-live-") as directory:
        home = Path(directory) / "home"
        environment = os.environ.copy()
        environment["BLACKHOLE_HOME"] = str(home)
        environment.setdefault("BLACKHOLE_LOG_LEVEL", "info")
        command = [
            sys.executable,
            "-m",
            "app.web_app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        try:
            process = subprocess.Popen(
                command,
                cwd=str(ROOT),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )

            def read_output() -> None:
                if process is None or process.stdout is None:
                    return
                for line in process.stdout:
                    output_lines.append(line.rstrip("\r\n"))

            reader = threading.Thread(target=read_output, name="live-log-reader", daemon=True)
            reader.start()
            base_url = f"http://127.0.0.1:{port}"
            ready = False
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    launch_error = f"web launcher exited with code {process.returncode}"
                    break
                status, health = http_json(base_url, "/api/health")
                if status == 200 and bool(health.get("ok")):
                    ready = True
                    break
                time.sleep(0.25)
            if not ready:
                launch_error = launch_error or "web launcher did not become ready"
            else:
                for event_id, text in zip(capture_ids, CAPTURE_TEXTS):
                    status, response = http_json(
                        base_url,
                        "/api/v2/capture",
                        method="POST",
                        body={"event_id": event_id, "text": text},
                    )
                    capture = response.get("capture") if isinstance(response.get("capture"), dict) else {}
                    captures.append(
                        {
                            "http_status": status,
                            "saved": bool(response.get("saved")),
                            "event_id": capture.get("event_id", event_id),
                            "processing_status": (
                                response.get("processing", {}).get("status")
                                if isinstance(response.get("processing"), dict)
                                else None
                            ),
                        }
                    )
                    if event_id == "live-undo":
                        undo_status, undo_response = http_json(
                            base_url,
                            "/api/v2/retract",
                            method="POST",
                            body={"event_id": event_id},
                        )
                        undo_value = undo_response.get("retraction")
                        undo = dict(undo_value) if isinstance(undo_value, dict) else {}
                        undo["http_status"] = undo_status

                deadline = time.monotonic() + POLL_SECONDS
                while time.monotonic() < deadline:
                    status, payload = http_json(base_url, "/api/v2/processing")
                    if status == 200:
                        processing = processing_summary(payload)
                        counts = processing.get("counts")
                        if isinstance(counts, dict) and all(
                            int(counts.get(key, 0) or 0) == 0 for key in ("pending", "processing", "failed")
                        ):
                            break
                    time.sleep(0.5)

                for question in ASK_QUESTIONS:
                    status, response = http_json(
                        base_url,
                        "/api/v2/ask",
                        method="POST",
                        body={"question": question},
                    )
                    answer = response.get("answer") if isinstance(response.get("answer"), dict) else {}
                    asks.append(
                        {
                            "http_status": status,
                            "question": question,
                            "mode": answer.get("mode"),
                            "status": answer.get("status"),
                            "answer": answer.get("answer"),
                            "source_refs": answer.get("source_refs", []),
                            "provider_used": answer.get("provider_used"),
                        }
                    )
                state_status, state_payload = http_json(base_url, "/api/v2/state")
                final_state = state_summary(state_payload)
                final_state["http_status"] = state_status
        except (OSError, ValueError) as error:
            launch_error = str(error)
        finally:
            if process is not None and process.poll() is None:
                try:
                    if os.name == "nt":
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        process.send_signal(signal.SIGINT)
                    process.wait(timeout=10)
                except (OSError, subprocess.TimeoutExpired):
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
            if reader is not None:
                reader.join(timeout=10)

    log_text = "\n".join(output_lines)
    required_log_fragments = [
        "[startup] product-v2 ready",
        "[web] listening",
        "[worker] product-v2 worker started",
        "[capture] saved",
        "[queue] pending",
        "[provider] start",
        "[provider] complete",
        "[memory] updated",
        "[attention] updated",
        "[undo] requested",
        "[undo] deleted",
        "[ask] start",
        "[ask] path",
        "[ask] sources",
        "[ask] complete",
        "[worker] product-v2 worker stopped",
        "[web] server stopped",
    ]
    log_checks = {
        "required_fragments": {fragment: fragment in log_text for fragment in required_log_fragments},
        "capture_text_absent": all(text not in log_text for text in CAPTURE_TEXTS),
        "uncontrolled_retry_count": log_text.count("retry scheduled"),
        "line_count": len(output_lines),
        "max_line_length": max((len(line) for line in output_lines), default=0),
        "examples": output_lines[:40],
    }
    counts = processing.get("counts") if isinstance(processing.get("counts"), dict) else {}
    source_ids = final_state.get("source_event_ids", [])
    attention = final_state.get("attention", [])
    attention_text = json.dumps(attention, ensure_ascii=False)
    structural_ok = (
        launch_error is None
        and len(captures) == 3
        and all(item["http_status"] == 200 and item["saved"] for item in captures)
        and undo.get("http_status") == 200
        and bool(undo.get("forgotten"))
        and bool(undo.get("deleted"))
        and counts.get("processed") == 2
        and counts.get("failed", 0) == 0
        and len(asks) == 2
        and all(item["http_status"] == 200 for item in asks)
        and final_state.get("http_status") == 200
        and "live-keys" in source_ids
        and "live-children" in source_ids
        and "live-undo" not in source_ids
        and "live-undo" not in json.dumps(final_state, ensure_ascii=False)
        and "dzieci" in attention_text.casefold()
        and all(log_checks["required_fragments"].values())
        and bool(log_checks["capture_text_absent"])
        and log_checks["uncontrolled_retry_count"] == 0
        and log_checks["max_line_length"] < 600
    )
    result: dict[str, object] = {
        "run_type": "product-v2-undo-and-ops-logs-live-smoke",
        "scope": "authorized post-freeze product smoke; non-scored",
        "base_sha": BASE_SHA,
        "launcher": "python -m app.web_app",
        "home_is_fresh_temp": True,
        "manual_processing_or_retry_used": False,
        "capture_limit": 3,
        "ask_limit": 2,
        "captures": captures,
        "undo": undo,
        "processing": processing,
        "asks": asks,
        "state": final_state,
        "logs": log_checks,
        "launch_error": launch_error,
        "structural_ok": structural_ok,
        "provider_tokens_read_or_persisted": False,
        "benchmark_oracle_accessed": False,
        "holdout_accessed": False,
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    report = run()
    raise SystemExit(0 if report.get("structural_ok") else 1)
