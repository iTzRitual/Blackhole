from __future__ import annotations

import base64
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.tests.test_product_v2 import ProductFakeProvider
from app.web_app import create_server


class AskThreadProvider:
    def __init__(self) -> None:
        self.answer_contexts: list[dict[str, Any]] = []

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, time_context, contract
        return {
            "facts": [
                {
                    "event_id": str(event["event_id"]),
                    "entity": "car",
                    "concept": "condition",
                    "knowledge_status": "known",
                    "value": "knocking at the front left",
                }
                for event in events
            ]
        }

    def answer(
        self,
        *,
        question: str,
        context: dict[str, Any],
        time_context: dict[str, Any],
    ) -> dict[str, Any]:
        del question, time_context
        self.answer_contexts.append(context)
        evidence_ids = [
            item["evidence_id"]
            for item in context.get("facts", [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        ]
        return {"answer": "A bounded provider summary.", "evidence_ids": evidence_ids[:1]}


class ProductV2HttpTests(unittest.TestCase):
    @staticmethod
    def request(
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
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.loads(error.read().decode("utf-8"))

    def test_get_state_is_read_only_for_provider_and_v2_capture_supports_undo_and_blob_get(self) -> None:
        content = b"attachment-only"
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            server = create_server("127.0.0.1", 0, home=Path(directory), provider=provider)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                status, before = self.request(base_url, "/api/v2/state")
                self.assertEqual(status, 200)
                self.assertEqual(provider.calls, [])
                self.assertEqual(before["state"]["counts"]["captures"], 0)

                status, rejected = self.request(
                    base_url,
                    "/api/v2/capture",
                    method="POST",
                    body={"attachment": {"path": "C:\\Windows\\secret.txt"}},
                )
                self.assertEqual(status, 400)
                self.assertEqual(rejected["code"], "invalid_request")
                self.assertEqual(provider.calls, [])

                status, saved = self.request(
                    base_url,
                    "/api/v2/capture",
                    method="POST",
                    body={
                        "event_id": "v2-http-1",
                        "attachment": {
                            "filename": "note.txt",
                            "mime_type": "text/plain",
                            "data_base64": base64.b64encode(content).decode("ascii"),
                        },
                    },
                )
                self.assertEqual(status, 200)
                self.assertTrue(saved["saved"])
                digest = saved["capture"]["attachments"][0]["sha256"]
                self.assertEqual(saved["capture"]["attachments"][0]["blob_ref"], f"sha256:{digest}")
                self.assertEqual(saved["processing"]["status"], "pending")

                for _ in range(100):
                    status, processing = self.request(base_url, "/api/v2/processing")
                    self.assertEqual(status, 200)
                    if processing["processing"]["counts"]["processed"] == 1:
                        break
                    time.sleep(0.01)
                self.assertEqual(processing["processing"]["counts"]["processed"], 1)
                with urllib.request.urlopen(f"{base_url}/api/v2/attachments/{digest}", timeout=5) as response:
                    self.assertEqual(response.read(), content)

                status, retracted = self.request(
                    base_url,
                    "/api/v2/retract",
                    method="POST",
                    body={"event_id": "v2-http-1"},
                )
                self.assertEqual(status, 200)
                self.assertTrue(retracted["retraction"]["retracted"])
                status, after = self.request(base_url, "/api/v2/state")
                self.assertEqual(status, 200)
                self.assertEqual(after["state"]["counts"]["active_captures"], 0)
            finally:
                server.shutdown()
                server.server_close()

    def test_product_ask_is_post_and_uses_provider_for_cost_question(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            server = create_server("127.0.0.1", 0, home=Path(directory), provider=provider)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                self.request(
                    base_url,
                    "/api/v2/capture",
                    method="POST",
                    body={"text": "PocketWave costs 9 EUR monthly."},
                )
                for _ in range(100):
                    _status, state = self.request(base_url, "/api/v2/state")
                    if state["state"]["counts"]["facts"]:
                        break
                    time.sleep(0.01)
                status, answer = self.request(
                    base_url,
                    "/api/v2/ask",
                    method="POST",
                    body={"question": "What am I paying for?"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(answer["answer"]["mode"], "costs")
                self.assertTrue(answer["answer"]["provider_used"])
                self.assertEqual(provider.answer_calls, 1)
            finally:
                server.shutdown()
                server.server_close()

    def test_product_ask_accepts_bounded_thread_context_without_persisting_it_as_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = AskThreadProvider()
            server = create_server("127.0.0.1", 0, home=Path(directory), provider=provider)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                self.request(
                    base_url,
                    "/api/v2/capture",
                    method="POST",
                    body={"event_id": "http-thread-car", "text": "My car is knocking."},
                )
                for _ in range(100):
                    _status, state = self.request(base_url, "/api/v2/state")
                    if state["state"]["counts"]["facts"]:
                        break
                    time.sleep(0.01)
                thread_context = [
                    {"role": "user", "text": "What do I know about my car?"},
                    {"role": "assistant", "text": "The car is knocking at the front left."},
                ] + [{"role": "user", "text": f"A later conversational aside {index}"} for index in range(6)]
                status, answer = self.request(
                    base_url,
                    "/api/v2/ask",
                    method="POST",
                    body={"question": "What does that mean?", "thread": thread_context},
                )
                self.assertEqual(status, 200)
                self.assertTrue(answer["answer"]["provider_used"])
                sent_thread = provider.answer_contexts[-1]["thread"]
                self.assertEqual(len(sent_thread), 8)
                self.assertTrue(any(item["role"] == "assistant" for item in sent_thread))
                self.assertTrue(all(set(item) == {"role", "text"} for item in sent_thread))
                self.assertFalse(any("evidence_id" in item for item in sent_thread))
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
