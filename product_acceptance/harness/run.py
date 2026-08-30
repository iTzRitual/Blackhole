"""Run Product V2 dogfood cases against a black-box adapter."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .adapters import HttpHostAdapter, MockHostAdapter
from .case_loader import (
    DEFAULT_CASES_DIR,
    DEFAULT_FIXTURES_DIR,
    CaseValidationError,
    load_cases,
    parse_timestamp,
    resolve_fixture,
)


PASS = "PASS"
FAIL = "FAIL"
PARTIAL = "PARTIAL"
NOT_TESTED = "NOT TESTED"


def _check(status: str, name: str, detail: str) -> dict[str, str]:
    return {"status": status, "name": name, "detail": detail}


def _nested_value(response: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
    value: Any = response
    for key in path:
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    return value


def _processing_status(response: dict[str, Any]) -> str | None:
    processing = response.get("processing")
    if isinstance(processing, dict):
        value = processing.get("status")
        if isinstance(value, str):
            return value
    value = response.get("processing_status")
    return value if isinstance(value, str) else None


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(
            f"{key} {_flatten_text(item)}"
            for key, item in value.items()
            if key not in {"question", "source_text"}
        )
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _contains_all(response: dict[str, Any], values: list[str]) -> list[dict[str, str]]:
    haystack = _flatten_text(response).casefold()
    return [
        _check(PASS if value.casefold() in haystack else FAIL, "answer contains expected text", value)
        for value in values
    ]


def _does_not_contain(response: dict[str, Any], values: list[str]) -> list[dict[str, str]]:
    haystack = _flatten_text(response).casefold()
    return [
        _check(FAIL if value.casefold() in haystack else PASS, "answer excludes forbidden text", value)
        for value in values
    ]


def _evaluate_capture(response: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    capture = response.get("capture") if isinstance(response.get("capture"), dict) else {}
    if "saved" in expect:
        observed = bool(response.get("saved")) or bool(capture.get("saved"))
        checks.append(_check(PASS if observed == expect["saved"] else FAIL, "capture saved", f"expected {expect['saved']}, observed {observed}"))
    if expect.get("durable"):
        event_id = _nested_value(response, ("capture", "event_id"))
        observed = bool(response.get("saved")) and bool(event_id)
        checks.append(_check(PASS if observed else FAIL, "capture has durable-looking receipt", f"saved={response.get('saved')!r}, event_id={event_id!r}"))
    if "processing" in expect:
        observed = _processing_status(response)
        checks.append(_check(PASS if observed == expect["processing"] else FAIL, "capture processing status", f"expected {expect['processing']!r}, observed {observed!r}"))
    if "message" in expect:
        observed = str(response.get("message", ""))
        checks.append(_check(PASS if expect["message"] in observed else FAIL, "capture message", f"expected substring {expect['message']!r}, observed {observed!r}"))
    if "duplicate" in expect:
        observed = bool(capture.get("duplicate", response.get("duplicate", False)))
        checks.append(_check(PASS if observed == expect["duplicate"] else FAIL, "duplicate response", f"expected {expect['duplicate']}, observed {observed}"))
    if expect.get("attachment_persisted"):
        attachment = _nested_value(response, ("capture", "attachment"), response.get("attachment"))
        if not isinstance(attachment, dict):
            attachments = _nested_value(response, ("capture", "attachments"), response.get("attachments"))
            if isinstance(attachments, list) and attachments:
                attachment = attachments[0]
        observed = isinstance(attachment, dict) and bool(attachment.get("sha256") or attachment.get("id") or attachment.get("filename"))
        checks.append(_check(PASS if observed else FAIL, "attachment receipt", f"attachment receipt present={observed}"))
    return checks


def _evaluate_processing(response: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    processing = response.get("processing") if isinstance(response.get("processing"), dict) else {}
    outcome = expect.get("outcome")
    if outcome == "processed":
        observed = bool(response.get("ok")) and int(processing.get("processed", 0) or 0) > 0
        checks.append(_check(PASS if observed else FAIL, "processing completes work", f"ok={response.get('ok')!r}, processed={processing.get('processed', 0)!r}"))
    elif outcome == "retryable":
        error_text = _flatten_text(response).casefold()
        observed = not bool(response.get("ok")) and any(token in error_text for token in ("retry", "provider", "unavailable"))
        checks.append(_check(PASS if observed else FAIL, "processing failure is retryable", f"response={error_text[:180]}"))
    elif outcome == "failed":
        observed = not bool(response.get("ok"))
        checks.append(_check(PASS if observed else FAIL, "processing reports failure", f"ok={response.get('ok')!r}"))
    elif outcome == "no_duplicate":
        observed = bool(response.get("ok")) and int(processing.get("processed", 0) or 0) == 0
        checks.append(_check(PASS if observed else FAIL, "repeated processing is a no-op", f"ok={response.get('ok')!r}, processed={processing.get('processed', 0)!r}"))
    if "processing" in expect:
        observed_status = _processing_status(response)
        checks.append(_check(PASS if observed_status == expect["processing"] else FAIL, "processing status", f"expected {expect['processing']!r}, observed {observed_status!r}"))
    return checks


def _evaluate_surface(response: dict[str, Any], expect: dict[str, Any], *, surface: str) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    checks.extend(_contains_all(response, expect.get("include", [])))
    checks.extend(_does_not_contain(response, expect.get("exclude", [])))
    text = _flatten_text(response).casefold()
    if expect.get("evidence") == "required":
        evidence_markers = ("evidence", "source", "capture_id", "event_id", "provenance")
        observed = any(marker in text for marker in evidence_markers)
        checks.append(_check(PASS if observed else FAIL, f"{surface} shows evidence", f"markers present={observed}"))
    if expect.get("uncertainty") == "required":
        uncertainty_markers = ("unknown", "uncertain", "not sure", "not confirmed", "no supporting evidence", "ambiguous", "niepewn", "niejednoznacz")
        observed = any(marker in text for marker in uncertainty_markers)
        checks.append(_check(PASS if observed else FAIL, f"{surface} communicates uncertainty", f"markers present={observed}"))
    if expect.get("actionable") is True:
        observed = bool(_nested_value(response, ("actionable",), False)) or "due" in text or "open" in text
        checks.append(_check(PASS if observed else FAIL, f"{surface} is actionable", f"actionable signal present={observed}"))
    if expect.get("not_urgent") is True:
        observed = not bool(_nested_value(response, ("urgent",), False)) and "urgent" not in text
        checks.append(_check(PASS if observed else FAIL, f"{surface} is not urgent", f"explicit urgent signal present={not observed}"))
    if expect.get("empty") is True:
        items = response.get("items")
        answer = response.get("answer")
        observed = (isinstance(items, list) and not items) or answer in (None, "")
        checks.append(_check(PASS if observed else FAIL, f"{surface} is empty", f"empty={observed}"))
    return checks


def _evaluate_undo(response: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    undo = response.get("undo") if isinstance(response.get("undo"), dict) else {}
    if "raw_preserved" in expect:
        observed = bool(undo.get("raw_preserved"))
        checks.append(_check(PASS if observed == expect["raw_preserved"] else FAIL, "undo preserves raw evidence", f"expected {expect['raw_preserved']}, observed {observed}"))
    if expect.get("removed_from_active"):
        observed = undo.get("active") is False
        checks.append(_check(PASS if observed else FAIL, "undo removes item from active state", f"active={undo.get('active')!r}; expected removal of {expect['removed_from_active']}"))
    return checks


def _evaluate_restart(response: dict[str, Any], expect: dict[str, Any]) -> list[dict[str, str]]:
    restart = response.get("restart") if isinstance(response.get("restart"), dict) else {}
    observed = bool(restart.get("state_preserved"))
    return [_check(PASS if observed == expect.get("state_preserved") else FAIL, "restart preserves state", f"expected {expect.get('state_preserved')}, observed {observed}")]


def _unsupported_checks(response: dict[str, Any], step_type: str) -> list[dict[str, str]]:
    reason = response.get("reason") or response.get("error") or "adapter did not expose this operation"
    return [_check(NOT_TESTED, f"{step_type} surface", str(reason))]


def _run_step(case: dict[str, Any], step: dict[str, Any], adapter: Any, fixtures_dir: Path) -> dict[str, Any]:
    step_type = step["type"]
    response: dict[str, Any]
    if step_type == "capture":
        fixture_path = None
        if "attachment" in step:
            fixture_path = resolve_fixture(step["attachment"]["fixture"], fixtures_dir)
        response = adapter.capture(step, fixture_path=fixture_path)
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else _evaluate_capture(response, step.get("expect", {}))
    elif step_type == "advance_time":
        response = adapter.set_time(parse_timestamp(step["to"], label=f"{case['case_id']}.{step['id']}.to"))
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else [_check(PASS, "test clock advances", step["to"])]
    elif step_type == "ask":
        response = adapter.ask(step["question"])
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else _evaluate_surface(response, step.get("expect", {}), surface="Ask")
    elif step_type == "attention":
        response = adapter.attention()
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else _evaluate_surface(response, step.get("expect", {}), surface="Attention")
    elif step_type == "memory":
        response = adapter.memory()
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else _evaluate_surface(response, step.get("expect", {}), surface="Memory")
    elif step_type in {"process", "retry"}:
        response = adapter.process() if step_type == "process" else adapter.retry()
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else _evaluate_processing(response, step.get("expect", {}))
    elif step_type == "undo":
        response = adapter.undo(step["target_capture_id"])
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else _evaluate_undo(response, step.get("expect", {}))
    elif step_type == "restart":
        response = adapter.restart()
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else _evaluate_restart(response, step.get("expect", {}))
    elif step_type == "set_provider":
        response = adapter.set_provider(step["availability"])
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else [_check(PASS, "provider fixture configured", step["availability"])]
    elif step_type == "health":
        response = adapter.health()
        checks = _unsupported_checks(response, step_type) if not response.get("_supported", True) else [_check(PASS if response.get("ok") else FAIL, "Host health", str(response))]
    else:  # pragma: no cover - loader rejects unknown step types
        response = {"_supported": False, "reason": f"unknown step type {step_type}"}
        checks = _unsupported_checks(response, step_type)

    return {"step_id": step["id"], "type": step_type, "checks": checks, "response": _public_response(response)}


def _public_response(response: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in response.items() if not key.startswith("_")}


def _status_for_checks(checks: list[dict[str, str]]) -> str:
    statuses = {check["status"] for check in checks}
    if FAIL in statuses:
        return FAIL
    if NOT_TESTED in statuses:
        return PARTIAL
    if PASS in statuses:
        return PASS
    return NOT_TESTED


def run_case(case: dict[str, Any], adapter: Any, *, fixtures_dir: Path) -> dict[str, Any]:
    adapter.begin_case(case["case_id"])
    adapter.set_time(parse_timestamp(case["initial_time"], label=f"{case['case_id']}.initial_time"))
    step_results = [_run_step(case, step, adapter, fixtures_dir) for step in case["steps"]]
    all_checks = [check for result in step_results for check in result["checks"]]
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "status": _status_for_checks(all_checks),
        "steps": step_results,
        "manual_observations": case.get("manual_observations", []),
    }


def _gate(gate_id: str, status: str, detail: str) -> dict[str, str]:
    return {"gate_id": gate_id, "status": status, "detail": detail}


def run_mock_quality_gates(fixtures_dir: Path = DEFAULT_FIXTURES_DIR) -> list[dict[str, str]]:
    """Exercise product-level reliability gates without a semantic provider."""

    gates: list[dict[str, str]] = []

    adapter = MockHostAdapter()
    adapter.begin_case("SMOKE")
    adapter.set_provider("unavailable")
    capture_step = {
        "id": "smoke-capture",
        "type": "capture",
        "text": "offline capture",
        "idempotency_key": "smoke-offline",
    }
    saved = adapter.capture(capture_step)
    capture_saved = bool(saved.get("saved")) and _processing_status(saved) == "pending"
    gates.append(_gate("capture_durable_save", PASS if capture_saved else FAIL, f"saved={saved.get('saved')!r}, processing={_processing_status(saved)!r}"))
    provider_independent = adapter.provider_calls == 0
    gates.append(_gate("capture_does_not_wait_for_provider", PASS if provider_independent else FAIL, f"provider_calls_during_capture={adapter.provider_calls}"))

    duplicate = adapter.capture(capture_step)
    one_active = len(adapter.captures) == 1 and bool(_nested_value(duplicate, ("capture", "duplicate"), False))
    gates.append(_gate("duplicate_submit_has_one_active_capture", PASS if one_active else FAIL, f"capture_count={len(adapter.captures)}, duplicate={_nested_value(duplicate, ('capture', 'duplicate'))!r}"))

    failed = adapter.process()
    adapter.set_provider("available")
    retried = adapter.retry()
    retry_ok = not failed.get("ok") and retried.get("ok") and int(_nested_value(retried, ("processing", "processed"), 0) or 0) == 1
    gates.append(_gate("provider_failure_is_retryable", PASS if retry_ok else FAIL, f"failure_ok={failed.get('ok')!r}, retry_ok={retried.get('ok')!r}, processed={_nested_value(retried, ('processing', 'processed'))!r}"))

    restart_adapter = MockHostAdapter()
    restart_adapter.begin_case("SMOKE-RESTART")
    restart_adapter.capture({"id": "pending-note", "type": "capture", "text": "pending", "idempotency_key": "smoke-pending"})
    restart = restart_adapter.restart()
    restart_ok = bool(_nested_value(restart, ("restart", "state_preserved"), False)) and len(restart_adapter.captures) == 1
    gates.append(_gate("restart_preserves_pending_state", PASS if restart_ok else FAIL, f"state_preserved={_nested_value(restart, ('restart', 'state_preserved'))!r}, captures={len(restart_adapter.captures)}"))

    fixture_path = resolve_fixture("blue-suitcase.svg", fixtures_dir)
    attachment = restart_adapter.capture({"id": "image-note", "type": "capture", "attachment": {"fixture": "blue-suitcase.svg", "mime_type": "image/svg+xml"}, "idempotency_key": "smoke-image"}, fixture_path=fixture_path)
    attachment_ok = bool(_nested_value(attachment, ("capture", "attachment", "sha256")))
    gates.append(_gate("attachment_receipt_has_content_fingerprint", PASS if attachment_ok else FAIL, f"fingerprint_present={attachment_ok}"))

    gates.append(_gate("harness_does_not_call_live_provider", PASS, "MockHostAdapter has no provider client; provider_calls measures only simulated failures."))
    return gates


def _coverage(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    def has_step(case: dict[str, Any], *step_types: str) -> bool:
        return any(step.get("type") in step_types for step in case.get("steps", []))

    predicates: dict[str, Callable[[dict[str, Any]], bool]] = {
        "capture": lambda case: has_step(case, "capture"),
        "memory": lambda case: has_step(case, "memory") or "memory" in case.get("tags", []),
        "attention": lambda case: has_step(case, "attention"),
        "ask": lambda case: has_step(case, "ask"),
        "undo": lambda case: has_step(case, "undo"),
        "attachments": lambda case: any("attachment" in step for step in case.get("steps", [])),
        "reliability": lambda case: has_step(case, "process", "retry", "restart", "set_provider") or "reliability" in case.get("tags", []),
        "open_world": lambda case: "open-world" in case.get("tags", []),
        "false_positive_attention": lambda case: "false-positive" in case.get("tags", []),
    }
    return {
        name: {
            "case_count": sum(predicate(case) for case in cases),
            "case_ids": [case["case_id"] for case in cases if predicate(case)],
        }
        for name, predicate in predicates.items()
    }


def build_report(cases: list[dict[str, Any]], results: list[dict[str, Any]], *, adapter_name: str, quality_gates: list[dict[str, str]]) -> dict[str, Any]:
    status_counts = {status: sum(result["status"] == status for result in results) for status in (PASS, FAIL, PARTIAL, NOT_TESTED)}
    return {
        "report_type": "product-v2-dogfood-acceptance",
        "suite": "Product V2 dogfood / acceptance suite",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "adapter": adapter_name,
        "live_provider_used": False,
        "target_provider_calls_possible": adapter_name == "http",
        "case_count": len(cases),
        "case_status_counts": status_counts,
        "coverage": _coverage(cases),
        "quality_gates": quality_gates,
        "limitations": [
            "Cases are visible development acceptance tests, not unseen generalization evidence.",
            "The mock adapter covers transport and reliability plumbing only; absent semantic surfaces are reported as NOT TESTED.",
            "The HTTP adapter does not reset or restart a target Host; isolate a real run outside the harness.",
        ],
        "cases": results,
    }


def _adapter_from_args(args: argparse.Namespace) -> Any:
    if args.adapter == "mock":
        return MockHostAdapter()
    if not args.base_url:
        raise CaseValidationError("--base-url is required with --adapter http")
    return HttpHostAdapter(args.base_url)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=("mock", "http"), default="mock")
    parser.add_argument("--base-url")
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES_DIR)
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURES_DIR)
    parser.add_argument("--case-id")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    try:
        cases = load_cases(args.cases_dir, args.fixtures_dir)
        adapter = _adapter_from_args(args)
    except CaseValidationError as error:
        print(f"case validation failed: {error}", file=sys.stderr)
        return 2

    if args.case_id:
        cases = [case for case in cases if case["case_id"] == args.case_id]
        if not cases:
            print(f"unknown case_id: {args.case_id}", file=sys.stderr)
            return 2

    results = [run_case(case, adapter, fixtures_dir=args.fixtures_dir) for case in cases]
    quality_gates = run_mock_quality_gates(args.fixtures_dir) if args.adapter == "mock" else [_gate("mock_quality_gates", NOT_TESTED, "Run with --adapter mock for deterministic CI gates.")]
    report = build_report(cases, results, adapter_name=args.adapter, quality_gates=quality_gates)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if any(result["status"] == FAIL for result in results) or any(gate["status"] == FAIL for gate in quality_gates) else 0


if __name__ == "__main__":
    raise SystemExit(main())
