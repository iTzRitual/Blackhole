"""Run a deterministic, offline Blackhole submission qualification audit.

The audit deliberately reads only the repository passed as ``--root``.  It
does not import application runtime code, invoke a provider, inspect a user's
home directory, or require network access.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


CURRENT_ADVANCED_RESULT = Path("eval/results/experiment-005-duplicate-evidence-full.json")
CURRENT_ADVANCED_LQA = 0.8695006212469447
CURRENT_ADVANCED_DSCR = 40


@dataclass(frozen=True)
class Finding:
    """A user-safe audit finding.

    Findings contain paths and rule names only where sensitive material could
    be involved.  They never retain or print matched secret values.
    """

    level: str
    code: str
    message: str


@dataclass(frozen=True)
class SecretFinding:
    path: str
    rule: str


@dataclass(frozen=True)
class PathFinding:
    path: str
    line: int
    kind: str


@dataclass(frozen=True)
class TrajectoryRecord:
    trajectory_id: str
    trajectory_type: str
    prompt_present: bool
    summary_present: bool
    runtime_artifacts_present: bool | None
    raw_trace_available: bool
    artifact_count: int


@dataclass
class AuditReport:
    findings: list[Finding] = field(default_factory=list)
    coding_trajectories: list[TrajectoryRecord] = field(default_factory=list)
    runtime_trajectories: list[TrajectoryRecord] = field(default_factory=list)
    secret_findings: list[SecretFinding] = field(default_factory=list)
    path_findings: list[PathFinding] = field(default_factory=list)

    @property
    def hard_failures(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "FAIL"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "WARN"]


REQUIRED_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    ("README present", "README.md", "file"),
    ("Improvement Changelog present", "IMPROVEMENT_CHANGELOG.md", "file"),
    ("reproduction guide present", "docs/REPRODUCTION.md", "file"),
    ("benchmark documentation present", "benchmark/README.md", "file"),
    ("benchmark contract present", "benchmark/dev/response-contract-v2.json", "file"),
    ("baseline implementation present", "baseline/run_baseline.py", "file"),
    ("baseline evidence present", "eval/results/baseline-v1.json", "file"),
    ("advanced application implementation present", "app/advanced_runner.py", "file"),
    ("evaluation results directory present", "eval/results", "directory"),
    ("coding trajectories directory present", "trajectories/coding", "directory"),
    ("runtime trajectories directory present", "trajectories/runtime", "directory"),
)


API_ASSIGNMENT_RE = re.compile(
    r"(?im)\b(?P<name>OPENAI_API_KEY|ANTHROPIC_API_KEY)\s*=\s*"
    r"(?P<value>\"[^\"]*\"|'[^']*'|[^\s#]+)"
)
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private key header",
        re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    ),
    (
        "Bearer token",
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{24,}\b"),
    ),
    (
        "OpenAI-style token",
        re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{19,}\b"),
    ),
    (
        "GitHub token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "Slack token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    ),
    (
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
)

ABSOLUTE_DEVELOPER_PATH_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]"
    r"(?:Users|home|tmp)[\\/]|/(?:Users|home|tmp)/)"
)
NAMED_ARTIFACT_RE = re.compile(r"(?i)(?:final|latest|comparison|submission)")


def _relative_path(root: Path, path: Path) -> str:
    """Return a stable repository-relative path for user-facing output."""

    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_placeholder_secret(value: str) -> bool:
    """Recognize documentation/configuration placeholders, not credentials."""

    normalized = value.strip().strip("`\"'").strip().lower()
    if not normalized:
        return True
    if normalized.startswith("<") and normalized.endswith(">"):
        return True
    if normalized.startswith("$"):
        return True
    if normalized in {
        "...",
        "…",
        "your-key",
        "your_api_key",
        "your-api-key",
        "replace-me",
        "replace_with_your_key",
        "replace-with-your-key",
        "changeme",
        "example",
        "dummy",
        "none",
        "null",
    }:
        return True
    if normalized.startswith(("your-", "your_", "placeholder", "replace_", "replace-")):
        return True
    if normalized.startswith(("os.environ", "os.getenv(", "getenv(", "env.get(")):
        return True
    if len(set(normalized)) == 1 and normalized[0] in "x0_-":
        return True
    return False


def scan_text_for_secrets(text: str) -> list[str]:
    """Return rule names for obvious credential material in ``text``.

    The return value intentionally excludes the matched text.  Named API-key
    assignments are checked separately so a short synthetic value is still
    caught, while examples such as ``OPENAI_API_KEY=<your-key>`` are ignored.
    """

    rules: set[str] = set()
    for match in API_ASSIGNMENT_RE.finditer(text):
        value = match.group("value")
        if not _is_placeholder_secret(value):
            rules.add(f"{match.group('name')} assignment")
    for rule, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            rules.add(rule)
    return sorted(rules)


def _safe_text(path: Path) -> str | None:
    """Read a tracked text file while skipping binary content."""

    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def git_tracked_paths(root: Path) -> tuple[list[Path], bool]:
    """Return tracked paths and whether Git provided a reliable inventory."""

    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return [], False
    if result.returncode != 0:
        return [], False
    raw_paths = result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return [Path(item) for item in raw_paths if item], True


def _safe_repo_path(root: Path, relative_path: Path) -> Path | None:
    """Resolve a repository-relative path without permitting escape outside root."""

    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def scan_tracked_files_for_secrets(
    root: Path, tracked_paths: Iterable[str | Path]
) -> list[SecretFinding]:
    """Scan only the supplied repository-controlled tracked paths."""

    findings: list[SecretFinding] = []
    for raw_path in tracked_paths:
        relative_path = Path(raw_path)
        path = _safe_repo_path(root, relative_path)
        if path is None or not path.is_file():
            continue
        text = _safe_text(path)
        if text is None:
            continue
        for rule in scan_text_for_secrets(text):
            findings.append(
                SecretFinding(path=relative_path.as_posix(), rule=rule)
            )
    return sorted(findings, key=lambda item: (item.path, item.rule))


def check_required_artifacts(root: Path) -> list[Finding]:
    """Check the hard repository-shape requirements."""

    findings: list[Finding] = []
    for label, relative, kind in REQUIRED_ARTIFACTS:
        path = root / relative
        present = path.is_file() if kind == "file" else path.is_dir()
        if present:
            findings.append(Finding("PASS", "required-artifact", f"{label}: {relative}"))
        else:
            findings.append(Finding("FAIL", "required-artifact", f"{label} missing: {relative}"))
    return findings


def _has_runtime_prompt(path: Path) -> bool:
    return any(
        child.is_file()
        and (child.name == "prompt.md" or child.name.endswith(".prompt.txt"))
        for child in path.rglob("*")
    )


def _has_runtime_trace(path: Path, trajectory_type: str) -> bool:
    if trajectory_type == "coding":
        return any((path / name).is_file() for name in ("transcript.txt", "transcript.json"))
    return any(
        child.is_file()
        and (
            child.name in {"trace.json", "transcript.txt", "transcript.json"}
            or child.name.endswith(".raw.txt")
        )
        for child in path.rglob("*")
    )


def inventory_trajectories(root: Path) -> list[TrajectoryRecord]:
    """Inventory coding and runtime trajectory directories deterministically."""

    records: list[TrajectoryRecord] = []
    for trajectory_type, parent in (
        ("coding", root / "trajectories" / "coding"),
        ("runtime", root / "trajectories" / "runtime"),
    ):
        if not parent.is_dir():
            continue
        for directory in sorted((item for item in parent.iterdir() if item.is_dir()), key=lambda item: item.name):
            files = [item for item in directory.rglob("*") if item.is_file()]
            if trajectory_type == "coding":
                prompt_present = (directory / "prompt.md").is_file()
                summary_present = (directory / "summary.md").is_file()
                runtime_artifacts_present: bool | None = None
            else:
                prompt_present = _has_runtime_prompt(directory)
                summary_present = (directory / "summary.md").is_file()
                runtime_artifacts_present = bool(files)
            records.append(
                TrajectoryRecord(
                    trajectory_id=directory.name,
                    trajectory_type=trajectory_type,
                    prompt_present=prompt_present,
                    summary_present=summary_present,
                    runtime_artifacts_present=runtime_artifacts_present,
                    raw_trace_available=_has_runtime_trace(directory, trajectory_type),
                    artifact_count=len(files),
                )
            )
    return records


def check_trajectory_inventory(
    records: Sequence[TrajectoryRecord],
) -> list[Finding]:
    """Require documented coding trajectories but not fabricated transcripts."""

    findings: list[Finding] = []
    coding = [record for record in records if record.trajectory_type == "coding"]
    runtime = [record for record in records if record.trajectory_type == "runtime"]
    if coding:
        findings.append(
            Finding("PASS", "trajectory-index", f"coding trajectories indexed: {len(coding)}")
        )
    else:
        findings.append(Finding("FAIL", "trajectory-index", "no coding trajectory directories found"))
    if runtime:
        findings.append(
            Finding("PASS", "trajectory-index", f"runtime trajectories indexed: {len(runtime)}")
        )
    else:
        findings.append(Finding("FAIL", "trajectory-index", "no runtime trajectory directories found"))

    for record in coding:
        missing: list[str] = []
        if not record.prompt_present:
            missing.append("prompt.md")
        if not record.summary_present:
            missing.append("summary.md")
        if missing:
            findings.append(
                Finding(
                    "FAIL",
                    "coding-trajectory-documentation",
                    f"{record.trajectory_id} missing {', '.join(missing)}",
                )
            )
    if coding and not any(
        finding.code == "coding-trajectory-documentation" and finding.level == "FAIL"
        for finding in findings
    ):
        documented = sum(record.prompt_present and record.summary_present for record in coding)
        raw = sum(record.raw_trace_available for record in coding)
        findings.append(
            Finding(
                "PASS",
                "coding-trajectory-documentation",
                f"coding trajectories documented: {documented}; authentic raw traces available: {raw}",
            )
        )
    for record in runtime:
        if not record.runtime_artifacts_present:
            findings.append(
                Finding(
                    "WARN",
                    "runtime-trajectory-artifacts",
                    f"{record.trajectory_id} has no runtime artifacts",
                )
            )
    return findings


def audit_submission_paths(
    root: Path, tracked_paths: Iterable[str | Path]
) -> list[PathFinding]:
    """Find developer-specific paths in submission-facing Markdown only.

    Trajectory Markdown is intentionally excluded: attachment and machine
    paths there can be legitimate historical evidence, not reproduction
    instructions.
    """

    findings: list[PathFinding] = []
    for raw_path in tracked_paths:
        relative_path = Path(raw_path)
        if relative_path.suffix.lower() != ".md":
            continue
        if relative_path.parts and relative_path.parts[0].lower() == "trajectories":
            continue
        path = _safe_repo_path(root, relative_path)
        if path is None or not path.is_file():
            continue
        text = _safe_text(path)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if ABSOLUTE_DEVELOPER_PATH_RE.search(line):
                findings.append(
                    PathFinding(
                        path=relative_path.as_posix(),
                        line=line_number,
                        kind="developer-specific absolute path",
                    )
                )
    return findings


def _metric_signature(data: object) -> tuple[float | None, int | None]:
    """Extract common score/DSCR shapes without assuming one result schema."""

    if not isinstance(data, dict):
        return None, None
    score: float | None = None
    dscr: int | None = None
    primary = data.get("primary")
    if isinstance(primary, dict) and isinstance(primary.get("score"), (int, float)):
        score = float(primary["score"])
    top_dscr = data.get("dscr")
    if isinstance(top_dscr, dict) and isinstance(top_dscr.get("count"), int):
        dscr = int(top_dscr["count"])
    latest = data.get("latest_kept_advanced")
    if isinstance(latest, dict):
        if score is None and isinstance(latest.get("lqa_0m"), (int, float)):
            score = float(latest["lqa_0m"])
        if dscr is None and isinstance(latest.get("dscr"), int):
            dscr = int(latest["dscr"])
    return score, dscr


def audit_named_evidence(root: Path) -> list[Finding]:
    """Warn when named final/comparison files lag the kept E005 result."""

    current_path = root / CURRENT_ADVANCED_RESULT
    if not current_path.is_file():
        return []
    findings: list[Finding] = []
    results_dir = root / "eval" / "results"
    if not results_dir.is_dir():
        return findings
    for path in sorted(results_dir.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file() or not NAMED_ARTIFACT_RE.search(path.stem):
            continue
        if path.resolve() == current_path.resolve():
            continue
        text = _safe_text(path)
        if text is None:
            continue
        score: float | None = None
        dscr: int | None = None
        data: object = None
        if path.suffix.lower() == ".json":
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None
            score, dscr = _metric_signature(data)
        if score is not None and dscr is not None:
            if abs(score - CURRENT_ADVANCED_LQA) > 1e-12 or dscr != CURRENT_ADVANCED_DSCR:
                findings.append(
                    Finding(
                        "WARN",
                        "stale-named-evidence",
                        f"{_relative_path(root, path)} reports LQA-0M={score:.10f}, DSCR={dscr}; "
                        f"kept E005 is LQA-0M={CURRENT_ADVANCED_LQA:.10f}, DSCR={CURRENT_ADVANCED_DSCR}",
                    )
                )
                continue
        if re.search(r"(?i)experiment[- _]?00[1-4]|generic projector|final gate c", text):
            findings.append(
                Finding(
                    "WARN",
                    "stale-named-evidence",
                    f"{_relative_path(root, path)} is a named final/comparison artifact that predates kept E005",
                )
            )
    return findings


def audit_metric_claims(root: Path) -> list[Finding]:
    """Report known current/final narrative claims that predate E005."""

    findings: list[Finding] = []
    evaluation = root / "docs" / "EVALUATION.md"
    evaluation_text = _safe_text(evaluation) if evaluation.is_file() else None
    if evaluation_text and "## 24. Final product-phase evidence" in evaluation_text:
        section = evaluation_text.split("## 24. Final product-phase evidence", 1)[1]
        section = section.split("## 25.", 1)[0]
        if "0.749229589" in section and "DSCR=72" in section:
            findings.append(
                Finding(
                    "WARN",
                    "metric-consistency",
                    "docs/EVALUATION.md section 24 presents the older E002 final claim "
                    "(LQA-0M=0.7492295899, DSCR=72); regenerate after integration/generalization freeze",
                )
            )
    reproduction = root / "docs" / "REPRODUCTION.md"
    reproduction_text = _safe_text(reproduction) if reproduction.is_file() else None
    if reproduction_text and "## 14. Final submission evidence" in reproduction_text:
        section = reproduction_text.split("## 14. Final submission evidence", 1)[1]
        section = section.split("## 15.", 1)[0]
        if "final-comparison-v1.json" in section:
            findings.append(
                Finding(
                    "WARN",
                    "metric-consistency",
                    "docs/REPRODUCTION.md section 14 still points final submission evidence "
                    "at the older final-comparison-v1 snapshot",
                )
            )
    return findings


def audit_repository(
    root: Path,
    *,
    tracked_paths: Iterable[str | Path] | None = None,
) -> AuditReport:
    """Run all deterministic checks for ``root``."""

    root = root.resolve()
    report = AuditReport()
    report.findings.extend(check_required_artifacts(root))
    records = inventory_trajectories(root)
    report.coding_trajectories = [record for record in records if record.trajectory_type == "coding"]
    report.runtime_trajectories = [record for record in records if record.trajectory_type == "runtime"]
    report.findings.extend(check_trajectory_inventory(records))

    if tracked_paths is None:
        tracked, git_ok = git_tracked_paths(root)
        if not git_ok:
            report.findings.append(
                Finding(
                    "WARN",
                    "tracked-file-inventory",
                    "Git tracked-file inventory unavailable; credential/path audits were skipped",
                )
            )
        tracked_paths = tracked
    tracked_list = list(tracked_paths)

    report.secret_findings = scan_tracked_files_for_secrets(root, tracked_list)
    if report.secret_findings:
        for secret in report.secret_findings:
            report.findings.append(
                Finding(
                    "FAIL",
                    "credential-hygiene",
                    f"{secret.path} — {secret.rule}",
                )
            )
    else:
        report.findings.append(Finding("PASS", "credential-hygiene", "no obvious committed credentials detected"))

    report.path_findings = audit_submission_paths(root, tracked_list)
    if report.path_findings:
        for finding in report.path_findings:
            report.findings.append(
                Finding(
                    "WARN",
                    "submission-path-audit",
                    f"{finding.path}:{finding.line} — {finding.kind}",
                )
            )
    else:
        report.findings.append(Finding("PASS", "submission-path-audit", "submission-facing Markdown has no developer-specific absolute paths"))

    report.findings.extend(audit_named_evidence(root))
    report.findings.extend(audit_metric_claims(root))
    return report


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "yes" if value else "no"


def print_inventory(report: AuditReport) -> None:
    print("\nTrajectory inventory")
    print("ID | Type | Prompt | Summary | Runtime artifacts | Raw trace | Files")
    print("--- | --- | --- | --- | --- | --- | ---")
    records = [*report.coding_trajectories, *report.runtime_trajectories]
    for record in records:
        print(
            f"{record.trajectory_id} | {record.trajectory_type} | "
            f"{_yes_no(record.prompt_present)} | {_yes_no(record.summary_present)} | "
            f"{_yes_no(record.runtime_artifacts_present)} | "
            f"{_yes_no(record.raw_trace_available)} | {record.artifact_count}"
        )


def print_report(report: AuditReport, *, include_inventory: bool = False) -> None:
    print("Blackhole qualification check")
    for finding in report.findings:
        print(f"[{finding.level}] {finding.message}")
    if include_inventory:
        print_inventory(report)
    if report.hard_failures:
        print(
            f"\nQualification checks failed with {len(report.hard_failures)} hard failure(s) "
            f"and {len(report.warnings)} warning(s)."
        )
    else:
        print(f"\nQualification checks passed with {len(report.warnings)} warning(s).")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root to audit (default: this script's repository)",
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="print the complete coding/runtime trajectory inventory",
    )
    args = parser.parse_args(argv)
    report = audit_repository(args.root)
    print_report(report, include_inventory=args.inventory)
    return 1 if report.hard_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
