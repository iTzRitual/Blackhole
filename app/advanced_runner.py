"""Run the Experiment 001 stateful Blackhole architecture on a public case.

The runner receives only public scenario, contract, and query inputs. A fresh
Codex CLI call interprets each chronological checkpoint segment; SQLite and the
deterministic projection retain the state used by a separate fresh query call.
No expected output or evaluator is supplied to the provider.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.contract import PublicContract, canonical_value, canonical_unknown_reason, canonical_subject, canonical_predicate, normalize_text
from app.provider import parse_repaired_json, structured_call
from app.prompts import extraction_prompt, query_prompt
from app.relation_recovery import (
    DETERMINISTIC_RECOVERY_VERSION,
    deterministic_relationships,
    recovery_digest,
    retrieved_relation_replacements,
)
from app.response_projector import ResponseProjector
from app.state_store import StateStore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = ROOT / "benchmark" / "dev" / "cases" / "scenario-001.json"
DEFAULT_QUERY_BUNDLE = ROOT / "benchmark" / "dev" / "query-bundle-v2.json"
DEFAULT_RESPONSE_CONTRACT = ROOT / "benchmark" / "dev" / "response-contract-v2.json"
DEFAULT_OUTPUT = ROOT / "eval" / "results" / "experiment-001-fast-dev-candidate.json"
DEFAULT_TRAJECTORY = ROOT / "trajectories" / "runtime" / "experiment-001-fast-dev"
EXTRACTOR_VERSION = "experiment-001-extractor-v1"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def artifact_reference(path: Path) -> str:
    """Keep trajectory metadata portable and free of local absolute paths."""

    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return path.name


def normalize_observation(
    item: Any,
    *,
    public_contract: PublicContract,
    batch_event_ids: set[str],
    available_event_ids: set[str],
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    event_id = item.get("event_id")
    if not isinstance(event_id, str) or event_id not in batch_event_ids:
        return None
    subject = canonical_subject(item.get("subject"), public_contract.document)
    predicate = canonical_predicate(item.get("predicate"), public_contract.document)
    status = normalize_text(item.get("knowledge_status", "")) if isinstance(item.get("knowledge_status"), str) else ""
    if subject is None or predicate is None or status not in {"known", "inferred", "unknown"}:
        return None
    refs_value = item.get("source_refs", [event_id])
    refs = sorted({ref for ref in refs_value if isinstance(ref, str) and ref in available_event_ids}) if isinstance(refs_value, list) else []
    if event_id not in refs:
        refs.append(event_id)
        refs.sort()
    result: dict[str, Any] = {
        "event_id": event_id,
        "subject": subject,
        "predicate": predicate,
        "knowledge_status": status,
        "operation": normalize_text(item.get("operation", "set")) if isinstance(item.get("operation", "set"), str) else "set",
        "source_refs": refs,
    }
    if result["operation"] not in {"set", "supersede", "correction", "contradiction", "duplicate"}:
        result["operation"] = "set"
    if status == "unknown":
        if "unknown_reason" not in item:
            return None
        result["unknown_reason"] = canonical_unknown_reason(item["unknown_reason"], public_contract.document)
    else:
        if "value" not in item:
            return None
        result["value"] = canonical_value(item["value"], public_contract.document, predicate)
    supersedes = item.get("supersedes_event_id")
    if isinstance(supersedes, str) and supersedes in available_event_ids:
        result["supersedes_event_id"] = supersedes
    return result


def normalize_relationship(
    item: Any,
    *,
    public_contract: PublicContract,
    batch_event_ids: set[str],
    available_event_ids: set[str],
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    source = item.get("source_event_id")
    target = item.get("target_event_id")
    relation_type = item.get("relation_type")
    if not isinstance(source, str) or source not in batch_event_ids or not isinstance(relation_type, str):
        return None
    if not isinstance(target, str) or target not in available_event_ids:
        target = None
    changed_fields = item.get("changed_fields", [])
    if not isinstance(changed_fields, list):
        changed_fields = []
    result: dict[str, Any] = {
        "source_event_id": source,
        "target_event_id": target,
        "relation_type": normalize_text(relation_type).replace(" ", "_"),
        "changed_fields": [str(value) for value in changed_fields if isinstance(value, str)],
    }
    if isinstance(item.get("duplicate_group"), str):
        result["duplicate_group"] = item["duplicate_group"]
    if isinstance(item.get("note"), str):
        result["note"] = item["note"]
    return result


def normalize_extraction(
    parsed: Any,
    *,
    public_contract: PublicContract,
    batch_event_ids: set[str],
    available_event_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(parsed, dict):
        return [], []
    observations = [
        normalized
        for item in parsed.get("observations", []) if isinstance(parsed.get("observations", []), list)
        for normalized in [
            normalize_observation(
                item,
                public_contract=public_contract,
                batch_event_ids=batch_event_ids,
                available_event_ids=available_event_ids,
            )
        ]
        if normalized is not None
    ]
    relationships = [
        normalized
        for item in parsed.get("relationships", []) if isinstance(parsed.get("relationships", []), list)
        for normalized in [
            normalize_relationship(
                item,
                public_contract=public_contract,
                batch_event_ids=batch_event_ids,
                available_event_ids=available_event_ids,
            )
        ]
        if normalized is not None
    ]
    return observations, relationships


def available_query_ids(query_bundle: dict[str, Any], requested: str | None) -> list[str]:
    all_ids = list(query_bundle.get("queries", {}).keys())
    if not requested:
        return all_ids
    query_ids = [item.strip() for item in requested.split(",") if item.strip()]
    unknown = [item for item in query_ids if item not in all_ids]
    if unknown:
        raise SystemExit(f"unknown query IDs: {','.join(unknown)}")
    return query_ids


def write_call_trace(call_dir: Path, stem: str, prompt: str, result: dict[str, Any]) -> dict[str, Any]:
    prompt_path = call_dir / f"{stem}.prompt.txt"
    raw_path = call_dir / f"{stem}.raw.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    raw_path.write_text(result.get("raw_text", ""), encoding="utf-8")
    provider = dict(result.get("provider", {}))
    provider.update(
        {
            "kind": stem.split("-", 1)[0],
            "prompt_path": str(prompt_path.relative_to(ROOT)),
            "raw_output_path": str(raw_path.relative_to(ROOT)),
            "parse_error": result.get("parse_error"),
        }
    )
    return provider


def replay_extraction(path: Path) -> dict[str, Any]:
    """Replay a recorded semantic extraction for deterministic projection checks."""

    raw_text = path.read_text(encoding="utf-8")
    parsed = json.loads(raw_text)
    return {
        "parsed": parsed,
        "parse_error": None,
        "raw_text": raw_text,
        "provider": {
            "returncode": 0,
            "duration_seconds": 0.0,
            "thread_id": None,
            "usage": None,
            "stderr": {"line_count": 0, "last_lines": []},
            "model": "gpt-5.6-luna",
            "reasoning_effort": "max",
            "replayed": True,
            "replay_path": artifact_reference(path),
        },
    }


def replay_model_output(path: Path) -> dict[str, Any]:
    """Replay a recorded model response while applying transport-only JSON repair."""

    raw_text = path.read_text(encoding="utf-8")
    parsed, parse_error, parse_repair = parse_repaired_json(raw_text)
    return {
        "parsed": parsed,
        "parse_error": parse_error,
        "raw_text": raw_text,
        "provider": {
            "returncode": 0,
            "duration_seconds": 0.0,
            "thread_id": None,
            "usage": None,
            "stderr": {"line_count": 0, "last_lines": []},
            "model": "gpt-5.6-luna",
            "reasoning_effort": "max",
            "replayed": True,
            "replay_path": artifact_reference(path),
            "parse_repair": parse_repair,
        },
    }


def run(args: argparse.Namespace) -> int:
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1")
    for path_name in ("scenario", "query_bundle", "response_contract", "output", "trajectory"):
        setattr(args, path_name, getattr(args, path_name).resolve())
    if args.replay_extraction is not None:
        args.replay_extraction = args.replay_extraction.resolve()
    if args.replay_extraction_dir is not None:
        args.replay_extraction_dir = args.replay_extraction_dir.resolve()
    if args.replay_query is not None:
        args.replay_query = args.replay_query.resolve()
    scenario = load_json(args.scenario)
    query_bundle = load_json(args.query_bundle)
    contract_document = load_json(args.response_contract)
    public_contract = PublicContract(contract_document)
    events = scenario["raw_events"][: args.max_events]
    checkpoints = [checkpoint for checkpoint in scenario["checkpoints"] if checkpoint <= args.max_events]
    if not checkpoints or checkpoints[-1] != args.max_events:
        raise SystemExit("--max-events must end at an approved checkpoint")
    query_ids = available_query_ids(query_bundle, args.query_ids)
    if not query_ids:
        raise SystemExit("at least one query ID is required")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.trajectory.mkdir(parents=True, exist_ok=True)
    call_dir = args.trajectory / "calls"
    call_dir.mkdir(parents=True, exist_ok=True)
    metadata: dict[str, Any] = {
        "run_id": args.run_id,
        "label": args.label,
        "started_at": iso_now(),
        "provider": "Codex CLI",
        "model": "gpt-5.6-luna",
        "reasoning_effort": args.semantic_reasoning,
        "runtime_mode": "subscription-first local authenticated CLI; no provider token access",
        "scenario_id": scenario["scenario_id"],
        "response_contract": contract_document.get("response_contract"),
        "contract_version": scenario["contract_version"],
        "event_count": args.max_events,
        "checkpoints": checkpoints,
        "query_ids": query_ids,
        "architecture": "fresh scoped semantic calls plus SQLite append-only raw events and deterministic rebuildable projection",
        "ingestion": "one fresh semantic extraction call per chronological batch within each checkpoint segment",
        "querying": "deterministic public response projection from SQLite state; optional fresh model query is diagnostic only",
        "relation_recovery": args.relation_recovery,
        "relation_recovery_calls": [],
        "calls": [],
        "projection_runs": [],
    }
    candidate: dict[str, Any] = {
        "response_contract": contract_document.get("response_contract"),
        "scenario_id": scenario["scenario_id"],
        "checkpoints": {},
        "run_metadata": metadata,
    }
    available_event_ids: set[str] = set()
    previous_checkpoint = 0

    with tempfile.TemporaryDirectory(prefix="blackhole-advanced-") as temp_dir:
        temp_root = Path(temp_dir)
        provider_workspace = temp_root / "provider-workspace"
        provider_workspace.mkdir()
        db_path = temp_root / "state.sqlite"
        with StateStore(db_path) as store:
            for checkpoint_index, checkpoint in enumerate(checkpoints):
                segment = events[previous_checkpoint:checkpoint]
                for batch_index in range(0, len(segment), args.batch_size):
                    batch = segment[batch_index : batch_index + args.batch_size]
                    store.insert_raw_events(batch)
                    available_event_ids.update(event["event_id"] for event in batch)
                    batch_event_ids = {event["event_id"] for event in batch}
                    prior_snapshot = store.extraction_context()
                    extraction_request = extraction_prompt(
                        events=batch,
                        contract=contract_document,
                        prior_snapshot=prior_snapshot,
                    )
                    call_name = f"extraction-{checkpoint:03d}-{batch_index // args.batch_size + 1:02d}"
                    replay_path = None
                    if args.replay_extraction_dir is not None:
                        replay_path = args.replay_extraction_dir / "calls" / f"{call_name}.raw.txt"
                        if not replay_path.exists():
                            raise SystemExit(f"recorded extraction is missing: {replay_path}")
                    if replay_path is not None:
                        extraction_result = replay_extraction(replay_path)
                    elif args.replay_extraction is not None:
                        if checkpoint_index != 0 or batch_index != 0 or len(segment) > args.batch_size:
                            raise SystemExit("--replay-extraction supports only one complete first checkpoint segment")
                        extraction_result = replay_extraction(args.replay_extraction)
                    else:
                        extraction_result = structured_call(
                            extraction_request,
                            temp_workspace=provider_workspace,
                            output_path=temp_root / f"extraction-{checkpoint:03d}-{batch_index // args.batch_size + 1:02d}.txt",
                            timeout=args.timeout,
                            reasoning_effort=args.semantic_reasoning,
                        )
                    metadata["calls"].append(write_call_trace(call_dir, call_name, extraction_request, extraction_result))
                    if extraction_result.get("provider", {}).get("returncode") != 0 or extraction_result.get("parse_error") or not isinstance(extraction_result.get("parsed"), dict):
                        raise SystemExit(f"semantic extraction failed for {call_name}: {extraction_result.get('parse_error') or extraction_result.get('provider', {}).get('stderr')}")
                    observations, relationships = normalize_extraction(
                        extraction_result.get("parsed"),
                        public_contract=public_contract,
                        batch_event_ids=batch_event_ids,
                        available_event_ids=available_event_ids,
                    )
                    store.add_observations(observations, EXTRACTOR_VERSION)
                    store.add_relationships(relationships, EXTRACTOR_VERSION)
                    if args.relation_recovery == "deterministic":
                        recovered = deterministic_relationships(store.connection)
                        inserted = store.add_relationships(recovered, DETERMINISTIC_RECOVERY_VERSION)
                        metadata["relation_recovery_calls"].append(
                            {
                                "checkpoint": checkpoint,
                                "batch": batch_index // args.batch_size + 1,
                                "candidate_count": len(recovered),
                                "inserted_count": inserted,
                                "candidate_digest": recovery_digest(recovered),
                                "version": DETERMINISTIC_RECOVERY_VERSION,
                            }
                        )
                    elif args.relation_recovery == "retrieval":
                        recovered = deterministic_relationships(store.connection)
                        deterministic_inserted = store.add_relationships(recovered, DETERMINISTIC_RECOVERY_VERSION)
                        retrieved = retrieved_relation_replacements(store.connection, max_candidates=4)
                        replacements = retrieved["replacements"]
                        replacement_inserted = store.replace_relationships_for_sources(
                            replacements,
                            "experiment-003-retrieval-reconciliation-v1",
                        )
                        recovery_record = {
                            "checkpoint": checkpoint,
                            "batch": batch_index // args.batch_size + 1,
                            "deterministic_candidate_count": len(recovered),
                            "deterministic_inserted_count": deterministic_inserted,
                            "candidate_set_count": len(retrieved["candidate_sets"]),
                            "replacement_count": len(replacements),
                            "replacement_inserted_count": replacement_inserted,
                            "replacement_digest": retrieved["replacement_digest"],
                            "max_candidates": retrieved["max_candidates"],
                            "version": "experiment-003-retrieval-reconciliation-v1",
                        }
                        metadata["relation_recovery_calls"].append(recovery_record)
                        (args.trajectory / f"relation-recovery-{checkpoint:03d}-{batch_index // args.batch_size + 1:02d}.json").write_text(
                            json.dumps(retrieved, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8",
                        )
                    projection_run = store.rebuild_projection()
                    metadata["projection_runs"].append(projection_run)
                projected_snapshot = store.snapshot()
                if args.use_query_model:
                    query_request = query_prompt(
                        contract=contract_document,
                        query_bundle=query_bundle,
                        scenario_id=scenario["scenario_id"],
                        checkpoint=checkpoint,
                        query_ids=query_ids,
                        snapshot=projected_snapshot,
                    )
                    if args.replay_query is not None:
                        if checkpoint_index != 0 or len(checkpoints) != 1:
                            raise SystemExit("--replay-query supports only one checkpoint")
                        query_result = replay_model_output(args.replay_query)
                    else:
                        query_result = structured_call(
                            query_request,
                            temp_workspace=provider_workspace,
                            output_path=temp_root / f"query-{checkpoint:03d}.txt",
                            timeout=args.timeout,
                        )
                else:
                    deterministic_queries = ResponseProjector(contract_document, query_bundle).project(
                        projected_snapshot,
                        query_ids=query_ids,
                    )
                    query_request = "DETERMINISTIC QUERY PROJECTION\n" + json.dumps(
                        {"checkpoint": checkpoint, "query_ids": query_ids}, ensure_ascii=False, indent=2
                    )
                    query_result = {
                        "parsed": {"queries": deterministic_queries},
                        "parse_error": None,
                        "raw_text": json.dumps({"queries": deterministic_queries}, ensure_ascii=False, indent=2),
                        "provider": {
                            "returncode": 0,
                            "duration_seconds": 0.0,
                            "thread_id": None,
                            "usage": None,
                            "stderr": {"line_count": 0, "last_lines": []},
                            "model": "deterministic-projection",
                            "reasoning_effort": "none",
                            "deterministic": True,
                        },
                    }
                query_call_name = f"query-{checkpoint:03d}"
                metadata["calls"].append(write_call_trace(call_dir, query_call_name, query_request, query_result))
                if query_result.get("provider", {}).get("returncode") != 0 or query_result.get("parse_error") or not isinstance(query_result.get("parsed"), dict):
                    raise SystemExit(f"query projection failed for {query_call_name}: {query_result.get('parse_error') or query_result.get('provider', {}).get('stderr')}")
                sanitized = public_contract.sanitize_response(
                    query_result.get("parsed"),
                    scenario_id=scenario["scenario_id"],
                    checkpoint=checkpoint,
                    query_ids=query_ids,
                    event_ids=available_event_ids,
                )
                candidate["checkpoints"][str(checkpoint)] = {
                    "checkpoint": checkpoint,
                    "queries": sanitized["queries"],
                }
                (args.trajectory / f"checkpoint-{checkpoint:03d}.json").write_text(
                    json.dumps(sanitized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                previous_checkpoint = checkpoint
            store_snapshot = store.snapshot()
        shutil.copy2(db_path, args.trajectory / "state.sqlite")

    usage_totals = {"input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0}
    for call in metadata["calls"]:
        usage = call.get("usage") or {}
        for key in usage_totals:
            value = usage.get(key)
            if isinstance(value, int):
                usage_totals[key] += value
    metadata["usage_totals"] = usage_totals
    metadata["final_state_counts"] = {
        "current_facts": len(store_snapshot["current_facts"]),
        "history_observations": len(store_snapshot["history"]),
        "relationships": len(store_snapshot["relationships"]),
    }
    metadata["finished_at"] = iso_now()
    args.output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": args.run_id, "output": str(args.output.relative_to(ROOT)), "trajectory": str(args.trajectory.relative_to(ROOT)), "checkpoints": checkpoints, "usage_totals": usage_totals}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--query-bundle", type=Path, default=DEFAULT_QUERY_BUNDLE)
    parser.add_argument("--response-contract", type=Path, default=DEFAULT_RESPONSE_CONTRACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--trajectory", type=Path, default=DEFAULT_TRAJECTORY)
    parser.add_argument("--max-events", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=10, help="maximum captures per fresh semantic extraction call")
    parser.add_argument("--replay-extraction", type=Path, help="replay one recorded extraction JSON for a deterministic projection/query diagnostic")
    parser.add_argument("--replay-extraction-dir", type=Path, help="replay recorded extraction JSON files from a prior trajectory's calls directory")
    parser.add_argument("--replay-query", type=Path, help="replay one recorded query response for a deterministic projection diagnostic")
    parser.add_argument("--use-query-model", action="store_true", help="use a fresh scoped model query instead of the deterministic response projector")
    parser.add_argument("--query-ids", help="comma-separated public query IDs for a labeled development slice")
    parser.add_argument("--run-id", default="experiment-001-fast-dev")
    parser.add_argument("--label", default="EXPERIMENT 001 / DEV FAST / NOT OFFICIAL SCORE")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--semantic-reasoning", choices=["max", "high", "medium"], default="max", help="Codex reasoning effort for semantic extraction; max is the default")
    parser.add_argument(
        "--relation-recovery",
        choices=["none", "deterministic", "retrieval"],
        default="none",
        help="optional generic deterministic relation recovery variant",
    )
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
