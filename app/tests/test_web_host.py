from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from unittest.mock import patch

from app.codex_discovery import MISSING, READY, ProviderStatus
from app.host import HostRuntime
from app.state_store import StateStore
from app.web_app import create_server


NEUTRAL_CONTRACT = {
    "response_contract": "neutral-host-http-v1",
    "unknown_reason": {"allowed_categories": ["conflicting", "missing", "not_stated"]},
    "public_ontology": {"subjects": [], "predicates": []},
    "value_normalization": {"object_field_aliases": {}, "enum_field_aliases": {}},
}


def provider_status(status: str, *, ready: bool) -> ProviderStatus:
    installed = status == READY
    return ProviderStatus(
        status=status,
        installed=installed,
        authenticated=True if installed else None,
        version="codex-cli 0.0.0-test" if installed else None,
        auth_check_available=installed,
        configured_runtime=True,
        ready=ready,
    )


class FakeDiscovery:
    def __init__(self, status: ProviderStatus) -> None:
        self.status = status
        self.calls = 0

    def __call__(self, **_kwargs: str) -> ProviderStatus:
        self.calls += 1
        return self.status


class NeutralProvider:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.fail = False

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_snapshot: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_snapshot, contract
        if self.fail:
            raise RuntimeError("provider stderr contained secret-token-value")
        event_ids = [str(event["event_id"]) for event in events]
        self.calls.append(event_ids)
        observations: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []
        price_events: list[str] = []
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", "")).casefold()
            if "18 eur" in text:
                price_events.append(event_id)
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "Northstar Cloud",
                        "predicate": "current_price",
                        "knowledge_status": "known",
                        "value": {"amount": "18", "currency": "EUR", "billing_period": "month"},
                        "operation": "set",
                    }
                )
            elif "22 eur" in text:
                price_events.append(event_id)
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "Northstar Cloud",
                        "predicate": "current_price",
                        "knowledge_status": "known",
                        "value": {"amount": "22", "currency": "EUR", "billing_period": "month"},
                        "operation": "supersede",
                        "supersedes_event_id": next(iter(price_events), None),
                    }
                )
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "Northstar Cloud",
                        "predicate": "price_effective",
                        "knowledge_status": "known",
                        "value": "2027-03-01",
                    }
                )
            elif "sometime in november" in text:
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "Northstar Cloud",
                        "predicate": "renewal_date",
                        "knowledge_status": "unknown",
                        "unknown_reason": "not stated",
                    }
                )
            else:
                observations.append(
                    {
                        "event_id": event_id,
                        "subject": "inbox",
                        "predicate": "note",
                        "knowledge_status": "known",
                        "value": "captured",
                    }
                )
        if len(price_events) >= 2:
            relationships.append(
                {
                    "source_event_id": price_events[-1],
                    "target_event_id": price_events[-2],
                    "relation_type": "meaningful_change",
                    "changed_fields": ["current_price"],
                }
            )
        return {"observations": observations, "relationships": relationships}


class RunningServer:
    def __init__(self, **kwargs: Any) -> None:
        self.server = create_server("127.0.0.1", 0, **kwargs)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def close(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        with error:
            return error.code, json.loads(error.read().decode("utf-8"))


class HostWebTests(unittest.TestCase):
    def test_health_is_cheap_and_pwa_assets_are_served(self) -> None:
        discovery = FakeDiscovery(provider_status(MISSING, ready=False))
        with tempfile.TemporaryDirectory() as directory:
            running = RunningServer(home=Path(directory), contract=NEUTRAL_CONTRACT, discovery_fn=discovery)
            try:
                status, health = request_json(running.base_url, "/api/health")
                self.assertEqual(status, 200)
                self.assertEqual(health["host"], True)
                self.assertEqual(discovery.calls, 0)
                for path, content_type in (
                    ("/", "text/html"),
                    ("/manifest.webmanifest", "application/manifest+json"),
                    ("/sw.js", "application/javascript"),
                    ("/icons/icon.svg", "image/svg+xml"),
                ):
                    with urllib.request.urlopen(f"{running.base_url}{path}", timeout=10) as response:
                        self.assertEqual(response.status, 200)
                        self.assertTrue(response.headers["Content-Type"].startswith(content_type))
                with urllib.request.urlopen(f"{running.base_url}/sw.js", timeout=10) as response:
                    service_worker = response.read().decode("utf-8")
                self.assertIn("url.pathname.startsWith(\"/api/\")", service_worker)
            finally:
                running.close()

    def test_status_capture_and_state_are_host_owned_before_processing(self) -> None:
        provider = NeutralProvider()
        discovery = FakeDiscovery(provider_status(READY, ready=True))
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            running = RunningServer(home=home, contract=NEUTRAL_CONTRACT, provider=provider, discovery_fn=discovery)
            try:
                status, payload = request_json(running.base_url, "/api/host/status")
                self.assertEqual(status, 200)
                self.assertTrue(payload["status"]["host"]["ready"])
                serialized_status = json.dumps(payload)
                self.assertNotIn("secret-token", serialized_status)
                self.assertNotIn("stderr", serialized_status.casefold())

                status, saved = request_json(
                    running.base_url,
                    "/api/capture",
                    method="POST",
                    body={"text": "Northstar Cloud costs 18 EUR per month."},
                )
                self.assertEqual(status, 200)
                self.assertTrue(saved["saved"])
                self.assertEqual(saved["processing"]["status"], "pending")
                self.assertEqual(provider.calls, [])

                status, processing = request_json(running.base_url, "/api/processing")
                self.assertEqual(status, 200)
                self.assertEqual(processing["processing"]["counts"]["pending"], 1)
                status, before = request_json(running.base_url, "/api/state")
                self.assertEqual(status, 200)
                self.assertEqual(before["state"]["counts"]["captures"], 1)
                self.assertFalse(any(item["subject"] == "northstar_cloud" for item in before["state"]["memory"]["subscriptions"]))
                with HostRuntime.open(home, contract=NEUTRAL_CONTRACT, provider=provider, discovery_fn=discovery) as host:
                    raw = host.store.raw_events()
                self.assertEqual(raw[0]["payload"]["text"], "Northstar Cloud costs 18 EUR per month.")
            finally:
                running.close()

    def test_ask_refreshes_once_and_answers_from_updated_state(self) -> None:
        provider = NeutralProvider()
        discovery = FakeDiscovery(provider_status(READY, ready=True))
        with tempfile.TemporaryDirectory() as directory:
            running = RunningServer(
                home=Path(directory),
                contract=NEUTRAL_CONTRACT,
                provider=provider,
                discovery_fn=discovery,
            )
            try:
                for text in (
                    "Northstar Cloud costs 18 EUR per month.",
                    "Northstar Cloud will cost 22 EUR per month from 2027-03-01.",
                ):
                    status, _payload = request_json(
                        running.base_url,
                        "/api/capture",
                        method="POST",
                        body={"text": text},
                    )
                    self.assertEqual(status, 200)
                status, answer_payload = request_json(
                    running.base_url,
                    "/api/query",
                    method="POST",
                    body={"question": "What subscription price changes do I know?"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(len(provider.calls), 1)
                self.assertEqual(answer_payload["answer"]["mode"], "subscription_history")
                assertions = answer_payload["answer"]["sections"][0]["assertions"]
                amounts = {item.get("value", {}).get("amount") for item in assertions if isinstance(item.get("value"), dict)}
                self.assertEqual(amounts, {"18", "22"})

                status, state_payload = request_json(running.base_url, "/api/state")
                self.assertEqual(status, 200)
                current = state_payload["state"]["memory"]["subscriptions"]
                current_prices = [item for item in current if item["predicate"] == "current_price"]
                self.assertEqual(current_prices[0]["value"]["amount"], "22")

                status, second = request_json(
                    running.base_url,
                    "/api/query",
                    method="POST",
                    body={"question": "What subscription price changes do I know?"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(len(provider.calls), 1)
                self.assertEqual(second["answer"]["mode"], "subscription_history")
            finally:
                running.close()

    def test_provider_unavailable_keeps_pending_failure_safe_and_existing_state_queryable(self) -> None:
        discovery = FakeDiscovery(provider_status(MISSING, ready=False))
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            running = RunningServer(home=home, contract=NEUTRAL_CONTRACT, discovery_fn=discovery)
            try:
                status, _payload = request_json(
                    running.base_url,
                    "/api/capture",
                    method="POST",
                    body={"text": "Northstar Cloud costs 18 EUR per month."},
                )
                self.assertEqual(status, 200)
                status, failed = request_json(
                    running.base_url,
                    "/api/query",
                    method="POST",
                    body={"question": "What are my subscriptions?"},
                )
                self.assertEqual(status, 409)
                self.assertEqual(failed["code"], "state_not_fresh")
                self.assertEqual(failed["failure_code"], "provider_unavailable")
                self.assertTrue(failed["state_available"])
                self.assertNotIn("secret-token", json.dumps(failed))
                with StateStore(home / "blackhole.db") as store:
                    self.assertEqual(len(store.raw_events()), 1)
                status, existing = request_json(
                    running.base_url,
                    "/api/query",
                    method="POST",
                    body={"question": "What are my subscriptions?"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(existing["answer"]["mode"], "subscriptions")
            finally:
                running.close()

    def test_process_failure_retry_and_no_secret_or_auth_surface(self) -> None:
        provider = NeutralProvider()
        provider.fail = True
        discovery = FakeDiscovery(provider_status(READY, ready=True))
        with tempfile.TemporaryDirectory() as directory:
            running = RunningServer(
                home=Path(directory),
                contract=NEUTRAL_CONTRACT,
                provider=provider,
                discovery_fn=discovery,
            )
            try:
                request_json(running.base_url, "/api/capture", method="POST", body={"text": "retry this"})
                status, failure = request_json(running.base_url, "/api/process", method="POST", body={})
                self.assertEqual(status, 500)
                self.assertEqual(failure["code"], "processing_failed")
                self.assertNotIn("secret-token", json.dumps(failure))
                provider.fail = False
                status, retried = request_json(running.base_url, "/api/retry", method="POST", body={})
                self.assertEqual(status, 200)
                self.assertEqual(retried["processing"]["processed"], 1)
                status, auth_path = request_json(running.base_url, "/api/auth", method="GET")
                self.assertEqual(status, 404)
                self.assertNotIn("token", json.dumps(auth_path).casefold())
            finally:
                running.close()

    def test_query_failure_is_bounded_and_reports_state_availability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            running = RunningServer(home=Path(directory), contract=NEUTRAL_CONTRACT)
            try:
                with patch("app.web_app.answer_question_from_snapshot", side_effect=RuntimeError("internal detail")):
                    status, failure = request_json(
                        running.base_url,
                        "/api/query",
                        method="POST",
                        body={"question": "What are my subscriptions?"},
                    )
                self.assertEqual(status, 500)
                self.assertEqual(failure["code"], "query_failed")
                self.assertTrue(failure["state_available"])
                self.assertNotIn("internal detail", json.dumps(failure))
            finally:
                running.close()

    def test_invalid_question_traversal_and_non_loopback_bind_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            running = RunningServer(home=home, contract=NEUTRAL_CONTRACT)
            try:
                status, invalid = request_json(running.base_url, "/api/query", method="POST", body={"question": ""})
                self.assertEqual(status, 400)
                self.assertEqual(invalid["code"], "invalid_question")
                status, traversal = request_json(running.base_url, "/..%2Fapp.py")
                self.assertEqual(status, 404)
                self.assertEqual(traversal["code"], "not_found")
            finally:
                running.close()
            with self.assertRaises(ValueError):
                create_server("0.0.0.0", 0, home=home)
            trusted = create_server("0.0.0.0", 0, home=home, trusted_lan_demo=True)
            trusted.server_close()


if __name__ == "__main__":
    unittest.main()
