"""Wendet ausstehende Migrationen aus ``app/db/sql/*.sql`` in Namensreihenfolge an."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SQL_DIR = Path(__file__).resolve().parent / "sql"


def migration_sql_files() -> list[tuple[str, Path]]:
    """Liefert ``(migration_id, path)`` sortiert nach Dateiname (z. B. ``001_…``, ``002_…``)."""
    paths = sorted(_SQL_DIR.glob("*.sql"), key=lambda p: p.name)
    return [(p.stem, p) for p in paths if p.is_file()]


MIGRATION_IDS: tuple[str, ...] = tuple(mid for mid, _ in migration_sql_files())


def _applied_migration_ids(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = '_migrations'",
    )
    if cur.fetchone() is None:
        return set()
    return {row[0] for row in conn.execute("SELECT migration_id FROM _migrations")}


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Führt fehlende SQL-Dateien aus, bucht in ``_migrations``. Rückgabe: Stems dieser Runde."""
    conn.execute("PRAGMA foreign_keys = ON")
    applied = _applied_migration_ids(conn)
    ran: list[str] = []
    for migration_id, sql_path in migration_sql_files():
        if migration_id in applied:
            continue
        sql = sql_path.read_text(encoding="utf-8")
        with conn:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _migrations (migration_id) VALUES (?)",
                (migration_id,),
            )
        applied.add(migration_id)
        ran.append(migration_id)
    return ran
