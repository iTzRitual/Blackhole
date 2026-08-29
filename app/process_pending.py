"""Process deferred Blackhole captures from a local SQLite database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.ingestion_engine import CodexCLIProvider, IngestionEngine
from app.state_store import StateStore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data" / "runtime" / "state.sqlite"
DEFAULT_CONTRACT = ROOT / "benchmark" / "dev" / "response-contract-v2.json"


def _load_contract(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("response contract must be a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--response-contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--semantic-reasoning", choices=["max", "high", "medium"], default="max")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    with StateStore(args.db) as store:
        before = store.processing_status() or {"counts": {}}
        counts = before.get("counts", {})
        pending_before = int(counts.get("pending", 0))
        failed_before = int(counts.get("failed", 0))
        needs_provider = pending_before > 0 or (args.retry_failed and failed_before > 0)
        if not needs_provider:
            print("Blackhole")
            print(f"{pending_before} pending captures")
            print("0 processed")
            if failed_before:
                print(f"{failed_before} failed captures remain; retry is available")
                return 1
            print("state already fresh")
            return 0

        contract = _load_contract(args.response_contract)
        with CodexCLIProvider(timeout=args.timeout, reasoning_effort=args.semantic_reasoning) as provider:
            with IngestionEngine(
                contract=contract,
                provider=provider,
                store=store,
                batch_size=args.batch_size,
            ) as engine:
                result = engine.process_pending(limit=args.limit)
                if args.retry_failed and (store.processing_status() or {"counts": {}}).get("counts", {}).get("failed", 0):
                    retry_result = engine.retry_failed(limit=args.limit)
                    result["processed"] = int(result.get("processed", 0)) + int(retry_result.get("processed", 0))
                    result["failed"] = int(retry_result.get("failed", 0))
                    result["state_rebuilt"] = bool(result.get("state_rebuilt")) or bool(retry_result.get("state_rebuilt"))
                    if not retry_result.get("failed") and not retry_result.get("blocked"):
                        remaining = engine.process_pending(limit=args.limit)
                        result["processed"] = int(result.get("processed", 0)) + int(remaining.get("processed", 0))
                        result["failed"] = int(remaining.get("failed", 0))
                        result["state_rebuilt"] = bool(result.get("state_rebuilt")) or bool(remaining.get("state_rebuilt"))
                final_status = store.processing_status() or {"counts": {}}
                result["pending_count"] = final_status.get("counts", {}).get("pending", 0)
                result["failed_count"] = final_status.get("counts", {}).get("failed", 0)

        print("Blackhole")
        print(f"{pending_before} pending captures")
        print(f"{int(result.get('processed', 0))} processed")
        if result.get("failed"):
            print(f"{int(result['failed'])} failed captures; retry is available")
            return 1
        if result.get("failed_count"):
            print(f"{int(result['failed_count'])} failed captures remain; retry is available")
            return 1
        if result.get("pending_count"):
            print(f"{int(result['pending_count'])} pending captures remain")
        print("state rebuilt" if result.get("state_rebuilt") else "state already fresh")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
