"""Flask application factory.

Phase 1 only wires the health route; later phases add real blueprints.
The factory accepts an optional config mapping so tests (and later environments)
can inject overrides without mutating an already-built app.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from flask import Flask

from .health import health_bp


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    if test_config is not None:
        app.config.update(test_config)
    app.register_blueprint(health_bp, url_prefix="/api")
    return app
