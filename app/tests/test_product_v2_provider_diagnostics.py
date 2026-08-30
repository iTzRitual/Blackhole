from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.product_v2 import ProductCodexProvider, ProductProviderExecutionError


class ProductV2ProviderDiagnosticsTests(unittest.TestCase):
    def test_installed_cli_invocation_uses_supported_flags_and_safe_failure_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / "codex.exe")

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        stdout=b"codex-cli 0.150.0-alpha.12.2\n",
                        stderr=b"",
                    )
                return subprocess.CompletedProcess(
                    command,
                    2,
                    stdout=b"",
                    stderr=b"error: unexpected argument '--ask-for-approval' found\napi_key=secret-token-value\n",
                )

            provider = ProductCodexProvider(
                home=directory,
                timeout=10,
                model="gpt-5.6-luna",
                reasoning_effort="high",
            )
            with patch("app.product_v2.shutil.which", return_value=executable), patch(
                "app.product_v2.subprocess.run", side_effect=fake_run
            ):
                with self.assertRaises(ProductProviderExecutionError) as raised:
                    provider.extract(events=[], prior_memory={}, time_context={}, contract={})

            diagnostic = provider.last_call
            self.assertIsNotNone(diagnostic)
            assert diagnostic is not None
            self.assertEqual(diagnostic["cli_version"], "codex-cli 0.150.0-alpha.12.2")
            self.assertEqual(diagnostic["returncode"], 2)
            self.assertEqual(diagnostic["model"], "gpt-5.6-luna")
            self.assertEqual(diagnostic["reasoning_effort"], "high")
            self.assertIn("unexpected argument", diagnostic["stderr"])
            self.assertNotIn("secret-token-value", json.dumps(diagnostic))
            self.assertNotIn("--ask-for-approval", diagnostic["invocation"])
            self.assertIn("--model", diagnostic["invocation"])
            self.assertIn("model_reasoning_effort=high", diagnostic["invocation"])
            self.assertIn("-s", diagnostic["invocation"])
            self.assertIn("read-only", diagnostic["invocation"])
            self.assertIn("exit code 2", str(raised.exception))

    def test_timeout_is_recorded_as_a_retryable_safe_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / "codex.exe")

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(command, 0, stdout=b"codex-cli 0.150.0\n", stderr=b"")
                raise subprocess.TimeoutExpired(command, timeout=10, output=b"warning: still running")

            provider = ProductCodexProvider(home=directory, timeout=10)
            with patch("app.product_v2.shutil.which", return_value=executable), patch(
                "app.product_v2.subprocess.run", side_effect=fake_run
            ):
                with self.assertRaises(ProductProviderExecutionError):
                    provider.extract(events=[], prior_memory={}, time_context={}, contract={})
            self.assertTrue(provider.last_call["timed_out"])
            self.assertEqual(provider.last_call["returncode"], None)


if __name__ == "__main__":
    unittest.main()
