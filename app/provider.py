"""Subscription-first Codex CLI calls for advanced experiments."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from baseline.run_baseline import (
    REASONING_EFFORT,
    base_command,
    output_text,
    parse_json_document,
    run_cli,
)


DEFAULT_PROVIDER_MODEL = "gpt-5.6-luna"


def parse_repaired_json(raw_text: str) -> tuple[dict[str, Any] | None, str | None, str | None]:
    """Parse JSON and repair only a small, unambiguous closing-delimiter truncation."""

    parsed, parse_error = parse_json_document(raw_text)
    if parsed is not None:
        return parsed, None, None
    stripped = raw_text.strip()
    if not stripped.startswith("{"):
        return None, parse_error, None
    for suffix in ("}", "]}", "}}", "]}}", "}}}"):
        try:
            candidate = json.loads(stripped + suffix)
        except (TypeError, ValueError):
            continue
        if isinstance(candidate, dict):
            return candidate, None, f"appended_suffix:{suffix}"
    return None, parse_error, None


def structured_call(
    prompt: str,
    *,
    temp_workspace: Path,
    output_path: Path,
    timeout: int,
    model: str = DEFAULT_PROVIDER_MODEL,
    reasoning_effort: str = REASONING_EFFORT,
) -> dict[str, Any]:
    """Run one fresh read-only CLI call and return parsed output plus metadata."""

    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be a non-empty string")
    cli = shutil.which("codex")
    if not cli:
        raise RuntimeError("codex CLI was not found on PATH")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = base_command(cli, temp_workspace)
    command[command.index("--model") + 1] = model
    command[command.index("-c") + 1] = f"model_reasoning_effort={reasoning_effort}"
    result = run_cli(
        command + ["-o", str(output_path), "-"],
        prompt,
        timeout,
    )
    raw_text = output_text(result, output_path)
    parsed, parse_error, parse_repair = parse_repaired_json(raw_text)
    return {
        "parsed": parsed,
        "parse_error": parse_error,
        "raw_text": raw_text,
        "provider": {
            "returncode": result.get("returncode"),
            "duration_seconds": result.get("duration_seconds"),
            "thread_id": result.get("thread_id"),
            "usage": result.get("usage"),
            "stderr": result.get("stderr"),
            "model": model,
            "reasoning_effort": reasoning_effort,
            "parse_repair": parse_repair,
        },
}


__all__ = ["DEFAULT_PROVIDER_MODEL", "parse_repaired_json", "structured_call"]
