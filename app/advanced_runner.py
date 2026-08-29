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
from app.completeness import (
    DETERMINISTIC_COMPLETION_VERSION,
    EVIDENCE_SCANNER_VERSION,
    VERIFIER_VERSION,
    detect_coverage_gaps,
    deterministic_completions,
    evidence_digest,
    prepare_verifier_observations,
    scan_raw_evidence,
    verification_prompt,
)
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
        "completeness": args.completeness,
        "completeness_batches": [],
        "completeness_totals": {
            "total_captures": len(events),
            "captures_scanned": 0,
            "captures_flagged": 0,
            "captures_repaired_deterministically": 0,
            "captures_sent_to_verifier": 0,
            "verifier_no_change_count": 0,
            "observations_added": 0,
            "observations_replaced": 0,
            "false_positive_verification_triggers": 0,
        },
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
                    if args.completeness != "none":
                        pre_completion_snapshot = store.snapshot()
                        evidence_records = [scan_raw_evidence(event) for event in batch]
                        gap_records = [
                            detect_coverage_gaps(event, evidence, pre_completion_snapshot, contract_document)
                            for event, evidence in zip(batch, evidence_records)
                        ]
                        flagged = [record for record in gap_records if record.get("reasons")]
                        metadata["completeness_totals"]["captures_scanned"] += len(batch)
                        metadata["completeness_totals"]["captures_flagged"] += len(flagged)

                        completion_proposals = [
                            completion
                            for event, gap in zip(batch, gap_records)
                            if gap.get("reasons")
                            for completion in deterministic_completions(event, gap, pre_completion_snapshot)
                        ]
                        normalized_completions = [
                            normalized
                            for item in completion_proposals
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
                        completion_inserted = store.add_observations(
                            normalized_completions,
                            DETERMINISTIC_COMPLETION_VERSION,
                        )
                        metadata["completeness_totals"]["observations_added"] += completion_inserted
                        metadata["completeness_totals"]["observations_replaced"] += sum(
                            item.get("operation") in {"correction", "supersede"}
                            for item in normalized_completions
                        )
                        repaired_event_ids = {
                            item.get("event_id")
                            for item in normalized_completions
                            if isinstance(item.get("event_id"), str)
                        }
                        metadata["completeness_totals"]["captures_repaired_deterministically"] += len(repaired_event_ids)
                        if completion_inserted:
                            projection_run = store.rebuild_projection()
                            metadata["projection_runs"].append(projection_run)

                        post_completion_snapshot = store.snapshot()
                        residual_records: list[dict[str, Any]] = []
                        for event, evidence, gap in zip(batch, evidence_records, gap_records):
                            if not gap.get("reasons"):
                                continue
                            residual = detect_coverage_gaps(event, evidence, post_completion_snapshot, contract_document)
                            residual["initial_reasons"] = gap.get("reasons", [])
                            residual_records.append({"event": event, "evidence": evidence, "gap": residual})

                        verifier_records: list[dict[str, Any]] = []
                        if args.completeness == "verifier":
                            metadata["completeness_totals"]["captures_sent_to_verifier"] += len(residual_records)
                            for verifier_index, record in enumerate(residual_records, start=1):
                                event = record["event"]
                                evidence = record["evidence"]
                                gap = record["gap"]
                                verifier_request = verification_prompt(
                                    event,
                                    gap,
                                    evidence,
                                    post_completion_snapshot,
                                    contract_document,
                                )
                                verification_name = (
                                    f"verification-{checkpoint:03d}-{batch_index // args.batch_size + 1:02d}-"
                                    f"{verifier_index:02d}"
                                )
                                verification_result = structured_call(
                                    verifier_request,
                                    temp_workspace=provider_workspace,
                                    output_path=temp_root / f"{verification_name}.txt",
                                    timeout=args.timeout,
                                    reasoning_effort="high",
                                )
                                metadata["calls"].append(
                                    write_call_trace(call_dir, verification_name, verifier_request, verification_result)
                                )
                                if (
                                    verification_result.get("provider", {}).get("returncode") != 0
                                    or verification_result.get("parse_error")
                                    or not isinstance(verification_result.get("parsed"), dict)
                                ):
                                    raise SystemExit(
                                        f"completeness verification failed for {verification_name}: "
                                        f"{verification_result.get('parse_error') or verification_result.get('provider', {}).get('stderr')}"
                                    )
                                prepared = prepare_verifier_observations(
                                    verification_result.get("parsed"),
                                    event_id=str(event.get("event_id")),
                                    evidence=evidence,
                                    contract=contract_document,
                                )
                                normalized_verifier = [
                                    normalized
                                    for item in prepared["items"]
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
                                verifier_inserted = store.add_observations(
                                    normalized_verifier,
                                    VERIFIER_VERSION,
                                )
                                metadata["completeness_totals"]["observations_added"] += verifier_inserted
                                metadata["completeness_totals"]["observations_replaced"] += sum(
                                    item.get("operation") in {"correction", "supersede"}
                                    for item in normalized_verifier
                                )
                                if prepared["no_change"] or not normalized_verifier:
                                    metadata["completeness_totals"]["verifier_no_change_count"] += 1
                                if prepared["no_change"] and not normalized_verifier:
                                    metadata["completeness_totals"]["false_positive_verification_triggers"] += 1
                                verifier_records.append(
                                    {
                                        "event_id": event.get("event_id"),
                                        "initial_reasons": gap.get("initial_reasons", []),
                                        "residual_reasons": gap.get("reasons", []),
                                        "no_change": prepared["no_change"],
                                        "accepted_observation_count": len(normalized_verifier),
                                        "inserted_observation_count": verifier_inserted,
                                        "rejected": prepared["rejected"],
                                        "call": verification_name,
                                    }
                                )
                            if any(item["inserted_observation_count"] for item in verifier_records):
                                projection_run = store.rebuild_projection()
                                metadata["projection_runs"].append(projection_run)

                        final_snapshot = store.snapshot()
                        final_residual = []
                        for record in residual_records:
                            final_gap = detect_coverage_gaps(
                                record["event"],
                                record["evidence"],
                                final_snapshot,
                                contract_document,
                            )
                            final_residual.append(
                                {
                                    "event_id": record["event"].get("event_id"),
                                    "reasons": final_gap.get("reasons", []),
                                }
                            )
                        batch_record = {
                            "checkpoint": checkpoint,
                            "batch": batch_index // args.batch_size + 1,
                            "scanner_version": EVIDENCE_SCANNER_VERSION,
                            "completion_version": DETERMINISTIC_COMPLETION_VERSION,
                            "verifier_version": VERIFIER_VERSION if args.completeness == "verifier" else None,
                            "event_ids": [event.get("event_id") for event in batch],
                            "scanned_count": len(batch),
                            "flagged_count": len(flagged),
                            "flagged_events": [
                                {
                                    "event_id": record.get("event_id"),
                                    "reasons": record.get("reasons", []),
                                    "mapping_count": len(record.get("mappings", [])),
                                    "evidence_digest": evidence_digest(evidence),
                                }
                                for record, evidence in zip(gap_records, evidence_records)
                                if record.get("reasons")
                            ],
                            "deterministic_proposal_count": len(normalized_completions),
                            "deterministic_inserted_count": completion_inserted,
                            "residual_events": [
                                {
                                    "event_id": item["event"].get("event_id"),
                                    "reasons": item["gap"].get("reasons", []),
                                }
                                for item in residual_records
                            ],
                            "verifier_records": verifier_records,
                            "final_residual": final_residual,
                        }
                        metadata["completeness_batches"].append(batch_record)
                        (args.trajectory / f"completeness-{checkpoint:03d}-{batch_index // args.batch_size + 1:02d}.json").write_text(
                            json.dumps(
                                {
                                    "evidence_records": evidence_records,
                                    "gap_records": gap_records,
                                    "batch_record": batch_record,
                                },
                                ensure_ascii=False,
                                indent=2,
                            )
                            + "\n",
                            encoding="utf-8",
                        )
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
    verification_calls = [call for call in metadata["calls"] if call.get("kind") == "verification"]
    completeness_provider_usage = {
        "calls": len(verification_calls),
        "input_tokens": sum((call.get("usage") or {}).get("input_tokens", 0) for call in verification_calls if isinstance((call.get("usage") or {}).get("input_tokens", 0), int)),
        "output_tokens": sum((call.get("usage") or {}).get("output_tokens", 0) for call in verification_calls if isinstance((call.get("usage") or {}).get("output_tokens", 0), int)),
        "reasoning_output_tokens": sum((call.get("usage") or {}).get("reasoning_output_tokens", 0) for call in verification_calls if isinstance((call.get("usage") or {}).get("reasoning_output_tokens", 0), int)),
        "runtime_seconds": sum(call.get("duration_seconds", 0.0) for call in verification_calls if isinstance(call.get("duration_seconds"), (int, float))),
    }
    metadata["completeness_totals"]["provider_calls"] = completeness_provider_usage["calls"]
    metadata["completeness_totals"]["provider_input_tokens"] = completeness_provider_usage["input_tokens"]
    metadata["completeness_totals"]["provider_output_tokens"] = completeness_provider_usage["output_tokens"]
    metadata["completeness_totals"]["provider_reasoning_output_tokens"] = completeness_provider_usage["reasoning_output_tokens"]
    metadata["completeness_totals"]["provider_runtime_seconds"] = completeness_provider_usage["runtime_seconds"]
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
    parser.add_argument(
        "--completeness",
        choices=["none", "deterministic", "verifier"],
        default="none",
        help="optional selective raw-source completeness treatment",
    )
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
