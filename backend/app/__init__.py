"""Flask application factory.

Registriert Health- und Wörterbuch-API, initialisiert ``app.db`` beim ersten Start,
wenn die Datei unter ``DATABASE_PATH`` noch fehlt. Optionales ``test_config``-Mapping
für Tests und Umgebungen ohne nachträgliche Mutation einer gebauten App.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import click
from flask import Flask

from .db import APP_DB_PATH, init_database
from .health import health_bp
from .persistence import SQL_DATABASE_EXTENSION_KEY, SqlDatabase
from .words import words_bp


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.setdefault("DATABASE_PATH", str(APP_DB_PATH))

    if test_config is not None:
        app.config.update(test_config)

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
