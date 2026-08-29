from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.qualification_check import (
    audit_repository,
    check_trajectory_inventory,
    inventory_trajectories,
    print_report,
    scan_text_for_secrets,
    scan_tracked_files_for_secrets,
)


class QualificationCheckTests(unittest.TestCase):
    def make_complete_fixture(self, root: Path) -> list[Path]:
        files = [
            "README.md",
            "IMPROVEMENT_CHANGELOG.md",
            "docs/REPRODUCTION.md",
            "benchmark/README.md",
            "benchmark/dev/response-contract-v2.json",
            "baseline/run_baseline.py",
            "eval/results/baseline-v1.json",
            "app/advanced_runner.py",
        ]
        for relative in files:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")

        coding = root / "trajectories" / "coding" / "001-fixture"
        coding.mkdir(parents=True)
        (coding / "prompt.md").write_text("prompt\n", encoding="utf-8")
        (coding / "summary.md").write_text("summary\n", encoding="utf-8")

        runtime = root / "trajectories" / "runtime" / "001-fixture"
        runtime.mkdir(parents=True)
        (runtime / "summary.md").write_text("summary\n", encoding="utf-8")
        (runtime / "trace.json").write_text("{}\n", encoding="utf-8")
        return [path.relative_to(root) for path in root.rglob("*") if path.is_file()]

    def test_complete_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = self.make_complete_fixture(root)
            report = audit_repository(root, tracked_paths=tracked)

            self.assertEqual(report.hard_failures, [])
            self.assertEqual(len(report.coding_trajectories), 1)
            self.assertEqual(len(report.runtime_trajectories), 1)

    def test_missing_required_artifact_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracked = self.make_complete_fixture(root)
            (root / "README.md").unlink()
            report = audit_repository(root, tracked_paths=tracked)

            self.assertTrue(report.hard_failures)
            self.assertTrue(any("README.md" in item.message for item in report.hard_failures))

    def test_missing_trajectory_prompt_and_summary_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            coding = root / "trajectories" / "coding"
            missing_prompt = coding / "001-missing-prompt"
            missing_prompt.mkdir(parents=True)
            (missing_prompt / "summary.md").write_text("summary\n", encoding="utf-8")
            missing_summary = coding / "002-missing-summary"
            missing_summary.mkdir()
            (missing_summary / "prompt.md").write_text("prompt\n", encoding="utf-8")

            records = inventory_trajectories(root)
            findings = check_trajectory_inventory(records)
            messages = "\n".join(item.message for item in findings)

            self.assertIn("001-missing-prompt missing prompt.md", messages)
            self.assertIn("002-missing-summary missing summary.md", messages)
            self.assertTrue(any(item.level == "FAIL" for item in findings))

    def test_placeholder_api_key_does_not_trigger_secret_failure(self) -> None:
        text = "OPENAI_API_KEY=<your-key>\nANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}\n"
        self.assertEqual(scan_text_for_secrets(text), [])

    def test_synthetic_secret_is_detected_without_printing_value(self) -> None:
        secret = "sk-live-synthetic-value-that-must-not-be-printed"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "fixture.txt"
            path.write_text(f"OPENAI_API_KEY={secret}\n", encoding="utf-8")
            findings = scan_tracked_files_for_secrets(root, [Path("fixture.txt")])

            self.assertTrue(findings)
            self.assertTrue(any(item.rule == "OPENAI_API_KEY assignment" for item in findings))
            self.assertNotIn(secret, " ".join(f"{item.path} {item.rule}" for item in findings))

            report = audit_repository(root, tracked_paths=[Path("fixture.txt")])
            output = io.StringIO()
            with redirect_stdout(output):
                print_report(report)
            self.assertNotIn(secret, output.getvalue())
            self.assertIn("fixture.txt", output.getvalue())
            self.assertIn("OPENAI_API_KEY assignment", output.getvalue())


if __name__ == "__main__":
    unittest.main()
