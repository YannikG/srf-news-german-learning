"""SQLite app.db: Pfade, Migrationen, öffentliche Init-Hilfen."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .runner import MIGRATION_IDS, apply_migrations

__all__ = ["APP_DB_PATH", "MIGRATION_IDS", "init_database"]

# Fester Pfad zum Compose-Volume `/data`; Tests setzen DATABASE_PATH in der App-Config.
APP_DB_PATH = Path("/data/app.db")


def init_database(path: str | Path) -> list[str]:
    """Wendet ausstehende Migrationen an. Liste: Stems der jetzt ausgeführten SQL-Dateien."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        return apply_migrations(conn)
    finally:
        conn.close()
