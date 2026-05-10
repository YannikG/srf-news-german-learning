"""Flask application factory (orchestrates bootstrap modules)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from flask import Flask

from .api_blueprints import register_api_blueprints
from .cli import register_app_cli
from .database_extensions import register_database_extensions
from .default_settings import apply_default_config
from .ollama_events import register_ollama_idle_and_event_stream


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    """Flask app with API blueprints, databases, Ollama idle handling, and SSE hub.

    Registers health, dictionary, article read, news refresh, settings, Ollama idle,
    and SSE stream blueprints. Bootstraps ``app.db`` on first start when the file at
    ``DATABASE_PATH`` is missing; bootstraps ``vectors.db`` when that path is missing.
    ``test_config`` updates ``app.config`` before defaults that depend on ``TESTING``.
    """
    app = Flask(__name__)
    apply_default_config(app, test_config)
    register_database_extensions(app)
    register_api_blueprints(app)
    register_ollama_idle_and_event_stream(app)
    register_app_cli(app)
    return app
