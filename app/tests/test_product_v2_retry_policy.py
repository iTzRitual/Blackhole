from __future__ import annotations

import tempfile
import time
import unittest

from app.product_v2 import ProductRuntime
from app.product_v2_store import MAX_AUTOMATIC_ATTEMPTS


class ProductV2RetryPolicyTests(unittest.TestCase):
    def test_automatic_retry_cap_requires_explicit_retry_after_terminal_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with ProductRuntime(directory, start_worker=False) as runtime:
                runtime.capture("bounded retry", event_id="retry-cap-1")
                for attempt in range(MAX_AUTOMATIC_ATTEMPTS):
                    claimed = (
                        runtime.store.claim_pending(runtime._owner_id)
                        if attempt == 0
                        else runtime.store.claim_failed(runtime._owner_id)
                    )
                    self.assertEqual([item["event_id"] for item in claimed], ["retry-cap-1"])
                    runtime.store.mark_failed(
                        runtime._owner_id,
                        ["retry-cap-1"],
                        error="semantic provider failed; retry available",
                        retry_after_seconds=0,
                    )
                    time.sleep(0.01)
                self.assertEqual(runtime.store.claim_failed(runtime._owner_id), [])
                status = runtime.processing_status("retry-cap-1")
                self.assertEqual(status["status"], "failed")
                self.assertEqual(status["attempt_count"], MAX_AUTOMATIC_ATTEMPTS)
                self.assertEqual(runtime.retry_failed("retry-cap-1")["retried"], 1)
                self.assertEqual(runtime.processing_status("retry-cap-1")["status"], "pending")


if __name__ == "__main__":
    unittest.main()
