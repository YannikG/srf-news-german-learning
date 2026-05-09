"""Flask application factory.

Phase 1 only wires the health route; later phases add real blueprints.
"""

from __future__ import annotations

from flask import Flask

from .health import health_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    return app
