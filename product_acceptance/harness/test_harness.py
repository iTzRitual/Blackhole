from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from product_acceptance.harness.adapters import MockHostAdapter
from product_acceptance.harness.case_loader import CaseValidationError, load_cases
from product_acceptance.harness.run import FAIL, NOT_TESTED, PASS, build_report, run_case, run_mock_quality_gates


CASES_DIR = Path(__file__).resolve().parents[1] / "cases"
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"


def _minimal_case(case_id: str = "TST-001") -> dict:
    return {
        "case_id": case_id,
        "title": "Minimal validation case",
        "locale": "en-US",
        "tags": ["capture"],
        "initial_time": "2026-01-01T09:00:00+00:00",
        "timezone": "Etc/UTC",
        "user_outcome": "The note is saved.",
        "steps": [
            {
                "id": "capture-note",
                "type": "capture",
                "at": "2026-01-01T09:00:00+00:00",
                "text": "A small note.",
                "idempotency_key": "tst-note",
                "expect": {"saved": True, "processing": "pending"},
            }
        ],
    }


class CaseLoaderTests(unittest.TestCase):
    def test_schema_documents_are_valid_json_contracts(self) -> None:
        case_schema = json.loads((SCHEMAS_DIR / "case.schema.json").read_text(encoding="utf-8"))
        report_schema = json.loads((SCHEMAS_DIR / "report.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(case_schema["type"], "array")
        self.assertIn("case", case_schema["$defs"])
        self.assertEqual(report_schema["type"], "object")

    def test_public_corpus_parses_and_covers_required_dimensions(self) -> None:
        cases = load_cases(CASES_DIR, FIXTURES_DIR)
        self.assertEqual(len(cases), 50)
        ids = [case["case_id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        required_ids = {"CAP-001", "CAP-002", "CAP-003", "MEM-001", "MEM-002", "MEM-003", "MEM-004", "MEM-007", "MEM-008", "MEM-009", "OW-006", "ATT-001", "ATT-002", "ATT-004", "REL-006", "REL-007", "REL-008", "REL-009", "ASK-006", "ASK-007", "TIME-008", "TIME-009", "UNDO-010"}
        self.assertTrue(required_ids.issubset(ids))
        self.assertGreaterEqual(sum("false-positive" in case["tags"] for case in cases), 4)
        self.assertGreaterEqual(sum("open-world" in case["tags"] for case in cases), 10)
        self.assertGreaterEqual(sum("attachment" in case["tags"] for case in cases), 5)
        self.assertGreaterEqual(sum("reliability" in case["tags"] for case in cases), 8)
        corpus_text = json.dumps(cases, ensure_ascii=False)
        for seed in (
            "Taxi za 10 minut.",
            "Odbieram dzieci za 10 minut.",
            "Klucze do piwnicy są u mamy.",
            "Samochód zaczął stukać z przodu po lewej.",
            "Kuba lubi ten zielony makaron z Lidla.",
            "PocketWave kosztuje 9 EUR miesięcznie.",
            "PocketWave od 1 września będzie kosztować 11 EUR.",
            "Muszę odnowić pozwolenie parkingowe do 12 września.",
            "Bought the same USB cable again.",
            "Don't cancel Netflix yet.",
        ):
            self.assertIn(seed, corpus_text)

    def test_duplicate_case_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = _minimal_case()
            (root / "a.json").write_text(json.dumps([case]), encoding="utf-8")
            (root / "b.json").write_text(json.dumps([case]), encoding="utf-8")
            with self.assertRaisesRegex(CaseValidationError, "duplicate case_id"):
                load_cases(root, FIXTURES_DIR)

    def test_timezone_without_offset_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = _minimal_case()
            case["initial_time"] = "2026-01-01T09:00:00"
            (root / "case.json").write_text(json.dumps([case]), encoding="utf-8")
            with self.assertRaisesRegex(CaseValidationError, "explicit UTC offset"):
                load_cases(root, FIXTURES_DIR)

    def test_missing_attachment_fixture_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = _minimal_case()
            case["steps"][0].pop("text")
            case["steps"][0]["attachment"] = {"fixture": "missing.svg", "mime_type": "image/svg+xml"}
            (root / "case.json").write_text(json.dumps([case]), encoding="utf-8")
            with self.assertRaisesRegex(CaseValidationError, "does not exist"):
                load_cases(root, FIXTURES_DIR)


class HarnessTests(unittest.TestCase):
    def test_mock_reliability_gates_are_deterministic_and_provider_free(self) -> None:
        gates = run_mock_quality_gates(FIXTURES_DIR)
        self.assertTrue(gates)
        self.assertTrue(all(gate["status"] == PASS for gate in gates), gates)

    def test_mock_executes_transport_cases_and_marks_semantics_not_tested(self) -> None:
        cases = load_cases(CASES_DIR, FIXTURES_DIR)
        adapter = MockHostAdapter()
        results = [run_case(case, adapter, fixtures_dir=FIXTURES_DIR) for case in cases]
        self.assertFalse(any(result["status"] == FAIL for result in results))
        self.assertTrue(any(result["status"] == "PARTIAL" for result in results))
        self.assertTrue(any(check["status"] == NOT_TESTED for result in results for step in result["steps"] for check in step["checks"]))
        report = build_report(cases, results, adapter_name="mock", quality_gates=run_mock_quality_gates(FIXTURES_DIR))
        self.assertEqual(report["case_count"], 50)
        self.assertFalse(report["live_provider_used"])
        self.assertEqual(report["coverage"]["capture"]["case_count"], 50)
        self.assertEqual(report["coverage"]["false_positive_attention"]["case_count"], 4)


if __name__ == "__main__":
    unittest.main()
