import io
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.ops_logging import ProductOpsLogger, sanitize_human_text
from app.product_v2 import ProductRuntime
from app.runtime_config import DEFAULT_BATCH_SIZE, DEFAULT_REASONING_EFFORT, SUPPORTED_REASONING_EFFORTS
from app.tests.test_product_v2 import ProductFakeProvider


REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPO_ROOT / "app" / "web"
APP_JS = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
CSS = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")
HTML = (WEB_ROOT / "index.html").read_text(encoding="utf-8")


class DelayedRetryProvider:
    def __init__(self) -> None:
        self.fail_once = True
        self.calls: list[list[str]] = []
        self.time_contexts: list[dict[str, Any]] = []

    def extract(
        self,
        *,
        events: list[dict[str, Any]],
        prior_memory: dict[str, Any],
        time_context: dict[str, Any],
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        del prior_memory, contract
        self.calls.append([str(event["event_id"]) for event in events])
        self.time_contexts.append(time_context)
        # Model a slow provider without making the deterministic test costly.
        time.sleep(0.02)
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("temporary provider outage")
        event_id = str(events[0]["event_id"])
        return {
            "facts": [],
            "attention": [
                {
                    "event_id": event_id,
                    "kind": "task",
                    "title": "Pick up the kids",
                    "status": "open",
                    "relative_minutes": 10,
                }
            ],
        }


class ProductV2FinalDogfoodTests(unittest.TestCase):
    def test_capture_time_survives_processing_delay_retry_and_rebuild(self) -> None:
        provider = DelayedRetryProvider()
        processing_now = datetime(2026, 8, 30, 20, 52, 41, tzinfo=timezone.utc)
        captured_at = "2026-08-30T22:52:41+02:00"
        expected_due = "2026-08-30T23:02:41+02:00"
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: processing_now,
            ) as runtime:
                runtime.capture(
                    "Odbieram dzieci za 10 minut.",
                    captured_at=captured_at,
                    timezone_name="Europe/Berlin",
                    event_id="final-time-1",
                )
                failed = runtime.process_pending()
                self.assertEqual(failed["failed"], 1)
                self.assertEqual(runtime.processing_status("final-time-1")["status"], "failed")

                self.assertEqual(runtime.retry_failed("final-time-1")["retried"], 1)
                processed = runtime.process_pending()
                self.assertEqual(processed["processed"], 1)
                self.assertEqual(provider.calls, [["final-time-1"], ["final-time-1"]])
                self.assertEqual(provider.time_contexts[0]["captures"][0]["captured_at"], captured_at)

                attention = runtime.snapshot()["attention"]
                self.assertEqual(len(attention), 1)
                self.assertEqual(attention[0]["due_at"], expected_due)

                runtime.store.rebuild()
                rebuilt = runtime.snapshot()["attention"]
                self.assertEqual(rebuilt[0]["due_at"], expected_due)

    def test_product_runtime_uses_conservative_product_defaults(self) -> None:
        self.assertEqual(DEFAULT_REASONING_EFFORT, "low")
        self.assertEqual(DEFAULT_BATCH_SIZE, 2)
        self.assertIn("low", SUPPORTED_REASONING_EFFORTS)

    def test_attention_and_disclosure_contract_is_human_and_stable(self) -> None:
        self.assertIn("const formatAttentionTime", APP_JS)
        self.assertIn("Overdue by ", APP_JS)
        self.assertIn("tomorrow · ", APP_JS)
        self.assertIn("Intl.DateTimeFormat", APP_JS)
        self.assertIn('data-disclosure-id="attention:', APP_JS)
        self.assertIn('data-disclosure-id="memory:', APP_JS)
        self.assertIn('data-disclosure-id="ask:', APP_JS)
        self.assertIn("state.openDisclosures", APP_JS)
        self.assertIn("rememberDisclosureState", APP_JS)
        self.assertIn("bindDisclosureState", APP_JS)
        self.assertIn("icon-chevron", HTML + APP_JS)
        self.assertIn("transform: rotate(180deg)", CSS)
        self.assertNotIn('content: "⌄"', CSS)
        self.assertNotIn(".nav-item.is-active::after", CSS)

    def test_ui_presentation_is_defensive_and_keeps_history_contextual(self) -> None:
        self.assertIn("isDisplayArtifact", APP_JS)
        self.assertIn("[object object]", APP_JS)
        self.assertIn("const displayText", APP_JS)
        self.assertIn('"fact_history"', APP_JS)
        self.assertIn("if (!name) return", APP_JS)
        self.assertIn("Changed from ", APP_JS)
        self.assertIn("Previously: ", APP_JS)
        self.assertNotIn('"Fact history"', APP_JS)
        self.assertIn("Supporting memories · ", APP_JS)
        self.assertIn("const renderAskConversation", APP_JS)
        self.assertIn("askMessages", APP_JS)
        self.assertIn("hasConversation", APP_JS)
        self.assertIn('class=\"chat-message user-message\"', APP_JS)
        self.assertIn('class=\"evidence-details related-memories\"', APP_JS)
        self.assertIn('id="ask-examples-heading"', HTML)
        self.assertIn("align-items: center", CSS)
        self.assertIn("align-self: center", CSS)
        self.assertIn("What Blackhole knows.", HTML)
        self.assertIn("Why Blackhole knows this", APP_JS)

    def test_raw_language_is_preserved_and_deterministic_ask_stays_provider_free(self) -> None:
        provider = ProductFakeProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc),
            ) as runtime:
                runtime.capture("Klucze do piwnicy są u mamy.", event_id="language-1")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                before = time.monotonic()
                answer = runtime.ask("Gdzie są klucze do piwnicy?")
                elapsed = time.monotonic() - before
                raw = runtime.store.raw_event("language-1")
                self.assertEqual(raw["payload"]["text"], "Klucze do piwnicy są u mamy.")
                self.assertEqual(provider.answer_calls, 0)
                self.assertLess(elapsed, 0.2)
                self.assertEqual(answer["provider_used"], False)
                self.assertEqual(answer["answer_language"], "pl")

    def test_human_operational_logs_are_readable_bounded_and_private(self) -> None:
        stream = io.StringIO()
        logger = ProductOpsLogger(stream=stream)
        logger.human("Learned · Basement keys → Mum's place")
        logger.human("token=secret-token-value\n" + ("x" * 500))
        rendered = stream.getvalue()
        self.assertIn("Learned · Basement keys", rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertNotIn("secret-token-value", rendered)
        self.assertLessEqual(max(len(line) for line in rendered.splitlines()), 240)
        self.assertLessEqual(len(sanitize_human_text("x" * 1000)), 220)

        provider = ProductFakeProvider()
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(
                directory,
                provider=provider,
                start_worker=False,
                clock=lambda: datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc),
                ops_logger=logger,
            ) as runtime:
                runtime.capture("PRIVATE_RAW_CAPTURE_VALUE", event_id="logs-1")
                self.assertEqual(runtime.process_pending()["processed"], 1)
                runtime.ask("Where are the basement keys?")
            rendered = stream.getvalue()
        self.assertIn("Saved capture · text", rendered)
        self.assertIn("Understanding", rendered)
        self.assertIn("Learned", rendered)
        self.assertIn("Ready ·", rendered)
        self.assertIn("Ask · deterministic retrieval", rendered)
        self.assertNotIn("PRIVATE_RAW_CAPTURE_VALUE", rendered)


if __name__ == "__main__":
    unittest.main()
