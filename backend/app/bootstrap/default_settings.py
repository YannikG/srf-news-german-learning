"""Flask ``app.config`` defaults and environment-derived integers."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from flask import Flask

from ..db import APP_DB_PATH

_APP_PACKAGE_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_STATIC_SPA_DIR = _APP_PACKAGE_DIR / "static" / "spa"


def read_int_env(name: str, default: int) -> int:
    """Parse ``name`` from the process environment; return ``default`` if unset or invalid."""
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        return default


def normalize_ollama_idle_config(app: Flask) -> tuple[int, int]:
    """Return ``(idle_seconds, warning_seconds)`` with sane bounds; updates ``app.config``."""
    default_idle, default_warn = 600, 60
    raw_idle = app.config.get("OLLAMA_IDLE_SHUTDOWN_SECONDS", default_idle)
    raw_warn = app.config.get("OLLAMA_SHUTDOWN_WARNING_SECONDS", default_warn)
    try:
        idle_sec = int(raw_idle)
    except (TypeError, ValueError):
        idle_sec = default_idle
    try:
        warn_sec = int(raw_warn)
    except (TypeError, ValueError):
        warn_sec = default_warn
    idle_sec = max(1, idle_sec)
    warn_sec = max(0, min(warn_sec, idle_sec))
    app.config["OLLAMA_IDLE_SHUTDOWN_SECONDS"] = idle_sec
    app.config["OLLAMA_SHUTDOWN_WARNING_SECONDS"] = warn_sec
    return idle_sec, warn_sec


def apply_default_config(app: Flask, test_config: Mapping[str, Any] | None) -> None:
    """Apply baseline config, then optional ``test_config`` overrides."""
    app.config.setdefault("DATABASE_PATH", str(APP_DB_PATH))
    app.config.setdefault(
        "STATIC_SPA_DIR",
        os.environ.get("STATIC_SPA_DIR", str(_DEFAULT_STATIC_SPA_DIR)),
    )
    app.config.setdefault("SIDECAR_BASE_URL", os.environ.get("SIDECAR_BASE_URL", ""))
    app.config.setdefault("SIDECAR_SHARED_SECRET", os.environ.get("SIDECAR_SHARED_SECRET", ""))
    app.config.setdefault("OLLAMA_BASE_URL", os.environ.get("OLLAMA_BASE_URL", ""))
    app.config.setdefault(
        "OLLAMA_SIMPLIFY_MODEL",
        os.environ.get("OLLAMA_SIMPLIFY_MODEL", "gemma4:e2b"),
    )

    if test_config is not None:
        app.config.update(test_config)

    app.config.setdefault(
        "OLLAMA_IDLE_SHUTDOWN_SECONDS",
        read_int_env("OLLAMA_IDLE_SHUTDOWN_SECONDS", 600),
    )
    app.config.setdefault(
        "OLLAMA_SHUTDOWN_WARNING_SECONDS",
        read_int_env("OLLAMA_SHUTDOWN_WARNING_SECONDS", 60),
    )
    app.config.setdefault("OLLAMA_IDLE_START_POLL_THREAD", not app.config.get("TESTING", False))
