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

    def test_json_terminal_failure_wins_over_incidental_warning_and_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / "codex.exe")
            terminal = {
                "type": "turn.failed",
                "error": {
                    "message": json.dumps(
                        {
                            "type": "error",
                            "error": {
                                "type": "invalid_request_error",
                                "code": "invalid_json_schema",
                                "message": "schema rejected api_key=secret-token-value",
                            },
                            "status": 400,
                        }
                    )
                },
            }

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(command, 0, stdout=b"codex-cli 0.150.0\n", stderr=b"")
                return subprocess.CompletedProcess(
                    command,
                    1,
                    stdout=(json.dumps(terminal) + "\n").encode(),
                    stderr=b"WARN codex_core::shell_snapshot: Shell snapshot not supported yet for PowerShell\nAuthorization: Bearer secret-token-value\n",
                )

            provider = ProductCodexProvider(home=directory)
            with patch("app.product_v2.shutil.which", return_value=executable), patch(
                "app.product_v2.subprocess.run", side_effect=fake_run
            ):
                with self.assertRaises(ProductProviderExecutionError) as raised:
                    provider.extract(events=[], prior_memory={}, time_context={}, contract={})

            diagnostic = provider.last_call
            self.assertIsNotNone(diagnostic)
            assert diagnostic is not None
            self.assertEqual(diagnostic["returncode"], 1)
            self.assertEqual(diagnostic["terminal_event"]["type"], "turn.failed")
            self.assertEqual(diagnostic["terminal_event"]["parsed_error"]["error"]["code"], "invalid_json_schema")
            self.assertIn("shell_snapshot", diagnostic["stderr_tail"])
            self.assertIn("invalid_json_schema", str(raised.exception))
            self.assertNotIn("shell snapshot", str(raised.exception))
            self.assertNotIn("secret-token-value", json.dumps(diagnostic))

    def test_schema_is_strict_and_declares_items_for_structured_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_path = ProductCodexProvider._schema_path(Path(directory))
            schema = json.loads(schema_path.read_text(encoding="utf-8"))

        def assert_strict(node: object) -> None:
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertFalse(node.get("additionalProperties"))
                    self.assertEqual(set(node.get("required", [])), set(node.get("properties", {})))
                if node.get("type") == "array":
                    self.assertIn("items", node)
                for value in node.values():
                    assert_strict(value)
            elif isinstance(node, list):
                for value in node:
                    assert_strict(value)

        assert_strict(schema)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["required"],
            [
                "facts",
                "observations",
                "relationships",
                "attention",
                "attachment_results",
                "answer",
                "source_refs",
                "evidence_ids",
            ],
        )

    def test_successful_structured_output_is_parsed_with_exact_safe_invocation_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / "codex.exe")
            commands: list[list[str]] = []
            kwargs_seen: list[dict[str, object]] = []
            payload = {
                "facts": [],
                "observations": [],
                "relationships": [],
                "attention": [],
                "attachment_results": [],
                "answer": None,
                "source_refs": [],
                "evidence_ids": [],
            }

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
                commands.append(command)
                kwargs_seen.append(kwargs)
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(command, 0, stdout=b"codex-cli 0.150.0\n", stderr=b"")
                schema_path = Path(command[command.index("--output-schema") + 1])
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                self.assertFalse(schema["additionalProperties"])
                output_path = Path(command[command.index("-o") + 1])
                output_path.write_text(json.dumps(payload), encoding="utf-8")
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout=b'{"type":"turn.completed"}\n',
                    stderr=b"",
                )

            provider = ProductCodexProvider(
                home=directory,
                timeout=17,
                model="gpt-5.6-luna",
                reasoning_effort="high",
            )
            with patch("app.product_v2.shutil.which", return_value=executable), patch(
                "app.product_v2.subprocess.run", side_effect=fake_run
            ):
                parsed = provider.extract(events=[], prior_memory={}, time_context={}, contract={})

            self.assertEqual(parsed, payload)
            command = commands[-1]
            self.assertEqual(command[0], executable)
            self.assertIn("--ephemeral", command)
            self.assertIn("--json", command)
            self.assertIn("--model", command)
            self.assertIn("gpt-5.6-luna", command)
            self.assertIn("-c", command)
            self.assertIn("model_reasoning_effort=high", command)
            self.assertIn("-s", command)
            self.assertIn("read-only", command)
            self.assertIn("--ignore-rules", command)
            self.assertIn("--skip-git-repo-check", command)
            self.assertIn("-C", command)
            self.assertIn("--add-dir", command)
            self.assertIn("--output-schema", command)
            self.assertIn("-o", command)
            self.assertEqual(command[-1], "-")
            self.assertNotIn("--ignore-user-config", command)
            self.assertNotIn("--disable", command)
            self.assertIsInstance(kwargs_seen[-1]["input"], bytes)
            self.assertIn(b"INPUT:\n{", kwargs_seen[-1]["input"])
            self.assertIn(b'"captures": []', kwargs_seen[-1]["input"])
            self.assertEqual(kwargs_seen[-1]["timeout"], 17)
            self.assertTrue(kwargs_seen[-1]["capture_output"])
            self.assertFalse(kwargs_seen[-1]["check"])
            self.assertEqual(provider.last_call["sandbox"], "read-only")
            self.assertEqual(provider.last_call["approval_mode"], "CLI default; no explicit approval flag")
            self.assertEqual(provider.last_call["feature_flags"]["shell_snapshot"], "default-enabled; not explicitly disabled")
            self.assertEqual(provider.last_call["timeout_seconds"], 17)

    def test_image_attachment_uses_supported_image_flag_and_documents_remain_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory) / "codex.exe")
            commands: list[list[str]] = []
            payload = {
                "facts": [],
                "observations": [],
                "relationships": [],
                "attention": [],
                "attachment_results": [],
                "answer": None,
                "source_refs": [],
                "evidence_ids": [],
            }

            def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                commands.append(command)
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(command, 0, stdout=b"codex-cli 0.150.0\n", stderr=b"")
                output_path = Path(command[command.index("-o") + 1])
                output_path.write_text(json.dumps(payload), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

            provider = ProductCodexProvider(home=directory)
            events = [
                {
                    "event_id": "image-event",
                    "attachments": [{"path": "C:\\tmp\\receipt.png", "mime_type": "image/png"}],
                },
                {
                    "event_id": "document-event",
                    "attachments": [{"path": "C:\\tmp\\contract.pdf", "mime_type": "application/pdf"}],
                },
            ]
            with patch("app.product_v2.shutil.which", return_value=executable), patch(
                "app.product_v2.subprocess.run", side_effect=fake_run
            ):
                provider.extract(events=events, prior_memory={}, time_context={}, contract={})

            command = commands[-1]
            self.assertIn("--image", command)
            self.assertIn("C:\\tmp\\receipt.png", command)
            self.assertNotIn("C:\\tmp\\contract.pdf", command)

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
