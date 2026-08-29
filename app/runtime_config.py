"""Validated, non-sensitive configuration for the local Blackhole Host."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNTIME_CONFIG_VERSION = "blackhole-runtime-config-v1"
DEFAULT_PROVIDER = "codex"
DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT = "high"
DEFAULT_TIMEOUT_SECONDS = 900
DEFAULT_BATCH_SIZE = 10
DEFAULT_DATABASE_NAME = "blackhole.db"
CONFIG_FILENAME = "config.json"
SUPPORTED_REASONING_EFFORTS = frozenset({"max", "high", "medium"})
SENSITIVE_CONFIG_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "auth_cookie",
        "auth_path",
        "authentication",
        "client_secret",
        "credentials",
        "password",
        "secret",
        "token",
    }
)


def resolve_home(home: str | Path | None = None) -> Path:
    """Resolve the explicit home override or the platform user's default."""

    if home is None:
        configured = os.environ.get("BLACKHOLE_HOME")
        if configured is not None:
            if not configured.strip():
                raise ValueError("BLACKHOLE_HOME must not be empty")
            home = configured
        else:
            home = Path.home() / ".blackhole"
    if not isinstance(home, (str, Path)) or not str(home).strip():
        raise ValueError("Blackhole home must be a non-empty path")
    return Path(home).expanduser().resolve()


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _is_sensitive_key(key: Any) -> bool:
    normalized = str(key).casefold().replace("-", "_")
    return normalized in SENSITIVE_CONFIG_KEYS or any(
        marker in normalized for marker in ("token", "secret", "password", "cookie", "credential", "auth_path")
    )


@dataclass
class RuntimeConfig:
    """Small product-runtime configuration with no credential fields."""

    home: Path
    database_path: Path
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    reasoning_effort: str = DEFAULT_REASONING_EFFORT
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    batch_size: int = DEFAULT_BATCH_SIZE
    version: str = RUNTIME_CONFIG_VERSION

    def __post_init__(self) -> None:
        self.home = resolve_home(self.home)
        database = Path(self.database_path).expanduser()
        if not database.is_absolute():
            database = self.home / database
        self.database_path = database.resolve()
        try:
            self.database_path.relative_to(self.home)
        except ValueError as error:
            raise ValueError("database must remain inside BLACKHOLE_HOME") from error
        self.validate()

    @classmethod
    def defaults(cls, home: str | Path | None = None) -> "RuntimeConfig":
        resolved_home = resolve_home(home)
        return cls(home=resolved_home, database_path=resolved_home / DEFAULT_DATABASE_NAME)

    @property
    def config_path(self) -> Path:
        return self.home / CONFIG_FILENAME

    def validate(self) -> None:
        if self.version != RUNTIME_CONFIG_VERSION:
            raise ValueError(f"unsupported runtime config version: {self.version}")
        if not isinstance(self.provider, str) or self.provider != DEFAULT_PROVIDER:
            raise ValueError(f"unsupported provider: {self.provider}")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model must be a non-empty string")
        if not isinstance(self.reasoning_effort, str) or self.reasoning_effort not in SUPPORTED_REASONING_EFFORTS:
            raise ValueError(f"unsupported reasoning effort: {self.reasoning_effort}")
        _positive_integer(self.timeout_seconds, "timeout_seconds")
        _positive_integer(self.batch_size, "batch_size")

    def to_dict(self) -> dict[str, Any]:
        """Return exactly the fields Blackhole is allowed to persist."""

        database = self.database_path.relative_to(self.home).as_posix()
        return {
            "config_version": self.version,
            "provider": self.provider,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "timeout_seconds": self.timeout_seconds,
            "batch_size": self.batch_size,
            "database": database,
        }

    def save(self) -> Path:
        """Persist configuration atomically without creating a secret store."""

        self.validate()
        self.home.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.home,
                prefix=".config-",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(payload)
                temporary_name = temporary.name
            Path(temporary_name).replace(self.config_path)
        finally:
            if temporary_name is not None:
                temporary_path = Path(temporary_name)
                if temporary_path.exists():
                    temporary_path.unlink()
        return self.config_path

    @classmethod
    def load(cls, path: str | Path) -> "RuntimeConfig":
        config_path = Path(path).expanduser().resolve()
        value = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("runtime config must be a JSON object")
        if any(_is_sensitive_key(key) for key in value):
            raise ValueError("runtime config must not contain credentials or secrets")

        home = config_path.parent
        database_value = value.get("database", DEFAULT_DATABASE_NAME)
        if not isinstance(database_value, str) or not database_value.strip():
            raise ValueError("database must be a relative path")
        database = Path(database_value)
        if database.is_absolute() or ".." in database.parts:
            raise ValueError("database must be a relative path inside BLACKHOLE_HOME")

        config = cls(
            home=home,
            database_path=home / database,
            provider=value.get("provider", DEFAULT_PROVIDER),
            model=value.get("model", DEFAULT_MODEL),
            reasoning_effort=value.get("reasoning_effort", DEFAULT_REASONING_EFFORT),
            timeout_seconds=value.get("timeout_seconds", value.get("timeout", DEFAULT_TIMEOUT_SECONDS)),
            batch_size=value.get("batch_size", DEFAULT_BATCH_SIZE),
            version=value.get("config_version", RUNTIME_CONFIG_VERSION),
        )
        return config

    @classmethod
    def load_or_create(cls, home: str | Path | None = None) -> "RuntimeConfig":
        resolved_home = resolve_home(home)
        path = resolved_home / CONFIG_FILENAME
        if path.exists():
            return cls.load(path)
        config = cls.defaults(resolved_home)
        config.save()
        return config


__all__ = [
    "CONFIG_FILENAME",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_DATABASE_NAME",
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "DEFAULT_REASONING_EFFORT",
    "DEFAULT_TIMEOUT_SECONDS",
    "RUNTIME_CONFIG_VERSION",
    "RuntimeConfig",
    "SUPPORTED_REASONING_EFFORTS",
    "resolve_home",
]
