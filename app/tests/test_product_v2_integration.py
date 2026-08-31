from __future__ import annotations

import tempfile
import unittest
from typing import Any

from app.product_v2 import ProductRuntime


class IntegrationSemanticProvider:
    """Small deterministic seam for projection/Ask integration tests."""

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
        attention: list[dict[str, Any]] = []
        for event in events:
            event_id = str(event["event_id"])
            text = str(event.get("payload", {}).get("text", ""))
            lowered = text.casefold()
            if "storage unit" in lowered:
                value = "2.4 metres" if "2.4" in lowered else "2 metres"
                item: dict[str, Any] = {
                    "event_id": event_id,
                    "entity": "storage unit",
                    "concept": "width",
                    "knowledge_status": "known",
                    "value": value,
                    "operation": "correction" if "correction" in lowered else "set",
                }
                if "correction" in lowered:
                    item["supersedes_event_id"] = "integration-old-width"
                facts.append(item)
            if "expense report" in lowered:
                completed = "submitted" in lowered
                attention.append(
                    {
                        "event_id": event_id,
                        "kind": "task",
                        "title": "Completed expense report" if completed else "Submit expense report",
                        "status": "completed" if completed else "open",
                        "knowledge_status": "known",
                        "details": {"lifecycle_key": "expense-report"},
                    }
                )
        return {"facts": facts, "attention": attention}


class ProductV2IntegrationTests(unittest.TestCase):
    def test_attention_lifecycle_projection_keeps_latest_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(directory, provider=IntegrationSemanticProvider(), start_worker=False) as runtime:
                runtime.capture("Submit the expense report by Friday.", event_id="integration-deadline")
                runtime.capture("I submitted the expense report this morning.", event_id="integration-complete")
                runtime.process_pending()
                attention = runtime.snapshot()["attention"]
                self.assertEqual(len(attention), 1)
                self.assertEqual(attention[0]["status"], "completed")
                self.assertEqual(attention[0]["state"], "completed")
                self.assertIn("Completed", attention[0]["title"])
                self.assertEqual(runtime.snapshot()["counts"]["attention"], 0)

    def test_change_answer_contains_before_and_after_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(directory, provider=IntegrationSemanticProvider(), start_worker=False) as runtime:
                runtime.capture("The storage unit is 2 metres wide.", event_id="integration-old-width")
                runtime.process_pending()
                runtime.capture("Correction: the storage unit is 2.4 metres wide, not 2 metres.", event_id="integration-new-width")
                runtime.process_pending()
                answer = runtime.ask("What changed about the storage unit's width?")
                self.assertIn("2 metres", answer["answer"])
                self.assertIn("2.4 metres", answer["answer"])
                self.assertEqual(answer["mode"], "changes")


if __name__ == "__main__":
    unittest.main()
