from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
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


REPO_ROOT = Path(__file__).resolve().parents[2]


class ProductV2HumanDogfoodRegressionTests(unittest.TestCase):
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
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.loads(error.read().decode("utf-8"))

    @staticmethod
    def command_json(*args: str) -> dict[str, Any]:
        result = subprocess.run(
            [sys.executable, *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if result.returncode != 0:
            raise AssertionError(f"command failed ({result.returncode}): {result.stdout}\n{result.stderr}")
        return json.loads(result.stdout)

    def test_normal_launch_processes_v2_queue_without_v1_or_manual_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            provider = ProductFakeProvider()
            provider.block_started = threading.Event()
            provider.block_release = threading.Event()
            server = create_server("127.0.0.1", 0, home=home, provider=provider)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                started = time.monotonic()
                status, saved = self.request(
                    base_url,
                    "/api/v2/capture",
                    method="POST",
                    body={
                        "event_id": "human-dogfood-delayed-1",
                        "text": "Odbieram dzieci za 10 minut.",
                    },
                )
                elapsed = time.monotonic() - started
                self.assertEqual(status, 200)
                self.assertTrue(saved["saved"])
                self.assertLess(elapsed, 0.5)
                self.assertIn(saved["processing"]["status"], {"pending", "processing"})
                self.assertTrue(provider.block_started.wait(timeout=2))

                status, processing = self.request(base_url, "/api/v2/processing")
                self.assertEqual(status, 200)
                counts = processing["processing"]["counts"]
                self.assertGreaterEqual(int(counts["processing"]), 1)
                self.assertEqual(int(counts["processed"]), 0)

                status, blocked_ask = self.request(
                    base_url,
                    "/api/v2/ask",
                    method="POST",
                    body={"question": "What do I need to do today?"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(blocked_ask["answer"]["status"], "processing")
                self.assertNotIn("no matching structured memory", blocked_ask["answer"]["answer"].casefold())
                self.assertEqual(provider.answer_calls, 0)

                provider.block_release.set()
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    status, processing = self.request(base_url, "/api/v2/processing")
                    self.assertEqual(status, 200)
                    counts = processing["processing"]["counts"]
                    if (
                        int(counts["processed"]) == 1
                        and int(counts["pending"]) == 0
                        and int(counts["processing"]) == 0
                        and int(counts["failed"]) == 0
                    ):
                        break
                    time.sleep(0.025)
                self.assertEqual(int(counts["processed"]), 1)
                self.assertEqual(int(counts["failed"]), 0)

                status, state = self.request(base_url, "/api/v2/state")
                self.assertEqual(status, 200)
                state_counts = state["state"]["counts"]
                self.assertGreaterEqual(int(state_counts["facts"]), 1)
                self.assertGreaterEqual(len(state["state"]["attention"]), 1)

                status, answer = self.request(
                    base_url,
                    "/api/v2/ask",
                    method="POST",
                    body={"question": "What do I need to do today?"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(answer["answer"]["mode"], "attention")
                self.assertIn("human-dogfood-delayed-1", answer["answer"]["source_refs"])

                host_status = self.command_json("-m", "app.host", "--home", str(home), "--json", "status")
                product_status = self.command_json(
                    "-m",
                    "app.product_process",
                    "--home",
                    str(home),
                    "--json",
                    "status",
                )
                host_product_counts = host_status["product"]["processing"]
                product_counts = product_status["processing"]["counts"]
                self.assertEqual(
                    host_product_counts,
                    {key: int(product_counts[key]) for key in ("pending", "processing", "processed", "failed")},
                )
                self.assertEqual(host_status["product"]["database"], product_status["database"])
                self.assertEqual(product_status["database"], str(home / "blackhole-v2.db"))

                legacy = sqlite3.connect(home / "blackhole.db")
                try:
                    legacy_count = legacy.execute("SELECT COUNT(*) FROM processing_state").fetchone()[0]
                finally:
                    legacy.close()
                self.assertEqual(legacy_count, 0)
            finally:
                provider.block_release.set()
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
