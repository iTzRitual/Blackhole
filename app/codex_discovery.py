"""Safe capability discovery for the externally authenticated Codex CLI."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


CODEX_PROVIDER_TYPE = "codex-cli"
MISSING = "MISSING"
INSTALLED_NOT_AUTHENTICATED = "INSTALLED_NOT_AUTHENTICATED"
READY = "READY"
ERROR = "ERROR"
DISCOVERY_TIMEOUT_SECONDS = 5
SUPPORTED_REASONING_EFFORTS = frozenset({"max", "high", "medium"})
VALID_STATUSES = frozenset({MISSING, INSTALLED_NOT_AUTHENTICATED, READY, ERROR})


@dataclass(frozen=True)
class ProviderStatus:
    """Machine-readable provider state with only safe summary fields."""

    status: str
    installed: bool
    authenticated: bool | None
    version: str | None
    auth_check_available: bool
    configured_runtime: bool
    ready: bool
    error_code: str | None = None
    type: str = CODEX_PROVIDER_TYPE

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": self.type,
            "status": self.status,
            "installed": self.installed,
            "authenticated": self.authenticated,
            "version": self.version,
            "auth_check_available": self.auth_check_available,
            "configured_runtime": self.configured_runtime,
            "ready": self.ready,
        }
        if self.error_code is not None:
            result["error_code"] = self.error_code
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ProviderStatus":
        status = value.get("status", ERROR)
        if status not in VALID_STATUSES:
            status = ERROR
        raw_version = value.get("version")
        version_match = (
            re.search(r"\b\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9.]+)?\b", raw_version)
            if isinstance(raw_version, str)
            else None
        )
        version = f"codex-cli {version_match.group(0)}" if version_match else None
        configured_runtime = bool(value.get("configured_runtime", False))
        installed = bool(value.get("installed", False))
        authenticated = value.get("authenticated") if isinstance(value.get("authenticated"), bool) else None
        ready = status == READY and installed and authenticated is True and configured_runtime
        raw_error = value.get("error_code")
        error_code = raw_error if isinstance(raw_error, str) and re.fullmatch(r"[a-z0-9_]+", raw_error) else None
        return cls(
            status=status,
            installed=installed,
            authenticated=authenticated,
            version=version,
            auth_check_available=bool(value.get("auth_check_available", False)),
            configured_runtime=configured_runtime,
            ready=ready,
            error_code=error_code,
            type=CODEX_PROVIDER_TYPE,
        )


def _run(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=DISCOVERY_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _version_summary(result: subprocess.CompletedProcess[str] | None) -> str | None:
    if result is None:
        return None
    text = "\n".join(part for part in (result.stdout, result.stderr) if isinstance(part, str))
    match = re.search(r"\b\d+\.\d+(?:\.\d+)?(?:[-+][A-Za-z0-9.]+)?\b", text)
    return f"codex-cli {match.group(0)}" if match else None


def _authentication_result(result: subprocess.CompletedProcess[str] | None) -> tuple[bool | None, bool, str | None]:
    if result is None:
        return None, False, "auth_check_failed"
    text = "\n".join(part for part in (result.stdout, result.stderr) if isinstance(part, str)).casefold()
    negative_markers = (
        "not logged",
        "not authenticated",
        "unauthenticated",
        "login required",
        "not logged in",
    )
    positive_markers = (
        "logged in",
        "authenticated",
        "login status: logged",
    )
    if any(marker in text for marker in negative_markers):
        return False, True, None
    if result.returncode == 0 and any(marker in text for marker in positive_markers):
        return True, True, None
    if result.returncode == 0:
        return None, True, "auth_status_unrecognized"
    return None, True, "auth_check_failed"


def discover_codex(
    *,
    configured_model: str,
    configured_reasoning: str,
) -> ProviderStatus:
    """Discover PATH/version/login status without reading credential material."""

    configured_runtime = bool(configured_model.strip()) and configured_reasoning in SUPPORTED_REASONING_EFFORTS
    executable = shutil.which("codex")
    if not executable:
        return ProviderStatus(
            status=MISSING,
            installed=False,
            authenticated=None,
            version=None,
            auth_check_available=False,
            configured_runtime=configured_runtime,
            ready=False,
            error_code="binary_not_found",
        )

    version_result = _run([executable, "--version"])
    version = _version_summary(version_result)
    if version_result is None or version_result.returncode != 0 or version is None:
        return ProviderStatus(
            status=ERROR,
            installed=True,
            authenticated=None,
            version=version,
            auth_check_available=False,
            configured_runtime=configured_runtime,
            ready=False,
            error_code="version_check_failed",
        )

    auth_result = _run([executable, "login", "status"])
    authenticated, auth_check_available, auth_error = _authentication_result(auth_result)
    if not configured_runtime:
        status = ERROR
        error_code = "runtime_config_invalid"
        ready = False
    elif authenticated is False:
        status = INSTALLED_NOT_AUTHENTICATED
        error_code = None
        ready = False
    elif authenticated is True:
        status = READY
        error_code = None
        ready = True
    else:
        status = ERROR
        error_code = auth_error or "auth_status_unavailable"
        ready = False
    return ProviderStatus(
        status=status,
        installed=True,
        authenticated=authenticated,
        version=version,
        auth_check_available=auth_check_available,
        configured_runtime=configured_runtime,
        ready=ready,
        error_code=error_code,
    )


__all__ = [
    "ERROR",
    "INSTALLED_NOT_AUTHENTICATED",
    "MISSING",
    "READY",
    "ProviderStatus",
    "discover_codex",
]
