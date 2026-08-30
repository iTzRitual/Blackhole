"""Backend-only Product V2 queue utility.

This command is intentionally separate from ``app.process_pending`` so the
frozen V1/deferred-ingestion command remains reproducible and Product V2 can
evolve its open-world schema independently.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.codex_discovery import discover_codex
from app.product_v2 import PRODUCT_RUNTIME_VERSION, ProductRuntime, product_database_path
from app.runtime_config import RuntimeConfig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Process the Blackhole Product V2 queue.")
    parser.add_argument("--home", type=Path, help="Blackhole Home (or use BLACKHOLE_HOME)")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--event-id")
    parser.add_argument("command", choices=("init", "status", "process", "retry"))
    args = parser.parse_args(argv)
    try:
        config = RuntimeConfig.load_or_create(args.home)
        with ProductRuntime(
            config.home,
            db_path=product_database_path(config.home),
            discovery_fn=discover_codex,
            model=config.model,
            reasoning_effort=config.reasoning_effort,
            timeout_seconds=config.timeout_seconds,
            batch_size=config.batch_size,
            start_worker=False,
        ) as runtime:
            if args.command == "init":
                result = {
                    "runtime": PRODUCT_RUNTIME_VERSION,
                    "home": str(config.home),
                    "database": str(runtime.store.path),
                    "processing": runtime.processing_status(),
                }
            elif args.command == "status":
                result = {
                    "runtime": PRODUCT_RUNTIME_VERSION,
                    "home": str(config.home),
                    "database": str(runtime.store.path),
                    "processing": runtime.processing_status() or {"counts": {}},
                }
            elif args.command == "process":
                result = runtime.process_pending(limit=args.limit)
            else:
                result = runtime.retry_failed(args.event_id, limit=args.limit)
        if args.json_output or args.command in {"status", "init"}:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"Product V2: {result.get('processed', 0)} processed")
            if result.get("failed") or result.get("failed_count"):
                print("retryable processing failures remain")
        return 1 if result.get("failed") or result.get("failed_count") else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Blackhole Product V2 error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
