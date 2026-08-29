"""Deferred Blackhole ingestion over the shared state and provider boundaries.

The engine keeps capture cheap and synchronous. Semantic work is performed
later against bounded chronological batches, then passes through the same
normalization, completeness, relation-recovery, duplicate-evidence, and
rebuildable projection components used by the kept advanced architecture.
"""

from __future__ import annotations

import copy
import tempfile
import uuid
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from app.completeness import (
    DETERMINISTIC_COMPLETION_VERSION,
    detect_coverage_gaps,
    deterministic_completions,
    scan_raw_evidence,
)
from app.contract import PublicContract
from app.prompts import extraction_prompt
from app.provider import DEFAULT_PROVIDER_MODEL, structured_call
from app.relation_recovery import (
    DETERMINISTIC_RECOVERY_VERSION,
    deterministic_relationships,
    retrieved_relation_replacements,
)
from app.semantic import normalize_extraction
from app.state_store import (
    DUPLICATE_EVIDENCE_PROJECTION_VERSION,
    StateStore,
)


INGESTION_PROCESSING_VERSION = "blackhole-ingestion-v1"
INGESTION_EXTRACTOR_VERSION = "blackhole-semantic-extractor-v1"
RETRIEVAL_RELATION_VERSION = "experiment-003-retrieval-reconciliation-v1"


class SemanticProvider(Protocol):
    """Provider boundary required by deferred semantic processing."""

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_snapshot: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a public extraction object with observations/relationships."""


class CodexCLIProvider:
    """Subscription-first Codex CLI adapter with externally owned auth.

    The adapter delegates authentication to the already-installed CLI. Its
    temporary workspace and output files are deleted when the adapter closes;
    no credential or raw provider response is persisted by Blackhole.
    """

    def __init__(
        self,
        *,
        timeout: int = 900,
        model: str = DEFAULT_PROVIDER_MODEL,
        reasoning_effort: str = "max",
    ) -> None:
        if timeout < 1:
            raise ValueError("timeout must be positive")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model must be a non-empty string")
        if reasoning_effort not in {"max", "high", "medium"}:
            raise ValueError("unsupported reasoning effort")
        self.timeout = timeout
        self.model = model
        self.reasoning_effort = reasoning_effort
        self._temporary = tempfile.TemporaryDirectory(prefix="blackhole-provider-")
        self.workspace = Path(self._temporary.name) / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.call_count = 0
        self.last_call: dict[str, Any] | None = None

    def close(self) -> None:
        self._temporary.cleanup()

    def __enter__(self) -> "CodexCLIProvider":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_snapshot: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        self.call_count += 1
        prompt = extraction_prompt(
            events=events,
            contract=contract,
            prior_snapshot=prior_snapshot,
        )
        output_path = Path(self._temporary.name) / f"extraction-{self.call_count:04d}.json"
        result = structured_call(
            prompt,
            temp_workspace=self.workspace,
            output_path=output_path,
            timeout=self.timeout,
            model=self.model,
            reasoning_effort=self.reasoning_effort,
        )
        provider_metadata = result.get("provider", {})
        self.last_call = {
            "call_number": self.call_count,
            "returncode": provider_metadata.get("returncode"),
            "duration_seconds": provider_metadata.get("duration_seconds"),
            "usage": provider_metadata.get("usage"),
            "model": provider_metadata.get("model", self.model),
            "reasoning_effort": provider_metadata.get("reasoning_effort"),
        }
        if (
            provider_metadata.get("returncode") != 0
            or result.get("parse_error")
            or not isinstance(result.get("parsed"), dict)
        ):
            raise RuntimeError("Codex CLI semantic extraction did not return valid JSON")
        return result["parsed"]


class IngestionEngine:
    """Capture and deferred semantic processing service for Blackhole state."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        contract: dict[str, Any],
        provider: SemanticProvider | None = None,
        store: StateStore | None = None,
        batch_size: int = 10,
        relation_recovery: str = "retrieval",
        completeness: str = "deterministic",
        duplicate_evidence: bool = True,
        processing_version: str = INGESTION_PROCESSING_VERSION,
        extractor_version: str = INGESTION_EXTRACTOR_VERSION,
    ) -> None:
        if store is not None and db_path is not None:
            raise ValueError("pass either db_path or store, not both")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        if relation_recovery not in {"none", "deterministic", "retrieval"}:
            raise ValueError("unsupported relation recovery mode")
        if completeness not in {"none", "deterministic"}:
            raise ValueError("deferred ingestion supports none or deterministic completeness")
        self.store = store or StateStore(db_path or ":memory:")
        self._owns_store = store is None
        self.contract_document = copy.deepcopy(contract)
        self.public_contract = PublicContract(self.contract_document)
        self.provider = provider
        self.batch_size = batch_size
        self.relation_recovery = relation_recovery
        self.completeness = completeness
        self.duplicate_evidence = duplicate_evidence
        self.processing_version = processing_version
        self.extractor_version = extractor_version

    def close(self) -> None:
        if self._owns_store:
            self.store.close()

    def __enter__(self) -> "IngestionEngine":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def capture(
        self,
        payload: str | dict[str, Any],
        *,
        source_type: str = "text",
        event_id: str | None = None,
        captured_at: str | None = None,
        observed_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append one raw capture and return without invoking a provider."""

        if isinstance(payload, str):
            if not payload.strip():
                raise ValueError("capture text must not be empty")
            raw_payload: dict[str, Any] = {"text": payload}
        elif isinstance(payload, dict):
            if not payload:
                raise ValueError("capture payload must not be empty")
            raw_payload = copy.deepcopy(payload)
        else:
            raise ValueError("capture payload must be text or an object")
        if not isinstance(source_type, str) or not source_type.strip():
            raise ValueError("source_type must be a non-empty string")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")

        next_sequence = self.store.connection.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 AS next_sequence FROM raw_events"
        ).fetchone()["next_sequence"]
        sequence = int(next_sequence)
        event_id = event_id or f"capture-{uuid.uuid4().hex}"
        captured_at = captured_at or self._now()
        observed_at = observed_at or datetime.now(timezone.utc).date().isoformat()
        event = {
            "event_id": event_id,
            "sequence": sequence,
            "captured_at": captured_at,
            "observed_at": observed_at,
            "source_type": source_type.strip(),
            "payload": raw_payload,
            "metadata": copy.deepcopy(metadata or {}),
        }
        self.store.insert_raw_events([event])
        return {
            "saved": True,
            "message": "Saved.",
            "event_id": event_id,
            "sequence": sequence,
            "processing_status": "pending",
        }

    def processing_status(self, event_id: str | None = None) -> dict[str, Any] | None:
        return self.store.processing_status(event_id)

    def snapshot(self) -> dict[str, Any]:
        return self.store.snapshot()

    def _available_event_ids(self, max_sequence: int) -> set[str]:
        return {
            str(event.get("event_id"))
            for event in self.store.raw_events(max_sequence=max_sequence)
            if isinstance(event.get("event_id"), str)
        }

    def _relation_recovery(self) -> tuple[int, str | None]:
        inserted = 0
        if self.relation_recovery == "none":
            return inserted, None
        recovered = deterministic_relationships(self.store.connection)
        inserted += self.store.add_relationships(recovered, DETERMINISTIC_RECOVERY_VERSION)
        if self.relation_recovery == "deterministic":
            return inserted, DETERMINISTIC_RECOVERY_VERSION
        retrieved = retrieved_relation_replacements(self.store.connection, max_candidates=4)
        inserted += self.store.replace_relationships_for_sources(
            retrieved["replacements"],
            RETRIEVAL_RELATION_VERSION,
        )
        return inserted, RETRIEVAL_RELATION_VERSION

    def _completeness(self, events: list[dict[str, Any]], available_event_ids: set[str]) -> int:
        if self.completeness == "none":
            return 0
        pre_completion_snapshot = self.store.snapshot()
        event_ids = {
            str(event.get("event_id"))
            for event in events
            if isinstance(event.get("event_id"), str)
        }
        proposals: list[dict[str, Any]] = []
        for event in events:
            evidence = scan_raw_evidence(event)
            gap = detect_coverage_gaps(
                event,
                evidence,
                pre_completion_snapshot,
                self.contract_document,
            )
            if gap.get("reasons"):
                proposals.extend(deterministic_completions(event, gap, pre_completion_snapshot))
        normalized: list[dict[str, Any]] = []
        for proposal in proposals:
            proposal_observations, _ = normalize_extraction(
                {"observations": [proposal], "relationships": []},
                public_contract=self.public_contract,
                batch_event_ids=event_ids,
                available_event_ids=available_event_ids,
            )
            normalized.extend(proposal_observations)
        return self.store.add_observations(normalized, DETERMINISTIC_COMPLETION_VERSION)

    @staticmethod
    def _failure_text(error: BaseException) -> str:
        message = str(error).strip()
        if not message:
            message = "processing failed"
        return f"{type(error).__name__}: {message[:900]}"

    def _process_batch(
        self,
        events: list[dict[str, Any]],
        *,
        retry_failed: bool = False,
    ) -> dict[str, Any]:
        events = sorted(events, key=lambda event: (int(event["sequence"]), str(event["event_id"])))
        event_ids = [str(event["event_id"]) for event in events]
        eligible_statuses = {"pending", "failed"} if retry_failed else {"pending"}
        eligible_events = [
            event
            for event in events
            if (status := self.store.processing_status(str(event["event_id"]))) is not None
            and status["status"] in eligible_statuses
        ]
        if not eligible_events:
            return {
                "requested": len(events),
                "processed": 0,
                "failed": 0,
                "skipped": len(events),
                "event_ids": event_ids,
                "state_rebuilt": False,
                "semantic_effects": 0,
            }
        claimed_ids = [str(event["event_id"]) for event in eligible_events]
        claimed = self.store.claim_processing(
            claimed_ids,
            self.processing_version,
            include_failed=retry_failed,
        )
        if claimed != len(claimed_ids):
            eligible_events = [
                event
                for event in eligible_events
                if (status := self.store.processing_status(str(event["event_id"]))) is not None
                and status["status"] == "processing"
            ]
            claimed_ids = [str(event["event_id"]) for event in eligible_events]
        if not eligible_events:
            return {
                "requested": len(events),
                "processed": 0,
                "failed": 0,
                "skipped": len(events),
                "event_ids": event_ids,
                "state_rebuilt": False,
                "semantic_effects": 0,
            }

        max_sequence = max(int(event["sequence"]) for event in eligible_events)
        available_event_ids = self._available_event_ids(max_sequence)
        observations_added = 0
        relationships_added = 0
        completions_added = 0
        projection_rebuilt = False
        try:
            if self.provider is None:
                raise RuntimeError("no semantic provider is configured")
            prior_sequence = min(int(event["sequence"]) for event in eligible_events) - 1
            parsed = self.provider.extract(
                events=eligible_events,
                prior_snapshot=self.store.extraction_context(max_sequence=prior_sequence),
                contract=self.contract_document,
            )
            if not isinstance(parsed, dict):
                raise ValueError("semantic provider returned a non-object")
            observations, relationships = normalize_extraction(
                parsed,
                public_contract=self.public_contract,
                batch_event_ids=set(claimed_ids),
                available_event_ids=available_event_ids,
            )
            observations_added = self.store.add_observations(observations, self.extractor_version)
            relationships_added = self.store.add_relationships(relationships, self.extractor_version)
            recovered_count, _relation_version = self._relation_recovery()
            relationships_added += recovered_count
            projection = self.store.rebuild_projection(duplicate_evidence=self.duplicate_evidence)
            projection_rebuilt = True
            completions_added = self._completeness(eligible_events, available_event_ids)
            if completions_added:
                projection = self.store.rebuild_projection(duplicate_evidence=self.duplicate_evidence)
            self.store.mark_processed(
                claimed_ids,
                processing_version=self.processing_version,
                extractor_version=self.extractor_version,
                completion_version=DETERMINISTIC_COMPLETION_VERSION if self.completeness == "deterministic" else None,
                relation_recovery_version=_relation_version,
                duplicate_projection_version=(
                    DUPLICATE_EVIDENCE_PROJECTION_VERSION if self.duplicate_evidence else None
                ),
            )
            semantic_effects = observations_added + relationships_added + completions_added
            return {
                "requested": len(events),
                "processed": len(claimed_ids),
                "failed": 0,
                "skipped": len(events) - len(claimed_ids),
                "event_ids": event_ids,
                "processed_event_ids": claimed_ids,
                "observations_added": observations_added,
                "relationships_added": relationships_added,
                "completions_added": completions_added,
                "semantic_effects": semantic_effects,
                "projection_run_id": projection.get("projection_run_id"),
                "state_rebuilt": projection_rebuilt,
            }
        except Exception as error:
            failure = self._failure_text(error)
            if not projection_rebuilt:
                try:
                    self.store.rebuild_projection(duplicate_evidence=self.duplicate_evidence)
                    projection_rebuilt = True
                except Exception as rebuild_error:
                    failure = f"{failure}; projection rebuild failed: {self._failure_text(rebuild_error)}"
            self.store.mark_failed(
                claimed_ids,
                processing_version=self.processing_version,
                error=failure,
            )
            return {
                "requested": len(events),
                "processed": 0,
                "failed": len(claimed_ids),
                "skipped": len(events) - len(claimed_ids),
                "event_ids": event_ids,
                "failed_event_ids": claimed_ids,
                "error": failure,
                "observations_added": observations_added,
                "relationships_added": relationships_added,
                "completions_added": completions_added,
                "semantic_effects": 0,
                "state_rebuilt": projection_rebuilt,
            }

    @staticmethod
    def _aggregate(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
        result_list = list(results)
        keys = (
            "requested",
            "processed",
            "failed",
            "skipped",
            "observations_added",
            "relationships_added",
            "completions_added",
            "semantic_effects",
        )
        aggregate = {key: sum(int(result.get(key, 0)) for result in result_list) for key in keys}
        aggregate["state_rebuilt"] = any(bool(result.get("state_rebuilt")) for result in result_list)
        aggregate["batches"] = len(result_list)
        aggregate["errors"] = [result["error"] for result in result_list if result.get("error")]
        aggregate["processed_event_ids"] = [
            event_id
            for result in result_list
            for event_id in result.get("processed_event_ids", [])
        ]
        aggregate["failed_event_ids"] = [
            event_id
            for result in result_list
            for event_id in result.get("failed_event_ids", [])
        ]
        return aggregate

    def process_event(self, event_id: str, *, retry: bool = False) -> dict[str, Any]:
        """Process one capture, or explicitly retry one failed capture."""

        event = self.store.raw_event(event_id)
        if event is None:
            raise ValueError(f"unknown event: {event_id}")
        status = self.store.processing_status(event_id)
        if status is None:
            raise RuntimeError(f"processing state is missing for {event_id}")
        if status["status"] == "failed" and not retry:
            return {
                "requested": 1,
                "processed": 0,
                "failed": 1,
                "skipped": 1,
                "event_ids": [event_id],
                "error": status["last_error"],
                "state_rebuilt": False,
                "semantic_effects": 0,
            }
        if status["status"] in {"pending", "failed"}:
            earlier_unprocessed = [
                candidate
                for candidate in self.store.processing_events(statuses=("pending", "failed", "processing"))
                if candidate.get("event_id") != event_id
                and int(candidate.get("sequence", 0)) < int(event.get("sequence", 0))
            ]
            if earlier_unprocessed:
                return {
                    "requested": 1,
                    "processed": 0,
                    "failed": 0,
                    "skipped": 1,
                    "blocked": True,
                    "reason": "earlier captures must be processed first",
                    "event_ids": [event_id],
                    "state_rebuilt": False,
                    "semantic_effects": 0,
                }
        if status["status"] == "processing":
            return {
                "requested": 1,
                "processed": 0,
                "failed": 0,
                "skipped": 1,
                "event_ids": [event_id],
                "state_rebuilt": False,
                "semantic_effects": 0,
            }
        return self._process_batch([event], retry_failed=retry)

    def process_pending(self, *, limit: int | None = None) -> dict[str, Any]:
        """Process pending captures in chronological bounded batches."""

        events = self.store.processing_events(statuses=("pending",), limit=limit)
        results: list[dict[str, Any]] = []
        for start in range(0, len(events), self.batch_size):
            result = self._process_batch(events[start : start + self.batch_size])
            results.append(result)
            if result.get("failed"):
                # Do not process later captures after a failed earlier batch.
                break
        aggregate = self._aggregate(results)
        status = self.store.processing_status() or {"counts": {}}
        aggregate.update(
            {
                "pending_count": status.get("counts", {}).get("pending", 0),
                "failed_count": status.get("counts", {}).get("failed", 0),
                "state_fresh": status.get("counts", {}).get("pending", 0) == 0
                and status.get("counts", {}).get("failed", 0) == 0,
            }
        )
        return aggregate

    def retry_failed(self, event_id: str | None = None, *, limit: int | None = None) -> dict[str, Any]:
        """Retry failed captures in source order, preserving earlier pending order."""

        failed_events = self.store.processing_events(statuses=("failed",), limit=None)
        if event_id is not None:
            failed_events = [event for event in failed_events if event.get("event_id") == event_id]
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            failed_events = failed_events[:limit]
        if not failed_events:
            return {
                "requested": 0,
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "state_rebuilt": False,
                "semantic_effects": 0,
                "pending_count": (self.store.processing_status() or {"counts": {}}).get("counts", {}).get("pending", 0),
            }
        first_sequence = int(failed_events[0]["sequence"])
        earlier_pending = [
            event
            for event in self.store.processing_events(statuses=("pending", "failed"))
            if int(event.get("sequence", 0)) < first_sequence
            and event.get("event_id") not in {item.get("event_id") for item in failed_events}
        ]
        if earlier_pending:
            return {
                "requested": 0,
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "blocked": True,
                "reason": "earlier pending captures must be processed first",
                "event_ids": [event.get("event_id") for event in earlier_pending],
                "state_rebuilt": False,
                "semantic_effects": 0,
            }
        results: list[dict[str, Any]] = []
        for start in range(0, len(failed_events), self.batch_size):
            result = self._process_batch(
                failed_events[start : start + self.batch_size],
                retry_failed=True,
            )
            results.append(result)
            if result.get("failed"):
                break
        aggregate = self._aggregate(results)
        status = self.store.processing_status() or {"counts": {}}
        aggregate["pending_count"] = status.get("counts", {}).get("pending", 0)
        aggregate["failed_count"] = status.get("counts", {}).get("failed", 0)
        return aggregate

    def ensure_state_fresh(self) -> dict[str, Any]:
        """Process pending state for an Ask-like caller when freshness is needed."""

        before = self.store.processing_status() or {"counts": {}}
        if before.get("counts", {}).get("pending", 0) == 0:
            return {
                "processed": 0,
                "failed": 0,
                "state_rebuilt": False,
                "pending_count": before.get("counts", {}).get("pending", 0),
                "failed_count": before.get("counts", {}).get("failed", 0),
                "processing_count": before.get("counts", {}).get("processing", 0),
                "fresh": before.get("counts", {}).get("failed", 0) == 0
                and before.get("counts", {}).get("processing", 0) == 0,
            }
        result = self.process_pending()
        status = self.store.processing_status() or {"counts": {}}
        result["processing_count"] = status.get("counts", {}).get("processing", 0)
        result["fresh"] = result.get("pending_count", 0) == 0 and result.get("failed_count", 0) == 0 and result.get("processing_count", 0) == 0
        return result


__all__ = [
    "CodexCLIProvider",
    "INGESTION_EXTRACTOR_VERSION",
    "INGESTION_PROCESSING_VERSION",
    "IngestionEngine",
    "SemanticProvider",
]
