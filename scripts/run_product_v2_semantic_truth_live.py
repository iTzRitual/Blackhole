"""Run the bounded, non-scored Product V2 semantic-truth live smoke.

The source file is UTF-8 so the prescribed Polish/German mixed-language
sequence reaches the normal Host HTTP lifecycle without shell-pipe recoding.
The runner never calls the manual processing endpoint and records only safe,
user-visible results and structured state.
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.web_app import create_server


RESULT_PATH = ROOT / "trajectories" / "coding" / "040-product-v2-semantic-truth" / "live-validation.json"
BASE_SHA = "7a76a1b660b49d28cb5aa29ab9e9b5099238aaee"
CAPTURES = [
    "Klucze do piwnicy są u mamy.",
    "Jednak znalazłem klucze w szufladzie biurka.",
    "PocketWave kosztuje 9 EUR miesięcznie.",
    "Od 1 września PocketWave będzie kosztować 11 EUR miesięcznie.",
    "Chyba gwarancja na bojler kończy się w grudniu.",
    "Mechanik mówi, że stukanie może powodować lewe łożysko.",
    "Drugi mechanik mówi, że lewe łożysko jest okej i podejrzewa oponę.",
    "Spotkanie z Markiem jest we wtorek o 14:00.",
    "Meeting z Markiem moved to Donnerstag 16:00.",
    "Muszę odnowić pozwolenie parkingowe do piątku.",
]
ASKS = [
    "Gdzie są teraz klucze do piwnicy?",
    "Gdzie wcześniej były klucze?",
    "Ile kosztuje PocketWave i czy cena się zmieniała?",
    "Kiedy kończy się gwarancja na bojler?",
    "Co może powodować stukanie w samochodzie?",
    "Kiedy mam spotkanie z Markiem?",
    "What changed about my meeting with Marek?",
    "Was weißt du über die Kellerschlüssel?",
]
BASE_CAPTURE = datetime.fromisoformat("2026-08-30T10:00:00+02:00")


def http_json(base_url: str, path: str, method: str = "GET", body: dict[str, object] | None = None) -> tuple[int, dict[str, object]]:
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
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {"ok": False, "error_type": "invalid_json"}
    return status, payload if isinstance(payload, dict) else {"payload": payload}


def summarize_item(item: object) -> dict[str, object]:
    if not isinstance(item, dict):
        return {"type": type(item).__name__}
    keys = (
        "entity_key", "entity_label", "concept", "value", "knowledge_status",
        "source_refs", "status", "title", "kind", "starts_at", "due_at",
        "state", "negated", "attribution", "semantic_relation", "temporal",
        "metadata", "details",
    )
    return {key: item[key] for key in keys if key in item}


def run() -> dict[str, object]:
    started_at = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="blackhole-v2-semantic-truth-live-") as home_dir:
        server = create_server("127.0.0.1", 0, home=Path(home_dir), auto_start_product_worker=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        captures: list[dict[str, object]] = []
        asks: list[dict[str, object]] = []
        processing: dict[str, object] = {}
        attention: list[dict[str, object]] = []
        try:
            health_status, health = http_json(base_url, "/api/health")
            for index, text in enumerate(CAPTURES, start=1):
                captured_at = (BASE_CAPTURE + timedelta(minutes=index - 1)).isoformat()
                status, payload = http_json(
                    base_url,
                    "/api/v2/capture",
                    method="POST",
                    body={
                        "event_id": f"semantic-live-utf8-{index:02d}",
                        "text": text,
                        "captured_at": captured_at,
                        "timezone": "Europe/Berlin",
                    },
                )
                capture = payload.get("capture") if isinstance(payload.get("capture"), dict) else {}
                captures.append(
                    {
                        "index": index,
                        "text": text,
                        "http_status": status,
                        "ok": bool(payload.get("ok")),
                        "saved": bool(payload.get("saved")),
                        "event_id": capture.get("event_id"),
                        "processing_status": (
                            payload.get("processing", {}).get("status")
                            if isinstance(payload.get("processing"), dict)
                            else None
                        ),
                    }
                )

            deadline = time.monotonic() + 900
            while True:
                status, payload = http_json(base_url, "/api/v2/processing")
                processing = payload.get("processing") if isinstance(payload.get("processing"), dict) else {}
                counts = processing.get("counts") if isinstance(processing.get("counts"), dict) else {}
                if int(counts.get("pending", 0) or 0) == 0 and int(counts.get("processing", 0) or 0) == 0:
                    break
                if time.monotonic() >= deadline:
                    processing = {"timeout": True, "http_status": status, "counts": counts}
                    break
                time.sleep(2)

            counts = processing.get("counts") if isinstance(processing.get("counts"), dict) else {}
            event_summaries = [
                {
                    "event_id": event.get("event_id"),
                    "status": event.get("status"),
                    "attempt_count": event.get("attempt_count"),
                    "last_error": event.get("last_error"),
                }
                for event in processing.get("events", [])
                if isinstance(event, dict)
            ] if isinstance(processing.get("events"), list) else []
            provider_retries = sum(
                max(int(event.get("attempt_count", 0) or 0) - 1, 0)
                for event in event_summaries
            )

            for question in ASKS:
                status, payload = http_json(
                    base_url,
                    "/api/v2/ask",
                    method="POST",
                    body={"question": question},
                )
                answer = payload.get("answer") if isinstance(payload.get("answer"), dict) else {}
                asks.append(
                    {
                        "question": question,
                        "http_status": status,
                        "ok": bool(payload.get("ok")),
                        "mode": answer.get("mode"),
                        "status": answer.get("status"),
                        "answer": answer.get("answer"),
                        "provider_used": answer.get("provider_used"),
                        "source_refs": answer.get("source_refs", []),
                        "items": [summarize_item(item) for item in answer.get("items", [])]
                        if isinstance(answer.get("items"), list)
                        else [],
                    }
                )

            state_status, state_payload = http_json(base_url, "/api/v2/state")
            state = state_payload.get("state") if isinstance(state_payload.get("state"), dict) else {}
            attention = [summarize_item(item) for item in state.get("attention", [])] if isinstance(state.get("attention"), list) else []
            current_facts = state.get("current_facts") if isinstance(state.get("current_facts"), list) else []
            history = state.get("fact_history") if isinstance(state.get("fact_history"), list) else []
            structural_ok = (
                health_status == 200
                and bool(health.get("ok"))
                and len(captures) == 10
                and all(item["http_status"] == 200 and item["saved"] for item in captures)
                and int(counts.get("processed", 0) or 0) == 10
                and int(counts.get("failed", 0) or 0) == 0
                and len(asks) == 8
                and all(item["http_status"] == 200 for item in asks)
                and state_status == 200
                and bool(state_payload.get("ok"))
            )
            result: dict[str, object] = {
                "run_type": "product-v2-semantic-truth-live-smoke",
                "scope": "authorized post-freeze product generalization; non-scored",
                "base_sha": BASE_SHA,
                "encoding": "UTF-8 source file and UTF-8 HTTP JSON bodies",
                "host_lifecycle": "normal create_server HTTP lifecycle with auto_start_product_worker=true",
                "manual_processing_endpoint_used": False,
                "capture_limit": 10,
                "ask_limit": 8,
                "health": {"http_status": health_status, "ok": bool(health.get("ok"))},
                "captures": captures,
                "processing": {"counts": counts, "events": event_summaries, "provider_retries": provider_retries},
                "asks": asks,
                "attention": {
                    "http_status": state_status,
                    "items": attention,
                    "current_fact_count": len(current_facts),
                    "fact_history_count": len(history),
                },
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
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


if __name__ == "__main__":
    report = run()
    raise SystemExit(0 if report.get("structural_ok") else 1)
