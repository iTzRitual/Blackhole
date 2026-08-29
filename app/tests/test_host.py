from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.codex_discovery import (
    ERROR,
    INSTALLED_NOT_AUTHENTICATED,
    MISSING,
    READY,
    ProviderStatus,
    discover_codex,
)
from app.host import HostRuntime
from app.runtime_config import RuntimeConfig, resolve_home


NEUTRAL_CONTRACT = {
    "response_contract": "neutral-host-test-v1",
    "unknown_reason": {"allowed_categories": ["not_stated", "conflicting", "missing"]},
    "public_ontology": {"subjects": [], "predicates": []},
    "value_normalization": {"object_field_aliases": {}, "enum_field_aliases": {}},
}


def discovery_status(
    status: str,
    *,
    installed: bool,
    authenticated: bool | None,
    ready: bool,
) -> ProviderStatus:
    return ProviderStatus(
        status=status,
        installed=installed,
        authenticated=authenticated,
        version="codex-cli 0.0.0-test" if installed else None,
        auth_check_available=installed,
        configured_runtime=True,
        ready=ready,
    )


class FakeDiscovery:
    def __init__(self, result: ProviderStatus) -> None:
        self.result = result
        self.calls: list[dict[str, str]] = []

    def __call__(self, **kwargs: str) -> ProviderStatus:
        self.calls.append(kwargs)
        return self.result


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.fail = False

    def extract(
        self,
        *,
        events: list[dict[str, object]],
        prior_snapshot: dict[str, object],
        contract: dict[str, object],
    ) -> dict[str, object]:
        del prior_snapshot, contract
        event_ids = [str(event["event_id"]) for event in events]
        self.calls.append(event_ids)
        if self.fail:
            raise RuntimeError("provider stderr would contain a secret token")
        return {
            "observations": [
                {
                    "event_id": event_id,
                    "subject": "inbox",
                    "predicate": "note",
                    "knowledge_status": "known",
                    "value": "captured",
                }
                for event_id in event_ids
            ],
            "relationships": [],
        }


class HostRuntimeTests(unittest.TestCase):
    def test_first_run_initializes_home_and_database_without_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "blackhole-home"
            discovery = FakeDiscovery(discovery_status(MISSING, installed=False, authenticated=None, ready=False))
            with HostRuntime.initialize(
                home,
                contract=NEUTRAL_CONTRACT,
                discovery_fn=discovery,
            ) as host:
                status = host.status()
                self.assertTrue(status["host"]["ready"])
                self.assertEqual(status["provider"]["status"], MISSING)
                self.assertTrue(host.config.config_path.exists())
                self.assertTrue(host.config.database_path.exists())
            self.assertEqual(len(discovery.calls), 1)

    def test_blackhole_home_override_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            override = Path(directory) / "override"
            with patch.dict(os.environ, {"BLACKHOLE_HOME": str(override)}):
                self.assertEqual(resolve_home(), override.resolve())
                config = RuntimeConfig.load_or_create()
            self.assertEqual(config.home, override.resolve())
            self.assertTrue((override / "config.json").exists())

    def test_codex_discovery_distinguishes_missing_and_ready(self) -> None:
        with patch("app.codex_discovery.shutil.which", return_value=None):
            missing = discover_codex(configured_model="gpt-5.6-luna", configured_reasoning="high")
        self.assertEqual(missing.status, MISSING)
        self.assertFalse(missing.ready)

        class Completed:
            def __init__(self, returncode: int, stdout: str, stderr: str = "") -> None:
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        with (
            patch("app.codex_discovery.shutil.which", return_value="codex"),
            patch(
                "app.codex_discovery.subprocess.run",
                side_effect=[
                    Completed(0, "codex-cli 0.150.0-alpha.12.2\n"),
                    Completed(0, "Logged in using ChatGPT\n"),
                ],
            ),
        ):
            ready = discover_codex(configured_model="gpt-5.6-luna", configured_reasoning="high")
        self.assertEqual(ready.status, READY)
        self.assertTrue(ready.authenticated)
        self.assertEqual(ready.version, "codex-cli 0.150.0-alpha.12.2")

        with (
            patch("app.codex_discovery.shutil.which", return_value="codex"),
            patch(
                "app.codex_discovery.subprocess.run",
                side_effect=[Completed(0, "codex-cli 0.1\n"), Completed(1, "Not logged in\n")],
            ),
        ):
            unauthenticated = discover_codex(configured_model="gpt-5.6-luna", configured_reasoning="high")
        self.assertEqual(unauthenticated.status, INSTALLED_NOT_AUTHENTICATED)
        self.assertFalse(unauthenticated.ready)

    def test_capture_and_processing_without_provider_preserve_raw_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            discovery = FakeDiscovery(discovery_status(MISSING, installed=False, authenticated=None, ready=False))
            with HostRuntime.open(
                Path(directory),
                contract=NEUTRAL_CONTRACT,
                discovery_fn=discovery,
            ) as host:
                saved = host.capture("A raw note that must not be lost.", event_id="host-no-provider-1")
                before = host.store.raw_event("host-no-provider-1")
                self.assertEqual(saved["processing_status"], "pending")
                self.assertEqual(before["payload"]["text"], "A raw note that must not be lost.")
                result = host.process_pending()
                self.assertEqual(result["failed"], 1)
                self.assertEqual(result["error"], "provider unavailable: Codex CLI not found")
                self.assertEqual(host.processing_status("host-no-provider-1")["status"], "failed")
                self.assertEqual(host.store.raw_event("host-no-provider-1"), before)

    def test_ready_provider_is_reported_without_a_semantic_probe(self) -> None:
        discovery = FakeDiscovery(discovery_status(READY, installed=True, authenticated=True, ready=True))
        with tempfile.TemporaryDirectory() as directory, HostRuntime.open(
            directory,
            contract=NEUTRAL_CONTRACT,
            discovery_fn=discovery,
        ) as host:
            status = host.status()
        self.assertEqual(status["provider"]["status"], READY)
        self.assertTrue(status["provider"]["ready"])
        self.assertEqual(len(discovery.calls), 1)

    def test_status_and_config_are_safe_machine_readable_values(self) -> None:
        discovery = FakeDiscovery(discovery_status(READY, installed=True, authenticated=True, ready=True))
        with tempfile.TemporaryDirectory() as directory, HostRuntime.open(
            directory,
            contract=NEUTRAL_CONTRACT,
            discovery_fn=discovery,
        ) as host:
            status = host.status()
            serialized = json.dumps(status)
            config_text = host.config.config_path.read_text(encoding="utf-8")
        for forbidden in ("api_key", "access_token", "cookie", "auth_path", "credential", "secret"):
            self.assertNotIn(forbidden, serialized.casefold())
            self.assertNotIn(forbidden, config_text.casefold())
        self.assertIn("database", status["host"])
        self.assertNotIn("stderr", status["provider"])

    def test_fake_processing_is_idempotent_through_host_runtime(self) -> None:
        provider = FakeProvider()
        discovery = FakeDiscovery(discovery_status(READY, installed=True, authenticated=True, ready=True))
        with tempfile.TemporaryDirectory() as directory, HostRuntime.open(
            directory,
            contract=NEUTRAL_CONTRACT,
            provider=provider,
            discovery_fn=discovery,
        ) as host:
            host.capture("first", event_id="host-idempotent-1")
            host.capture("second", event_id="host-idempotent-2")
            first = host.process_pending()
            snapshot = host.snapshot()
            second = host.process_pending()
            self.assertEqual(first["processed"], 2)
            self.assertEqual(second["processed"], 0)
            self.assertEqual(second["semantic_effects"], 0)
            self.assertEqual(provider.calls, [["host-idempotent-1", "host-idempotent-2"]])
            self.assertEqual(host.snapshot()["current_facts"], snapshot["current_facts"])

    def test_retry_is_explicit_and_provider_errors_are_redacted(self) -> None:
        provider = FakeProvider()
        provider.fail = True
        discovery = FakeDiscovery(discovery_status(READY, installed=True, authenticated=True, ready=True))
        with tempfile.TemporaryDirectory() as directory, HostRuntime.open(
            directory,
            contract=NEUTRAL_CONTRACT,
            provider=provider,
            discovery_fn=discovery,
        ) as host:
            host.capture("retry me", event_id="host-retry-1")
            failed = host.process_pending()
            self.assertEqual(failed["failed"], 1)
            self.assertEqual(failed["error"], "semantic provider failed; retry available")
            self.assertEqual(
                host.processing_status("host-retry-1")["last_error"],
                "semantic provider failed; retry available",
            )
            provider.fail = False
            retried = host.retry_failed()
            self.assertEqual(retried["processed"], 1)
            self.assertEqual(host.processing_status("host-retry-1")["status"], "processed")

    def test_configuration_persists_validated_non_sensitive_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = RuntimeConfig.defaults(directory)
            config.model = "gpt-5.6-luna"
            config.reasoning_effort = "max"
            config.timeout_seconds = 42
            config.batch_size = 3
            config.save()
            loaded = RuntimeConfig.load(config.config_path)
            self.assertEqual(loaded.model, config.model)
            self.assertEqual(loaded.reasoning_effort, "max")
            self.assertEqual(loaded.timeout_seconds, 42)
            self.assertEqual(loaded.batch_size, 3)
            self.assertNotIn("token", config.config_path.read_text(encoding="utf-8").casefold())

    def test_secret_fields_are_rejected_if_added_to_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps({"config_version": "blackhole-runtime-config-v1", "api_key": "should-not-exist"}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                RuntimeConfig.load(path)

    def test_database_state_survives_host_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            discovery = FakeDiscovery(discovery_status(READY, installed=True, authenticated=True, ready=True))
            with HostRuntime.open(home, contract=NEUTRAL_CONTRACT, discovery_fn=discovery) as first:
                first.capture("persisted raw input", event_id="host-restart-1")
                self.assertEqual(first.processing_status("host-restart-1")["status"], "pending")

            provider = FakeProvider()
            with HostRuntime.open(
                home,
                contract=NEUTRAL_CONTRACT,
                provider=provider,
                discovery_fn=discovery,
            ) as second:
                self.assertEqual(second.processing_status("host-restart-1")["status"], "pending")
                result = second.ensure_state_fresh()
                self.assertEqual(result["processed"], 1)

            with HostRuntime.open(home, contract=NEUTRAL_CONTRACT, discovery_fn=discovery) as final:
                self.assertEqual(final.processing_status("host-restart-1")["status"], "processed")
                self.assertEqual(final.store.raw_event("host-restart-1")["payload"]["text"], "persisted raw input")


if __name__ == "__main__":
    unittest.main()
