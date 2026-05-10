"""Flask application factory.

Registers health, dictionary, article read, news refresh, settings, Ollama idle,
and SSE events blueprints;
bootstraps ``app.db`` on first start when the file at ``DATABASE_PATH`` is missing,
and accepts an optional
``test_config`` map so tests and environments can inject settings without mutating an
already-built app.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click
from flask import Flask

from .articles import articles_bp
from .db import APP_DB_PATH, init_database
from .events import EVENTS_SSE_HUB_KEY, SseHub, events_bp
from .health import health_bp
from .news import news_bp
from .ollama import OLLAMA_IDLE_SERVICE_KEY, ollama_bp
from .ollama.poll import start_idle_poll_thread
from .ollama.service import OllamaIdleService
from .persistence import SQL_DATABASE_EXTENSION_KEY, SqlDatabase
from .settings import settings_bp
from .sidecar.client import post_ollama_stop
from .words import words_bp


def _int_from_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        return default


def _normalize_ollama_idle_config(app: Flask) -> tuple[int, int]:
    """Return (idle_seconds, warning_seconds) with sane bounds; updates app.config."""
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


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.setdefault("DATABASE_PATH", str(APP_DB_PATH))
    app.config.setdefault("SIDECAR_BASE_URL", os.environ.get("SIDECAR_BASE_URL", ""))
    app.config.setdefault("SIDECAR_SHARED_SECRET", os.environ.get("SIDECAR_SHARED_SECRET", ""))

    if test_config is not None:
        app.config.update(test_config)

    app.config.setdefault(
        "OLLAMA_IDLE_SHUTDOWN_SECONDS",
        _int_from_env("OLLAMA_IDLE_SHUTDOWN_SECONDS", 600),
    )
    app.config.setdefault(
        "OLLAMA_SHUTDOWN_WARNING_SECONDS",
        _int_from_env("OLLAMA_SHUTDOWN_WARNING_SECONDS", 60),
    )
    app.config.setdefault("OLLAMA_IDLE_START_POLL_THREAD", not app.config.get("TESTING", False))

    db_path_str = app.config.get("DATABASE_PATH")
    if db_path_str:
        app.extensions[SQL_DATABASE_EXTENSION_KEY] = SqlDatabase(db_path_str)
        db_path = Path(db_path_str)
        if not db_path.is_file():
            # First boot only: create the file and apply all migrations. For schema
            # updates on an existing file, run `flask init-db` (not every app start).
            init_database(db_path)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(words_bp, url_prefix="/api")
    app.register_blueprint(articles_bp, url_prefix="/api")
    app.register_blueprint(news_bp, url_prefix="/api")
    app.register_blueprint(settings_bp, url_prefix="/api")
    app.register_blueprint(ollama_bp, url_prefix="/api")
    app.register_blueprint(events_bp, url_prefix="/api")

    sidecar_base = str(app.config.get("SIDECAR_BASE_URL") or "").strip()
    sidecar_secret_raw = app.config.get("SIDECAR_SHARED_SECRET")
    sidecar_secret = sidecar_secret_raw if isinstance(sidecar_secret_raw, str) else ""
    idle_sec, warn_sec = _normalize_ollama_idle_config(app)

    def _stop_ollama() -> tuple[bool, str | None]:
        if not sidecar_base:
            return False, "SIDECAR_BASE_URL is not set"
        return post_ollama_stop(sidecar_base, sidecar_secret or None)

    idle_svc = OllamaIdleService(
        idle_shutdown_seconds=float(idle_sec),
        warning_seconds=float(warn_sec),
        stop_fn=_stop_ollama,
        idle_enabled=bool(sidecar_base),
    )
    app.extensions[OLLAMA_IDLE_SERVICE_KEY] = idle_svc

    sse_hub = SseHub()
    app.extensions[EVENTS_SSE_HUB_KEY] = sse_hub

    def _publish_ollama_state() -> None:
        sse_hub.publish("ollama_state", idle_svc.sse_public_state())

    idle_svc.add_state_listener(_publish_ollama_state)

    def _on_idle_warning() -> None:
        sse_hub.publish("shutdown_warning", {"warning_seconds": warn_sec})

    idle_svc.add_warning_listener(_on_idle_warning)

    if app.config.get("OLLAMA_IDLE_START_POLL_THREAD"):
        start_idle_poll_thread(app)

    _register_cli(app)
    return app


def _register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Apply pending migrations (existing DB: release deploy, schema updates)."""
        db_path = app.config.get("DATABASE_PATH")
        if not db_path:
            raise click.UsageError("DATABASE_PATH is not set.")
        ran = init_database(db_path)
        if ran:
            click.echo(f"Applied migrations at {db_path}: {', '.join(ran)}")
        else:
            click.echo(f"No pending migrations at {db_path}.")
