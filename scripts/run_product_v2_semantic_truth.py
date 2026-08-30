"""Run the Product V2 semantic-truth sequence suite and save its evidence.

This is a non-scored, provider-free post-freeze generalization check. It
imports only the visible semantic sequence cases and never reads benchmark,
holdout, baseline, or evaluator-owned expected-output material.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.tests.test_product_v2_semantic_truth import SEMANTIC_CASES


RESULT_PATH = ROOT / "eval" / "results" / "product-v2-semantic-truth.json"
BASE_SHA = "7a76a1b660b49d28cb5aa29ab9e9b5099238aaee"


def _revision() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def run() -> dict[str, Any]:
    suite = unittest.defaultTestLoader.loadTestsFromName(
        "app.tests.test_product_v2_semantic_truth"
    )
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=0).run(suite)
    report: dict[str, Any] = {
        "report_type": "product-v2-semantic-truth",
        "evidence_scope": "post-freeze product generalization; non-scored",
        "base_sha": BASE_SHA,
        "tested_revision": _revision(),
        "source_worktree": "C:/Users/natan/OneDrive/Dokumenty/ChatGPT/Blackhole-v2-provenance-fix",
        "target_branch": "product/v2-semantic-truth",
        "suite": {
            "module": "app.tests.test_product_v2_semantic_truth",
            "case_count": len(SEMANTIC_CASES),
            "multi_capture_case_count": sum(
                len(case.get("captures", [])) > 1 for case in SEMANTIC_CASES
            ),
            "test_methods_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "status": "PASS" if result.wasSuccessful() else "FAIL",
        },
        "provider_calls": 0,
        "benchmark_oracle_accessed": False,
        "holdout_accessed": False,
        "official_baseline_changed": False,
        "stdout": output.getvalue()[-4000:],
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["suite"]["status"] == "PASS" else 1)
