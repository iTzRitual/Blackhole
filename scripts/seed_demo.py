"""Seed or reset the deterministic local Blackhole demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.demo import DEFAULT_DB_PATH, seed_database  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the local Blackhole demo database.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite path for the demo state.")
    parser.add_argument("--reset", action="store_true", help="Replace an existing demo database with the seed.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if db_path.exists() and not args.reset:
        print(f"Refusing to replace existing demo database: {db_path}. Re-run with --reset.", file=sys.stderr)
        return 2
    result = seed_database(db_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
