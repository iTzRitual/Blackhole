"""Blackhole Host runtime facade and backend-only command line entry point."""

from __future__ import annotations

import argparse
import copy
import json
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from app.codex_discovery import (
    ERROR,
    INSTALLED_NOT_AUTHENTICATED,
    MISSING,
    ProviderStatus,
    discover_codex,
)
from app.ingestion_engine import CodexCLIProvider, IngestionEngine, SemanticProvider
from app.ops_logging import ProductOpsLogger
from app.product_v2 import PRODUCT_RUNTIME_VERSION, ProductRuntime, product_database_path
from app.runtime_config import RuntimeConfig
from app.runtime_contract import runtime_contract
from app.state_store import StateStore


ROOT = Path(__file__).resolve().parents[1]
# Kept as a named public-contract loader for benchmark tooling and callers that
# explicitly request the frozen contract.  HostRuntime itself uses the
# benchmark-independent runtime contract by default.
DEFAULT_PUBLIC_CONTRACT = ROOT / "benchmark" / "dev" / "response-contract-v2.json"
HOST_VERSION = "blackhole-host-v1"


def load_public_contract(path: str | Path = DEFAULT_PUBLIC_CONTRACT) -> dict[str, Any]:
    """Load only the public ontology/response configuration, never expected output."""

    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("public response contract must be a JSON object")
    return value


def _provider_unavailable_message(status: ProviderStatus) -> str:
    if status.status == MISSING:
        return "provider unavailable: Codex CLI not found"
    if status.status == INSTALLED_NOT_AUTHENTICATED:
        return "provider unavailable: Codex CLI is not authenticated"
    if status.status == ERROR:
        return "provider unavailable: Codex CLI readiness check failed"
    return "provider unavailable: configured semantic provider is not ready"


class ProviderUnavailableError(RuntimeError):
    """Safe failure used when capture processing has no usable provider."""


class _UnavailableProvider:
    def __init__(self, status: ProviderStatus) -> None:
        self.message = _provider_unavailable_message(status)

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_snapshot: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del events, prior_snapshot, contract
        raise ProviderUnavailableError(self.message)


class _SafeProvider:
    """Prevent provider exception text from crossing the Host API boundary."""

    def __init__(self, provider: SemanticProvider) -> None:
        self.provider = provider

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_snapshot: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            return self.provider.extract(
                events=events,
                prior_snapshot=prior_snapshot,
                contract=contract,
            )
        except ProviderUnavailableError:
            raise
        except Exception as error:
            del error
            raise RuntimeError("semantic provider failed; retry available") from None


def _safe_error(value: Any) -> str:
    text = str(value or "").casefold()
    if "provider unavailable" in text:
        if "not found" in text:
            return "provider unavailable: Codex CLI not found"
        if "not authenticated" in text:
            return "provider unavailable: Codex CLI is not authenticated"
        return "provider unavailable: configured semantic provider is not ready"
    if "provider" in text or "codex" in text:
        return "semantic provider failed; retry available"
    return "processing failed; retry available"


def _safe_processing_value(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    result = copy.deepcopy(value)
    if result.get("last_error"):
        result["last_error"] = _safe_error(result["last_error"])
    return result


def _safe_processing_payload(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    result = copy.deepcopy(value)
    if isinstance(result.get("processing"), dict):
        result["processing"] = _safe_processing_payload(result["processing"])
    if isinstance(result.get("events"), list):
        result["events"] = [
            _safe_processing_value(item) if isinstance(item, dict) else item
            for item in result["events"]
        ]
    elif "event_id" in result:
        return _safe_processing_value(result)
    return result


def _safe_product_result(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    if isinstance(result.get("processing"), dict):
        result["processing"] = _safe_processing_payload(result["processing"])
    return result


def _safe_result(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    if result.get("error"):
        result["error"] = _safe_error(result["error"])
    if isinstance(result.get("errors"), list):
        result["errors"] = [_safe_error(error) for error in result["errors"]]
        if result["errors"] and not result.get("error"):
            result["error"] = result["errors"][0]
    return result


class HostRuntime:
    """Blackhole-owned runtime boundary suitable for a future transport layer."""

    def __init__(
        self,
        config: RuntimeConfig,
        *,
        contract: dict[str, Any] | None = None,
        provider: SemanticProvider | None = None,
        discovery_fn: Callable[..., ProviderStatus] | None = None,
        clock: Callable[[], datetime] | None = None,
        auto_start_product_worker: bool = True,
        store: StateStore | None = None,
        _managed: bool = False,
        ops_logger: ProductOpsLogger | None = None,
    ) -> None:
        config.validate()
        self.config = config
        self.contract = copy.deepcopy(contract if contract is not None else runtime_contract())
        self._provider = provider
        self._discovery_fn = discovery_fn or discover_codex
        self._clock = clock
        self._auto_start_product_worker = auto_start_product_worker
        self._provider_status_cache: ProviderStatus | None = None
        self._lock = threading.RLock()
        self._managed = _managed
        self.ops_logger = ops_logger
        self._product_runtime: ProductRuntime | None = None
        self.store = store or StateStore(config.database_path)
        self._owns_store = store is None
        self.engine = IngestionEngine(
            contract=self.contract,
            provider=provider,
            store=self.store,
            batch_size=config.batch_size,
        )

    @classmethod
    def open(
        cls,
        home: str | Path | None = None,
        *,
        contract: dict[str, Any] | None = None,
        provider: SemanticProvider | None = None,
        discovery_fn: Callable[..., ProviderStatus] | None = None,
        clock: Callable[[], datetime] | None = None,
        auto_start_product_worker: bool = True,
        ops_logger: ProductOpsLogger | None = None,
    ) -> "HostRuntime":
        config = RuntimeConfig.load_or_create(home)
        config.home.mkdir(parents=True, exist_ok=True)
        return cls(
            config,
            contract=contract,
            provider=provider,
            discovery_fn=discovery_fn,
            clock=clock,
            auto_start_product_worker=auto_start_product_worker,
            ops_logger=ops_logger,
        )

    initialize = open

    def close(self) -> None:
        if self._managed:
            return
        self.shutdown()

    def shutdown(self) -> None:
        """Close all owned Product V2/V1 resources, including a worker."""

        product = self._product_runtime
        self._product_runtime = None
        if product is not None:
            product.close()
        if self._owns_store:
            self.store.close()

    def __enter__(self) -> "HostRuntime":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _provider_status(self, *, refresh: bool = False) -> ProviderStatus:
        if self._provider_status_cache is not None and not refresh:
            return self._provider_status_cache
        try:
            discovered = self._discovery_fn(
                configured_model=self.config.model,
                configured_reasoning=self.config.reasoning_effort,
            )
            if isinstance(discovered, dict):
                discovered = ProviderStatus.from_dict(discovered)
            elif isinstance(discovered, ProviderStatus):
                discovered = ProviderStatus.from_dict(discovered.to_dict())
            if not isinstance(discovered, ProviderStatus):
                raise TypeError("discovery did not return ProviderStatus")
        except Exception as error:
            del error
            discovered = ProviderStatus(
                status=ERROR,
                installed=False,
                authenticated=None,
                version=None,
                auth_check_available=False,
                configured_runtime=False,
                ready=False,
                error_code="discovery_failed",
            )
        self._provider_status_cache = discovered
        return discovered

    def status(self, *, refresh_provider: bool = False) -> dict[str, Any]:
        with self._lock:
            processing = self.store.processing_status() or {"counts": {}}
            counts = processing.get("counts", {})
            product = self.product_runtime
            product_processing = product.processing_status() or {"counts": {}}
            product_counts = product_processing.get("counts", {})
            return {
                "host": {
                    "ready": True,
                    "version": HOST_VERSION,
                    "database": str(self.config.database_path),
                },
                "provider": self._provider_status(refresh=refresh_provider).to_dict(),
                "processing": {
                    "pending": int(counts.get("pending", 0)),
                    "processing": int(counts.get("processing", 0)),
                    "processed": int(counts.get("processed", 0)),
                    "failed": int(counts.get("failed", 0)),
                },
                "product": {
                    "version": PRODUCT_RUNTIME_VERSION,
                    "database": str(product.store.path),
                    "processing": {
                        "pending": int(product_counts.get("pending", 0)),
                        "processing": int(product_counts.get("processing", 0)),
                        "processed": int(product_counts.get("processed", 0)),
                        "failed": int(product_counts.get("failed", 0)),
                    },
                },
            }

    def doctor(self) -> dict[str, Any]:
        """Return safe installation diagnostics without semantic inference."""

        state = self.status(refresh_provider=True)
        database_exists = self.config.database_path.exists()
        try:
            self.store.connection.execute("SELECT 1").fetchone()
            database_readable = True
        except Exception:
            database_readable = False
        return {
            "host": state["host"],
            "home": {
                "path": str(self.config.home),
                "exists": self.config.home.exists(),
            },
            "config": {
                "path": str(self.config.config_path),
                "exists": self.config.config_path.exists(),
                "version": self.config.version,
            },
            "database": {
                "path": str(self.config.database_path),
                "exists": database_exists,
                "readable": database_readable,
            },
            "provider": state["provider"],
            "processing": state["processing"],
        }

    def capture(self, payload: str | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Append an immutable capture without invoking a semantic provider."""

        with self._lock:
            return self.engine.capture(payload, **kwargs)

    @property
    def product_runtime(self) -> ProductRuntime:
        """Lazily open the separate Product V2 store and background worker."""

        with self._lock:
            if self._product_runtime is None:
                self._product_runtime = ProductRuntime(
                    self.config.home,
                    db_path=product_database_path(self.config.home),
                    provider=self._provider,
                    discovery_fn=self._discovery_fn,
                    model=self.config.model,
                    reasoning_effort=self.config.reasoning_effort,
                    timeout_seconds=self.config.timeout_seconds,
                    batch_size=self.config.batch_size,
                    start_worker=False,
                    auto_start_on_capture=self._auto_start_product_worker,
                    clock=self._clock,
                    ops_logger=self.ops_logger,
                )
            return self._product_runtime

    def start_product_worker(self) -> None:
        """Start the managed Product V2 worker for normal Host lifecycles."""

        with self._lock:
            self.product_runtime.start_worker()

    def product_capture(self, text: str | None = None, **kwargs: Any) -> dict[str, Any]:
        return self.product_runtime.capture(text, **kwargs)

    def product_processing_status(self, event_id: str | None = None) -> dict[str, Any] | None:
        value = self.product_runtime.processing_status(event_id)
        if event_id is not None:
            return _safe_processing_value(value)
        if value is None:
            return None
        result = copy.deepcopy(value)
        result["events"] = [
            _safe_processing_value(item) for item in result.get("events", [])
        ]
        return result

    def product_state(self) -> dict[str, Any]:
        return _safe_processing_payload(self.product_runtime.state())

    def product_process_pending(self, *, limit: int | None = None) -> dict[str, Any]:
        return self.product_runtime.process_pending(limit=limit)

    def product_retry_failed(self, event_id: str | None = None, *, limit: int | None = None) -> dict[str, Any]:
        return self.product_runtime.retry_failed(event_id, limit=limit)

    def product_ask(self, question: str) -> dict[str, Any]:
        return _safe_product_result(self.product_runtime.ask(question))

    def product_forget(self, event_id: str, *, reason: str = "user undo") -> dict[str, Any]:
        return self.product_runtime.forget(event_id, reason=reason)

    def product_retract(self, event_id: str, *, reason: str = "user undo") -> dict[str, Any]:
        """Compatibility name for the permanent Product V2 Undo operation."""

        return self.product_forget(event_id, reason=reason)

    def product_set_attention_status(
        self,
        fingerprint: str,
        status: str,
        *,
        note: str | None = None,
    ) -> dict[str, Any]:
        return self.product_runtime.set_attention_status(fingerprint, status, note=note)

    def product_attachment_bytes(self, sha256: str) -> tuple[bytes, dict[str, Any]]:
        return self.product_runtime.attachment_bytes(sha256)

    def processing_status(self, event_id: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            value = self.store.processing_status(event_id)
            if event_id is not None:
                return _safe_processing_value(value)
            if value is None:
                return None
            result = copy.deepcopy(value)
            result["events"] = [
                _safe_processing_value(item) for item in result.get("events", [])
            ]
            return result

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self.store.snapshot()

    def state(self) -> dict[str, Any]:
        """Alias for the rebuildable state view used by future clients."""

        return self.snapshot()

    def _work_counts(self) -> dict[str, int]:
        status = self.store.processing_status() or {"counts": {}}
        return {key: int(status.get("counts", {}).get(key, 0)) for key in ("pending", "failed")}

    def _selected_provider(self) -> tuple[SemanticProvider, CodexCLIProvider | None]:
        if self._provider is not None:
            return _SafeProvider(self._provider), None
        status = self._provider_status(refresh=True)
        if not status.ready:
            return _UnavailableProvider(status), None
        try:
            provider = CodexCLIProvider(
                timeout=self.config.timeout_seconds,
                model=self.config.model,
                reasoning_effort=self.config.reasoning_effort,
            )
        except Exception:
            return _UnavailableProvider(
                ProviderStatus(
                    status=ERROR,
                    installed=True,
                    authenticated=True,
                    version=status.version,
                    auth_check_available=status.auth_check_available,
                    configured_runtime=status.configured_runtime,
                    ready=False,
                    error_code="provider_initialization_failed",
                )
            ), None
        return _SafeProvider(provider), provider

    def _run_with_provider(self, operation: str, **kwargs: Any) -> dict[str, Any]:
        selected, owned_provider = self._selected_provider()
        try:
            with self._lock:
                previous = self.engine.provider
                self.engine.provider = selected
                try:
                    result = getattr(self.engine, operation)(**kwargs)
                finally:
                    self.engine.provider = previous
            return _safe_result(result)
        finally:
            if owned_provider is not None:
                owned_provider.close()

    def process_pending(self, *, limit: int | None = None) -> dict[str, Any]:
        counts = self._work_counts()
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")
        if counts["pending"] == 0 or limit == 0:
            with self._lock:
                return _safe_result(self.engine.process_pending(limit=limit))
        return self._run_with_provider("process_pending", limit=limit)

    def retry_failed(self, event_id: str | None = None, *, limit: int | None = None) -> dict[str, Any]:
        counts = self._work_counts()
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative")
        if counts["failed"] == 0 or limit == 0:
            with self._lock:
                return _safe_result(self.engine.retry_failed(event_id, limit=limit))
        return self._run_with_provider("retry_failed", event_id=event_id, limit=limit)

    def ensure_state_fresh(self) -> dict[str, Any]:
        if self._work_counts()["pending"] == 0:
            with self._lock:
                return _safe_result(self.engine.ensure_state_fresh())
        return self._run_with_provider("ensure_state_fresh")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, help="Blackhole data directory (or use BLACKHOLE_HOME)")
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit machine-readable JSON")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="initialize Blackhole Home and the SQLite database")
    commands.add_parser("status", help="show safe host, provider, and processing status")
    commands.add_parser("doctor", help="run safe local readiness checks")
    process = commands.add_parser("process", help="process pending captures")
    process.add_argument("--limit", type=int)
    retry = commands.add_parser("retry", help="retry failed captures")
    retry.add_argument("--event-id")
    retry.add_argument("--limit", type=int)
    return parser


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _print_init(status: dict[str, Any]) -> None:
    provider = status["provider"]
    print("Blackhole")
    print("[ok] data directory ready")
    print("[ok] database initialized")
    if provider["installed"]:
        print("[ok] Codex CLI detected")
    else:
        print("[!!] Codex CLI not found")
    if provider["ready"]:
        print("[ok] Codex authenticated and ready")
    elif provider["installed"]:
        print("[!!] Codex semantic processing is unavailable")
    print()
    print("Blackhole Host is ready.")
    if not provider["ready"]:
        print("Capture is available; semantic processing requires an authenticated Codex CLI.")


def _print_processing(command: str, result: dict[str, Any]) -> None:
    print("Blackhole")
    print(f"{command}: {int(result.get('processed', 0))} processed")
    if result.get("failed"):
        print(f"{int(result['failed'])} failed: {result.get('error', 'retry available')}")
    elif result.get("failed_count"):
        print(f"{int(result['failed_count'])} failed captures remain; retry is available")
    elif result.get("pending_count"):
        print(f"{int(result['pending_count'])} pending captures remain")
    else:
        print("state is fresh")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        with HostRuntime.open(home=args.home) as host:
            if args.command == "init":
                status = host.status(refresh_provider=True)
                if args.json_output:
                    _print_json(status)
                else:
                    _print_init(status)
                return 0
            if args.command == "status":
                _print_json(host.status())
                return 0
            if args.command == "doctor":
                _print_json(host.doctor())
                return 0
            if args.command == "process":
                if args.limit is not None and args.limit < 0:
                    raise ValueError("--limit must be non-negative")
                result = host.process_pending(limit=args.limit)
                if args.json_output:
                    _print_json(result)
                else:
                    _print_processing("process", result)
                return 1 if result.get("failed") or result.get("failed_count") else 0
            if args.command == "retry":
                if args.limit is not None and args.limit < 0:
                    raise ValueError("--limit must be non-negative")
                result = host.retry_failed(args.event_id, limit=args.limit)
                if args.json_output:
                    _print_json(result)
                else:
                    _print_processing("retry", result)
                return 1 if result.get("failed") or result.get("failed_count") else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Blackhole Host error: {error}")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["DEFAULT_PUBLIC_CONTRACT", "HOST_VERSION", "HostRuntime", "load_public_contract", "main"]
