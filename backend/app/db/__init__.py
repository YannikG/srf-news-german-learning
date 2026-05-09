"""SQLite app.db path, migrations, and public init helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .runner import MIGRATION_IDS, apply_migrations

__all__ = ["APP_DB_PATH", "MIGRATION_IDS", "init_database"]

# Default path for Compose volume mount at `/data`; tests override DATABASE_PATH in config.
APP_DB_PATH = Path("/data/app.db")


def init_database(path: str | Path) -> list[str]:
    """Apply pending migrations. Returns stems of SQL files executed in this call."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        return apply_migrations(conn)
    finally:
        conn.close()
