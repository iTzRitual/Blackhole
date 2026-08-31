"""Prepare a persistent, synthetic Product V2 Home for a live demo.

The utility uses the normal Product V2 HTTP capture and processing routes with
the repository's visible deterministic acceptance provider. It is a demo
preparation aid, not a provider-quality or benchmark run. It refuses to reuse
a non-empty Home so it cannot silently mix synthetic demo state with a user's
local data.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.web_app import create_server
from scripts.run_product_v2_integrated_acceptance import DeterministicAcceptanceProvider


DEMO_NOW = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
DEMO_CAPTURES: tuple[dict[str, Any], ...] = (
    {
        "event_id": "demo-parking-permit",
        "captured_at": "2026-08-30T08:40:00+00:00",
        "timezone": "UTC",
        "source_type": "text",
        "text": "Please remind me to renew the parking permit by September 12.",
    },
    {
        "event_id": "demo-keys-old",
        "captured_at": "2026-08-30T09:00:00+00:00",
        "timezone": "UTC",
        "source_type": "text",
        "text": "The basement keys are at Mum's house.",
    },
    {
        "event_id": "demo-keys-corrected",
        "captured_at": "2026-08-30T09:30:00+00:00",
        "timezone": "UTC",
        "source_type": "text",
        "text": "Actually, I found the basement keys in my desk.",
    },
    {
        "event_id": "demo-pocketwave-old",
        "captured_at": "2026-08-20T09:00:00+01:00",
        "timezone": "Europe/London",
        "source_type": "text",
        "text": "PocketWave costs 9 EUR monthly.",
    },
    {
        "event_id": "demo-pocketwave-new",
        "captured_at": "2026-09-01T09:00:00+01:00",
        "timezone": "Europe/London",
        "source_type": "text",
        "text": "PocketWave will cost 11 EUR from September 1.",
    },
    {
        "event_id": "demo-kuba-preference",
        "captured_at": "2026-08-30T12:15:00+02:00",
        "timezone": "Europe/Warsaw",
        "source_type": "text",
        "text": "Kuba lubi ten zielony makaron z Lidla.",
    },
    {
        "event_id": "demo-boiler-warranty",
        "captured_at": "2026-08-30T13:00:00+00:00",
        "timezone": "UTC",
        "source_type": "text",
        "text": "I think the boiler warranty might expire in December, not sure.",
    },
)


def _request(base_url: str, route: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{base_url}{route}",
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method=method,
    )
    with urlopen(request, timeout=10) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"unexpected response for {route}")
    return value


def _new_home(requested: Path | None) -> Path:
    if requested is None:
        return Path(tempfile.mkdtemp(prefix="blackhole-product-v2-demo-"))
    home = requested.expanduser().resolve()
    if home.exists() and any(home.iterdir()):
        raise ValueError(f"demo Home must be new or empty: {home}")
    home.mkdir(parents=True, exist_ok=True)
    return home


def _count(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a synthetic Product V2 demo Home.")
    parser.add_argument(
        "--home",
        type=Path,
        help="new or empty Home to populate; omit to create a temporary Home",
    )
    args = parser.parse_args(argv)
    home = _new_home(args.home)
    provider = DeterministicAcceptanceProvider()
    server = create_server(
        "127.0.0.1",
        0,
        home=home,
        provider=provider,
        clock=lambda: DEMO_NOW,
        auto_start_product_worker=False,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        health = _request(base_url, "/api/health")
        if not health.get("ok"):
            raise RuntimeError("Product V2 demo Host did not become ready")
        for capture in DEMO_CAPTURES:
            response = _request(base_url, "/api/v2/capture", method="POST", payload=capture)
            if not response.get("saved"):
                raise RuntimeError(f"demo capture was not saved: {capture['event_id']}")
        processed = _request(base_url, "/api/v2/process", method="POST", payload={})
        if not processed.get("ok"):
            raise RuntimeError("demo processing did not complete")
        state_response = _request(base_url, "/api/v2/state")
        state = state_response.get("state") if isinstance(state_response.get("state"), dict) else {}
        print(
            json.dumps(
                {
                    "home": str(home),
                    "database": str(home / "blackhole-v2.db"),
                    "capture_count": len(DEMO_CAPTURES),
                    "processed_count": processed.get("processing", {}).get("processed", 0),
                    "attention_items": _count(state.get("attention")),
                    "memory_entities": _count(state.get("entities")),
                    "provider_calls": provider.calls,
                    "provider": "deterministic acceptance fixture; no live provider",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
