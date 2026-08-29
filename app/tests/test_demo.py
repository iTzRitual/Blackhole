from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from app.demo import answer_question, append_capture, build_view, seed_database
from app.state_store import StateStore
from app.web_app import create_server


class DemoTests(unittest.TestCase):
    def test_seed_builds_user_facing_state_categories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            result = seed_database(db_path)
            self.assertEqual(result["events"], 14)
            view = build_view(db_path)
            self.assertEqual(view["counts"]["captures"], 14)
            self.assertTrue(view["attention"])
            self.assertTrue(view["memory"]["subscriptions"])
            self.assertTrue(view["memory"]["unknown"])
            self.assertTrue(view["memory"]["duplicates"])

    def test_capture_is_saved_raw_only_and_rebuildable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            seed_database(db_path)
            result = append_capture("A fragment with no classification.", db_path)
            self.assertEqual(result["event_id"], "capture-0015")
            with StateStore(db_path) as store:
                raw = store.connection.execute(
                    "SELECT raw_json FROM raw_events WHERE event_id = ?", ("capture-0015",)
                ).fetchone()
                self.assertIsNotNone(raw)
                event = json.loads(raw["raw_json"])
                self.assertEqual(event["payload"]["text"], "A fragment with no classification.")
                self.assertEqual(event["metadata"]["semantic_status"], "pending")
                self.assertEqual(
                    store.connection.execute(
                        "SELECT COUNT(*) AS count FROM observations WHERE event_id = ?", ("capture-0015",)
                    ).fetchone()["count"],
                    0,
                )
            self.assertEqual(build_view(db_path)["counts"]["captures"], 15)

    def test_question_routes_to_structured_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            seed_database(db_path)
            answer = answer_question("What information is incomplete?", db_path)
            self.assertEqual(answer["mode"], "unknown")
            self.assertTrue(answer["sections"][0]["assertions"])
            self.assertTrue(all("source_refs" in item for item in answer["sections"][0]["assertions"]))

    def test_local_http_surface_supports_state_query_capture_and_reset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.sqlite"
            seed_database(db_path)
            server = create_server("127.0.0.1", 0, db_path)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                state = json.load(urllib.request.urlopen(f"{base_url}/api/state"))
                self.assertEqual(state["state"]["counts"]["captures"], 14)
                request = urllib.request.Request(
                    f"{base_url}/api/capture",
                    data=json.dumps({"text": "Saved from the test."}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                saved = json.load(urllib.request.urlopen(request))
                self.assertTrue(saved["saved"])
                reset = urllib.request.Request(
                    f"{base_url}/api/reset",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                json.load(urllib.request.urlopen(reset))
                final_state = json.load(urllib.request.urlopen(f"{base_url}/api/state"))
                self.assertEqual(final_state["state"]["counts"]["captures"], 14)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
