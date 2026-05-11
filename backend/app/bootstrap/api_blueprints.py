"""Register HTTP API blueprints (shared ``/api`` prefix)."""

from __future__ import annotations

from flask import Flask

from ..articles import articles_bp
from ..events import events_bp
from ..health import health_bp
from ..news import news_bp
from ..ollama import ollama_bp
from ..pons import pons_bp
from ..settings import settings_bp
from ..words import words_bp


def register_api_blueprints(app: Flask) -> None:
    """Mount feature blueprints under ``/api``."""
    prefix = "/api"
    app.register_blueprint(health_bp, url_prefix=prefix)
    app.register_blueprint(words_bp, url_prefix=prefix)
    app.register_blueprint(articles_bp, url_prefix=prefix)
    app.register_blueprint(news_bp, url_prefix=prefix)
    app.register_blueprint(settings_bp, url_prefix=prefix)
    app.register_blueprint(ollama_bp, url_prefix=prefix)
    app.register_blueprint(pons_bp, url_prefix=prefix)
    app.register_blueprint(events_bp, url_prefix=prefix)
