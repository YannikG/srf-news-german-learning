"""Flask CLI commands bound to the application instance."""

from __future__ import annotations

import click
from flask import Flask

from ..db import init_database
from ..vectors import init_vectors_database


def register_app_cli(app: Flask) -> None:
    """Register ``init-db`` and ``init-vectors-db`` commands."""

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

    @app.cli.command("init-vectors-db")
    def init_vectors_db_command() -> None:
        """Create ``vectors.db`` or apply its initial migration when the file is new."""
        path = app.config.get("VECTORS_DATABASE_PATH")
        if not path:
            raise click.UsageError("VECTORS_DATABASE_PATH is not set.")
        ran = init_vectors_database(path)
        if ran:
            click.echo(f"Applied vectors migrations at {path}: {', '.join(ran)}")
        else:
            click.echo(f"No pending vectors migrations at {path}.")
