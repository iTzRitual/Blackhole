from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ops_logging import ProductOpsLogger
from app.product_v2 import ProductRuntime
from app.tests.test_product_v2 import ProductFakeProvider
from app.web_app import create_server


def fixed_clock() -> datetime:
    return datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)


class CorrectionProvider:
    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, time_context, contract
        facts: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            if event_id == "truth-old":
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "basement keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "mother's place",
                    }
                )
            elif event_id == "truth-new":
                facts.append(
                    {
                        "event_id": event_id,
                        "entity": "basement keys",
                        "concept": "location",
                        "knowledge_status": "known",
                        "value": "drawer",
                        "operation": "correction",
                        "supersedes_event_id": "truth-old",
                    }
                )
        return {"facts": facts}


class ProductV2UndoAndLoggingTests(unittest.TestCase):
    @staticmethod
    def runtime(directory: str, provider: Any | None = None, **kwargs: Any) -> ProductRuntime:
        return ProductRuntime(
            directory,
            provider=provider or ProductFakeProvider(),
            start_worker=False,
            clock=fixed_clock,
            **kwargs,
        )

    @staticmethod
    def assert_forgotten(test: unittest.TestCase, runtime: ProductRuntime, event_id: str) -> None:
        test.assertTrue(runtime.store.is_deleted(event_id))
        test.assertIsNone(runtime.store.raw_event(event_id))
        test.assertIsNone(runtime.processing_status(event_id))
        state = runtime.snapshot()
        encoded = json.dumps(state, ensure_ascii=False, sort_keys=True)
        test.assertNotIn(event_id, encoded)
        test.assertFalse(any(item.get("source_event_id") == event_id for item in state["fact_history"]))
        test.assertFalse(any(item.get("source_event_id") == event_id for item in state["relationships"]))
        test.assertFalse(any(item.get("source_event_id") == event_id for item in state["attention"]))
        test.assertFalse(any(item.get("event_id") == event_id for item in state["sources"]))

    def test_pending_capture_undo_removes_queue_and_raw_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture("pending private note", event_id="undo-pending")
                self.assertEqual(runtime.processing_status("undo-pending")["status"], "pending")
                result = runtime.retract("undo-pending")
                self.assertTrue(result["deleted"])
                self.assert_forgotten(self, runtime, "undo-pending")
                self.assertEqual(runtime.process_pending()["processed"], 0)
                self.assertEqual(provider.calls, [])

    def test_raw_source_delete_remains_guarded_outside_explicit_undo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture("guarded source", event_id="undo-guarded")
                with runtime.store._lock:
                    with self.assertRaises(sqlite3.IntegrityError):
                        runtime.store.connection.execute(
                            "DELETE FROM source_events WHERE event_id = ?",
                            ("undo-guarded",),
                        )
                    runtime.store.connection.rollback()
                self.assertIsNotNone(runtime.store.raw_event("undo-guarded"))
                self.assertTrue(runtime.retract("undo-guarded")["deleted"])

    def test_processing_capture_undo_removes_processing_state(self) -> None:
        provider = ProductFakeProvider()
        provider.block_started = threading.Event()
        provider.block_release = threading.Event()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=True,
                clock=fixed_clock,
            ) as runtime:
                runtime.capture("processing private note", event_id="undo-processing")
                self.assertTrue(provider.block_started.wait(timeout=2))
                self.assertEqual(runtime.processing_status("undo-processing")["status"], "processing")
                result = runtime.retract("undo-processing")
                self.assertTrue(result["deleted"])
                provider.block_release.set()
                self.assertTrue(runtime.wait_for_idle(timeout=3))
                time.sleep(0.05)
                self.assert_forgotten(self, runtime, "undo-processing")
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 0)

    def test_processed_capture_undo_rebuilds_without_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture("processed private note", event_id="undo-processed")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 1)
                result = runtime.retract("undo-processed")
                self.assertTrue(result["deleted"])
                self.assert_forgotten(self, runtime, "undo-processed")
                runtime.store.rebuild()
                self.assertEqual(runtime.snapshot()["counts"]["fact_history"], 0)

    def test_failed_retry_capture_undo_cannot_be_requeued(self) -> None:
        provider = ProductFakeProvider()
        provider.fail = True
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider) as runtime:
                runtime.capture("failed private note", event_id="undo-failed")
                self.assertEqual(runtime.process_pending()["failed"], 1)
                self.assertEqual(runtime.processing_status("undo-failed")["status"], "failed")
                result = runtime.retract("undo-failed")
                self.assertTrue(result["deleted"])
                provider.fail = False
                self.assertEqual(runtime.retry_failed("undo-failed")["retried"], 0)
                self.assert_forgotten(self, runtime, "undo-failed")
                self.assertEqual(runtime.process_pending()["processed"], 0)

    def test_late_provider_result_cannot_resurrect_deleted_capture(self) -> None:
        provider = ProductFakeProvider()
        provider.block_started = threading.Event()
        provider.block_release = threading.Event()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=True,
                clock=fixed_clock,
            ) as runtime:
                runtime.capture("late provider result must disappear", event_id="undo-race")
                self.assertTrue(provider.block_started.wait(timeout=2))
                runtime.retract("undo-race")
                provider.block_release.set()
                self.assertTrue(runtime.wait_for_idle(timeout=3))
                time.sleep(0.05)
                self.assert_forgotten(self, runtime, "undo-race")
                self.assertEqual(
                    runtime.store.connection.execute(
                        "SELECT COUNT(*) FROM memory_facts WHERE source_event_id = ?",
                        ("undo-race",),
                    ).fetchone()[0],
                    0,
                )

    def test_batch_undo_does_not_retry_or_erase_a_surviving_event(self) -> None:
        provider = ProductFakeProvider()
        provider.block_started = threading.Event()
        provider.block_release = threading.Event()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider) as runtime:
                runtime.capture("The car started knocking.", event_id="undo-batch-live")
                runtime.capture("The basement keys are here.", event_id="undo-batch-delete")
                claimed = runtime.store.claim_pending(runtime._owner_id, limit=2)
                self.assertEqual(
                    [item["event_id"] for item in claimed],
                    ["undo-batch-live", "undo-batch-delete"],
                )
                result_holder: dict[str, Any] = {}

                def process() -> None:
                    result_holder["result"] = runtime._process_claimed(claimed)

                worker = threading.Thread(target=process)
                worker.start()
                self.assertTrue(provider.block_started.wait(timeout=2))
                runtime.retract("undo-batch-delete")
                provider.block_release.set()
                worker.join(timeout=3)
                self.assertFalse(worker.is_alive())
                self.assertEqual(result_holder["result"]["processed"], 1)
                self.assertEqual(result_holder["result"]["deleted"], 1)
                self.assertEqual(runtime.processing_status("undo-batch-live")["status"], "processed")
                self.assert_forgotten(self, runtime, "undo-batch-delete")
                self.assertEqual(runtime.snapshot()["counts"]["facts"], 1)

    def test_raw_payload_and_all_public_semantic_views_are_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture(
                    "private raw payload that must be gone",
                    event_id="undo-raw",
                    metadata={"private_marker": "derived must not retain this"},
                )
                runtime.process_pending()
                runtime.retract("undo-raw")
                self.assert_forgotten(self, runtime, "undo-raw")
                self.assertEqual(
                    runtime.store.connection.execute(
                        "SELECT COUNT(*) FROM source_events WHERE event_id = ?",
                        ("undo-raw",),
                    ).fetchone()[0],
                    0,
                )
                self.assertEqual(
                    runtime.store.connection.execute(
                        "SELECT COUNT(*) FROM processing_state WHERE event_id = ?",
                        ("undo-raw",),
                    ).fetchone()[0],
                    0,
                )

    def test_memory_attention_ask_and_provenance_do_not_retrieve_deleted_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = ProductFakeProvider()
            with self.runtime(directory, provider) as runtime:
                runtime.capture("Odbieram dzieci za 10 minut.", event_id="undo-visible")
                runtime.process_pending()
                before = runtime.ask("What do I need to do today?")
                self.assertIn("undo-visible", before["source_refs"])
                runtime.retract("undo-visible")
                state = runtime.snapshot()
                self.assertEqual(state["attention"], [])
                self.assertEqual(state["current_facts"], [])
                after = runtime.ask("What do I need to do today?")
                self.assertIn(after["mode"], {"no_data", "no_match"})
                self.assertNotIn("undo-visible", after["source_refs"])
                self.assertNotIn("undo-visible", json.dumps(after, ensure_ascii=False))
                self.assert_forgotten(self, runtime, "undo-visible")

    def test_unreferenced_attachment_bytes_are_deleted(self) -> None:
        content = b"unshared-product-v2-attachment"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture(
                    None,
                    attachment={"content": content, "filename": "private.bin"},
                    event_id="undo-blob-alone",
                )
                path = runtime.store.blob_path(digest)
                self.assertTrue(path.exists())
                result = runtime.retract("undo-blob-alone")
                self.assertEqual(result["blobs_deleted"], 1)
                self.assertFalse(path.exists())
                with self.assertRaises(FileNotFoundError):
                    runtime.attachment_bytes(digest)
                self.assertEqual(runtime.snapshot()["attachments"], [])

    def test_shared_attachment_survives_first_delete_and_is_removed_after_last(self) -> None:
        content = b"shared-product-v2-attachment"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture(None, attachment=content, event_id="undo-shared-a")
                runtime.capture(None, attachment=content, event_id="undo-shared-b")
                path = runtime.store.blob_path(digest)
                first = runtime.retract("undo-shared-a")
                self.assertEqual(first["blobs_deleted"], 0)
                self.assertEqual(first["blobs_preserved"], 1)
                self.assertTrue(path.exists())
                self.assertIsNotNone(runtime.store.raw_event("undo-shared-b"))
                second = runtime.retract("undo-shared-b")
                self.assertEqual(second["blobs_deleted"], 1)
                self.assertFalse(path.exists())

    def test_failed_attachment_capture_cleans_published_orphan_blob(self) -> None:
        content = b"orphaned-after-validation-failure"
        digest = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                with self.assertRaises(ValueError):
                    runtime.capture(
                        None,
                        attachments=[
                            content,
                            {"content": b"never-published", "filename": "bad/name.txt"},
                        ],
                        event_id="undo-orphan",
                    )
                self.assertFalse(runtime.store.blobs.path_for_hash(digest).exists())
                self.assertIsNone(runtime.store.raw_event("undo-orphan"))

    def test_double_undo_is_clean_and_does_not_mutate_unrelated_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, ProductFakeProvider()) as runtime:
                runtime.capture("first private note", event_id="undo-double-a")
                runtime.capture("unrelated live note", event_id="undo-double-b")
                first = runtime.retract("undo-double-a")
                second = runtime.retract("undo-double-a")
                self.assertTrue(first["deleted"])
                self.assertFalse(second["deleted"])
                self.assertTrue(second["already_deleted"])
                self.assertIsNotNone(runtime.store.raw_event("undo-double-b"))
                self.assert_forgotten(self, runtime, "undo-double-a")

    def test_deleting_correction_restores_remaining_semantic_truth_after_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, CorrectionProvider()) as runtime:
                runtime.capture("old key location", event_id="truth-old")
                runtime.capture("new key location", event_id="truth-new")
                runtime.process_pending()
                self.assertEqual(runtime.snapshot()["current_facts"][0]["value"], "drawer")
                runtime.retract("truth-new")
                state = runtime.snapshot()
                self.assertEqual(state["current_facts"][0]["value"], "mother's place")
                self.assertEqual([row["source_event_id"] for row in state["fact_history"]], ["truth-old"])
                self.assertNotIn("truth-new", json.dumps(state, ensure_ascii=False))
                runtime.store.rebuild()
                self.assertEqual(runtime.snapshot()["current_facts"][0]["value"], "mother's place")

    def test_deleting_superseded_source_does_not_leave_phantom_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, CorrectionProvider()) as runtime:
                runtime.capture("old key location", event_id="truth-old")
                runtime.capture("new key location", event_id="truth-new")
                runtime.process_pending()
                runtime.retract("truth-old")
                state = runtime.snapshot()
                self.assertEqual(state["current_facts"][0]["value"], "drawer")
                self.assertNotIn("truth-old", json.dumps(state, ensure_ascii=False))
                self.assertNotIn("truth-old", state["current_facts"][0]["source_refs"])
                self.assertNotIn("truth-old", state["fact_history"][0].get("supersedes_event_id", ""))

    def test_operational_logs_cover_lifecycle_and_never_print_capture_or_secret(self) -> None:
        stream = io.StringIO()
        logger = ProductOpsLogger(stream=stream)
        provider = ProductFakeProvider()
        capture_text = "full capture text must not be logged secret-token-value"
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider, ops_logger=logger) as runtime:
                runtime.capture(capture_text, event_id="log-capture")
                runtime.process_pending()
                runtime.ask("What do I know about the inbox note?")
                runtime.retract("log-capture")
        output = stream.getvalue()
        for fragment in (
            "[capture] saved",
            "[queue] pending",
            "[provider] start",
            "[provider] complete",
            "[memory] updated",
            "[attention] updated",
            "[ask] start",
            "[ask] path",
            "[ask] sources",
            "[ask] complete",
            "[undo] requested",
            "[undo] deleted",
        ):
            self.assertIn(fragment, output)
        self.assertNotIn(capture_text, output)
        self.assertNotIn("secret-token-value", output)
        self.assertIn("provider_calls=0", output)
        self.assertTrue(all(len(line) < 600 for line in output.splitlines()))

    def test_provider_failure_logs_bounded_sanitized_error_and_retry(self) -> None:
        stream = io.StringIO()
        logger = ProductOpsLogger(stream=stream)
        provider = ProductFakeProvider()
        provider.fail = True
        with tempfile.TemporaryDirectory() as directory:
            with self.runtime(directory, provider, ops_logger=logger) as runtime:
                runtime.capture("failure body secret-token-value", event_id="log-failure")
                runtime.process_pending()
        output = stream.getvalue()
        self.assertIn("[provider] failed", output)
        self.assertIn("[queue] retry scheduled", output)
        self.assertNotIn("secret-token-value", output)
        self.assertNotIn("failure body", output)

    def test_server_worker_start_and_clean_stop_are_logged(self) -> None:
        stream = io.StringIO()
        logger = ProductOpsLogger(stream=stream)
        with tempfile.TemporaryDirectory() as directory:
            server = create_server(
                "127.0.0.1",
                0,
                home=Path(directory),
                provider=ProductFakeProvider(),
                ops_logger=logger,
            )
            try:
                self.assertIn("[worker] product-v2 worker started", stream.getvalue())
            finally:
                server.server_close()
        output = stream.getvalue()
        self.assertIn("[worker] product-v2 worker stopped", output)


if __name__ == "__main__":
    unittest.main()
