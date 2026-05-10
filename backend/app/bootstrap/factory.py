"""Flask application factory (orchestrates bootstrap modules)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from flask import Flask

from .api_blueprints import register_api_blueprints
from .cli import register_app_cli
from .database_extensions import register_database_extensions
from .default_settings import apply_default_config
from .load_dotenv_files import load_backend_dotenv_files
from .ollama_events import register_ollama_idle_and_event_stream
from .spa_static import register_spa_static_routes


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    """Flask app with API blueprints, databases, Ollama idle handling, and SSE hub.

    Registers health, dictionary, article read, news refresh, settings, Ollama idle,
    and SSE stream blueprints. Optionally serves a Vite SPA from ``STATIC_SPA_DIR``
    when ``index.html`` exists there (same-origin ``/`` and client routes). Bootstraps
    ``app.db`` on first start when the file at ``DATABASE_PATH`` is missing; bootstraps
    ``vectors.db`` when that path is missing.
    ``test_config`` updates ``app.config`` before defaults that depend on ``TESTING``.
    """
    if test_config is None or not test_config.get("TESTING", False):
        load_backend_dotenv_files()
    app = Flask(__name__)
    apply_default_config(app, test_config)
    register_database_extensions(app)
    register_api_blueprints(app)
    register_spa_static_routes(app)
    register_ollama_idle_and_event_stream(app)
    register_app_cli(app)
    return app
