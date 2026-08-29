"""Run the approved Codex CLI long-chat baseline on the public DEV case.

The runner intentionally knows only about the public scenario, the frozen
baseline prompt, and the public query bundle.  It never imports the generator,
expected output, or evaluator.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = ROOT / "benchmark" / "dev" / "cases" / "scenario-001.json"
DEFAULT_PROMPT = ROOT / "prompts" / "runtime" / "baseline-v1.md"
DEFAULT_RUNNER_PROMPT = ROOT / "prompts" / "runtime" / "baseline-runner-v2.md"
DEFAULT_QUERY_BUNDLE = ROOT / "benchmark" / "dev" / "query-bundle-v2.json"
DEFAULT_RESPONSE_CONTRACT = ROOT / "benchmark" / "dev" / "response-contract-v2.json"
DEFAULT_OUTPUT = ROOT / "eval" / "results" / "baseline-v1-candidate.json"
DEFAULT_TRAJECTORY = ROOT / "trajectories" / "runtime" / "003-baseline-v1"
MODEL = "gpt-5.6-luna"
REASONING_EFFORT = "max"
DEFAULT_TIMEOUT_SECONDS = 900


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def command_jsonl(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def thread_id_from(events: list[dict[str, Any]]) -> str | None:
    for event in events:
        if event.get("type") == "thread.started" and event.get("thread_id"):
            return str(event["thread_id"])
    return None


def usage_from(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage")
        if isinstance(usage, dict):
            return usage
        info = event.get("info")
        if isinstance(info, dict) and isinstance(info.get("usage"), dict):
            return info["usage"]
    return None


def stderr_summary(stderr: str) -> dict[str, Any]:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    return {
        "line_count": len(lines),
        "last_lines": lines[-5:],
    }


def run_cli(command: list[str], prompt: str | None, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            # Codex validates stdin as UTF-8.  Explicit bytes avoid the
            # Windows console code page changing non-ASCII synthetic text.
            input=prompt.encode("utf-8") if prompt is not None else None,
            text=False,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout = (completed.stdout or b"").decode("utf-8", errors="replace")
        stderr = (completed.stderr or b"").decode("utf-8", errors="replace")
        events = command_jsonl(stdout)
        return {
            "returncode": completed.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "events": events,
            "thread_id": thread_id_from(events),
            "usage": usage_from(events),
            "stderr": stderr_summary(stderr),
        }
    except subprocess.TimeoutExpired as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "returncode": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "events": [],
            "thread_id": None,
            "usage": None,
            "stderr": stderr_summary(stderr),
            "timeout": True,
        }


def capture_line(event: dict[str, Any]) -> str:
    # The public event is passed as-is.  No storyline, transition, or expected
    # state metadata is added by this harness.
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def capture_batch(events: list[dict[str, Any]], checkpoint: int) -> str:
    lines = [capture_line(event) for event in events]
    return (
        f"CAPTURE_BATCH checkpoint={checkpoint} count={len(events)}\n"
        "Each following JSON line is one immutable user capture. Preserve the\n"
        "order and do not answer questions about the batch.\n"
        + "\n".join(lines)
        + "\nEND_CAPTURE_BATCH\n"
        "Reply exactly CAPTURES_RECEIVED."
    )


def query_prompt(
    query_bundle: dict[str, Any],
    response_contract: dict[str, Any],
    scenario_id: str,
    checkpoint: int,
    query_ids: list[str],
) -> str:
    selected_queries = {
        query_id: query_bundle.get("queries", {}).get(query_id)
        for query_id in query_ids
        if query_id in query_bundle.get("queries", {})
    }
    return (
        "CHECKPOINT QUERY — read-only fork\n"
        f"The canonical ingestion history currently contains captures 1 through {checkpoint}.\n"
        "Use only the inherited conversation and the public contract/query bundle below.\n"
        "Return one JSON object and no prose outside it. Include every supplied query exactly once.\n"
        "The exact response shape is {response_contract, scenario_id, checkpoint, queries}.\n"
        "queries MUST be an object keyed by query_id, never an array. Each value is\n"
        "{assertions: [...]}. Each assertion MUST use public subject, public predicate,\n"
        "knowledge_status, source_refs, and the v2 value/unknown rules. Never emit\n"
        "state_key, type, grouped reports, or prose fields.\n"
        + json.dumps(
            {
                "checkpoint": checkpoint,
                "scenario_id": scenario_id,
                "response_contract": response_contract,
                "query_bundle": {"response_contract": query_bundle.get("response_contract"), "queries": selected_queries},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def parse_json_document(text: str) -> tuple[dict[str, Any] | None, str | None]:
    text = text.strip()
    if not text:
        return None, "empty model output"
    candidates = [text]
    if text.startswith("```"):
        lines = text.splitlines()
        candidates.append("\n".join(line for line in lines if not line.strip().startswith("```")).strip())
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first : last + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value, None
    return None, "model output was not a JSON object"


def output_text(result: dict[str, Any], output_path: Path) -> str:
    if output_path.exists():
        file_text = output_path.read_text(encoding="utf-8")
        parsed, _error = parse_json_document(file_text)
        if parsed is not None:
            return file_text
    event_texts: list[str] = []
    for event in reversed(result.get("events", [])):
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if isinstance(text, str):
            event_texts.append(text)
            continue
        content = item.get("content")
        if isinstance(content, str):
            event_texts.append(content)
    for text in event_texts:
        parsed, _error = parse_json_document(text)
        if parsed is not None:
            return text
    if event_texts:
        return max(event_texts, key=len)
    return ""


def base_command(cli: str, temp_workspace: Path) -> list[str]:
    return [
        cli,
        "exec",
        "--json",
        "--model",
        MODEL,
        "-c",
        f"model_reasoning_effort={REASONING_EFFORT}",
        "-s",
        "read-only",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(temp_workspace),
    ]


def resume_command(cli: str, session_id: str, output_path: Path) -> list[str]:
    command = [
        cli,
        "exec",
        "resume",
        session_id,
        "--json",
        "--model",
        MODEL,
        "-c",
        f"model_reasoning_effort={REASONING_EFFORT}",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-o",
        str(output_path),
    ]
    command.append("-")
    return command


def fork_command(cli: str, session_id: str) -> list[str]:
    return [
        cli,
        "exec",
        "fork",
        session_id,
        "--json",
        "--model",
        MODEL,
        "-c",
        f"model_reasoning_effort={REASONING_EFFORT}",
        "--ignore-rules",
        "--skip-git-repo-check",
    ]


def run(args: argparse.Namespace) -> int:
    cli = shutil.which("codex")
    if not cli:
        raise SystemExit("codex CLI was not found on PATH")
    for path_name in ("scenario", "prompt", "runner_prompt", "query_bundle", "response_contract", "output", "trajectory"):
        setattr(args, path_name, getattr(args, path_name).resolve())
    scenario = load_json(args.scenario)
    baseline_prompt = args.prompt.read_text(encoding="utf-8")
    runner_prompt = args.runner_prompt.read_text(encoding="utf-8")
    query_bundle = load_json(args.query_bundle)
    response_contract = load_json(args.response_contract)
    public_events = scenario["raw_events"][: args.max_events]
    checkpoints = [checkpoint for checkpoint in scenario["checkpoints"] if checkpoint <= args.max_events]
    if not checkpoints or checkpoints[-1] != args.max_events:
        raise SystemExit("--max-events must end at an approved checkpoint")
    available_query_ids = list(query_bundle.get("queries", {}).keys())
    if args.query_ids:
        query_ids = [item.strip() for item in args.query_ids.split(",") if item.strip()]
        unknown_query_ids = [item for item in query_ids if item not in available_query_ids]
        if unknown_query_ids:
            raise SystemExit(f"unknown query IDs: {','.join(unknown_query_ids)}")
    else:
        query_ids = available_query_ids
    if not query_ids:
        raise SystemExit("at least one query ID is required")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.trajectory.mkdir(parents=True, exist_ok=True)
    metadata: dict[str, Any] = {
        "run_id": args.run_id,
        "label": args.label,
        "started_at": iso_now(),
        "provider": "Codex CLI",
        "cli_path_basename": Path(cli).name,
        "model": MODEL,
        "reasoning_effort": REASONING_EFFORT,
        "sandbox": "read-only",
        "scenario_id": scenario["scenario_id"],
        "response_contract": response_contract.get("response_contract"),
        "contract_version": scenario["contract_version"],
        "event_count": args.max_events,
        "checkpoints": checkpoints,
        "batching": "one chronological capture batch per checkpoint segment; one persistent canonical session",
        "checkpoint_isolation": "native Codex CLI fork; query fork is never resumed",
        "structured_response": "prompt-constrained JSON; response-contract-v2 is validated by the deterministic evaluator",
        "query_ids": query_ids,
        "canonical_thread_id": None,
        "turns": [],
        "checkpoint_runs": {},
    }
    candidate: dict[str, Any] = {
        "response_contract": response_contract.get("response_contract"),
        "scenario_id": scenario["scenario_id"],
        "checkpoints": {},
        "run_metadata": metadata,
    }

    with tempfile.TemporaryDirectory(prefix="blackhole-baseline-") as temp_dir:
        temp_workspace = Path(temp_dir)
        first_end = checkpoints[0]
        initial_text = baseline_prompt + "\n\n" + runner_prompt + "\n\n" + capture_batch(public_events[:first_end], first_end)
        initial_output = temp_workspace / "canonical-initial.txt"
        initial = run_cli(base_command(cli, temp_workspace) + ["-o", str(initial_output), "-"], initial_text, args.timeout)
        canonical_id = initial.get("thread_id")
        metadata["canonical_thread_id"] = canonical_id
        metadata["turns"].append({"kind": "capture", "checkpoint": first_end, **{key: value for key, value in initial.items() if key != "events"}})
        if initial.get("returncode") != 0 or not canonical_id:
            raise SystemExit(f"canonical session failed: {initial.get('stderr')}")

        previous_end = 0
        for checkpoint_index, checkpoint in enumerate(checkpoints):
            segment_start = first_end if checkpoint_index == 0 else checkpoints[checkpoint_index - 1]
            if checkpoint_index > 0:
                batch_text = capture_batch(public_events[segment_start:checkpoint], checkpoint)
                output_path = temp_workspace / f"canonical-{checkpoint}.txt"
                resumed = run_cli(resume_command(cli, canonical_id, output_path), batch_text, args.timeout)
                metadata["turns"].append({"kind": "capture", "checkpoint": checkpoint, **{key: value for key, value in resumed.items() if key != "events"}})
                if resumed.get("returncode") != 0:
                    raise SystemExit(f"canonical resume failed at {checkpoint}: {resumed.get('stderr')}")

            raw_query_path = temp_workspace / f"query-{checkpoint}.txt"
            # Fork and ask in one provider invocation.  This avoids a race
            # between persisting a newly-created fork and resuming it while
            # retaining native checkpoint isolation.
            query_result = run_cli(
                fork_command(cli, canonical_id)
                + ["-o", str(raw_query_path), "-"],
                query_prompt(query_bundle, response_contract, scenario["scenario_id"], checkpoint, query_ids),
                args.timeout,
            )
            fork_id = query_result.get("thread_id")
            fork_record: dict[str, Any] = {
                "canonical_thread_id": canonical_id,
                "fork_thread_id": fork_id,
                "atomic_fork": True,
                "query": {key: value for key, value in query_result.items() if key != "events"},
                "discarded": True,
            }
            if query_result.get("returncode") != 0 or not fork_id:
                raise SystemExit(f"checkpoint fork/query failed at {checkpoint}: {query_result.get('stderr')}")
            raw_text = output_text(query_result, raw_query_path)
            parsed, parse_error = parse_json_document(raw_text)
            if parsed is None:
                parsed = {"response_contract": response_contract.get("response_contract"), "scenario_id": scenario["scenario_id"], "checkpoint": checkpoint, "queries": {}}
            query_map = parsed.get("queries") if isinstance(parsed.get("queries"), dict) else {}
            # Accept a common model formatting slip without interpreting its
            # assertions.  The evaluator still validates every assertion field.
            if isinstance(parsed.get("queries"), list):
                query_map = {
                    item["query_id"]: {"assertions": item.get("assertions", [])}
                    for item in parsed["queries"]
                    if isinstance(item, dict) and isinstance(item.get("query_id"), str)
                }
            candidate["checkpoints"][str(checkpoint)] = {"checkpoint": checkpoint, "queries": query_map}
            trajectory_output = args.trajectory / f"checkpoint-{checkpoint:03d}.json"
            trajectory_output.write_text(raw_text if raw_text else json.dumps(parsed, indent=2), encoding="utf-8")
            fork_record["parse_error"] = parse_error
            fork_record["response_contract"] = {
                "parsed": parse_error is None,
                "query_count": len(query_map),
                "trajectory_output": str(trajectory_output.relative_to(ROOT)),
            }
            metadata["checkpoint_runs"][str(checkpoint)] = fork_record

    metadata["finished_at"] = iso_now()
    args.output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {
        "run_id": metadata["run_id"],
        "output": str(args.output.relative_to(ROOT)),
        "trajectory": str(args.trajectory.relative_to(ROOT)),
        "canonical_thread_id": metadata["canonical_thread_id"],
        "checkpoints": checkpoints,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--runner-prompt", type=Path, default=DEFAULT_RUNNER_PROMPT)
    parser.add_argument("--query-bundle", type=Path, default=DEFAULT_QUERY_BUNDLE)
    parser.add_argument("--response-contract", type=Path, default=DEFAULT_RESPONSE_CONTRACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--trajectory", type=Path, default=DEFAULT_TRAJECTORY)
    parser.add_argument("--max-events", type=int, default=200)
    parser.add_argument("--query-ids", help="comma-separated query IDs for a labeled development slice")
    parser.add_argument("--run-id", default="baseline-v1")
    parser.add_argument("--label", default="OFFICIAL")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
