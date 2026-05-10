"""Apply pending migrations from ``app/db/sql/*.sql`` in filename order.

``PRAGMA foreign_keys = ON`` is set on the migration connection only; any future
app-level SQLite helper should run the same pragma on each new connection.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .migration_bookkeeping import (
    migration_bookkeeping_insert_sql,
    read_applied_migration_ids,
)

_SQL_DIR = Path(__file__).resolve().parent / "sql"


def migration_sql_files() -> list[tuple[str, Path]]:
    """Return ``(migration_id, path)`` pairs sorted by filename (e.g. ``001_…``, ``002_…``)."""
    paths = sorted(_SQL_DIR.glob("*.sql"), key=lambda p: p.name)
    return [(p.stem, p) for p in paths if p.is_file()]


MIGRATION_IDS: tuple[str, ...] = tuple(mid for mid, _ in migration_sql_files())


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Run missing SQL files and record rows in ``_migrations``. Returns stems applied this run.

    Each migration runs as **one** SQLite transaction: the file body and the bookkeeping
    ``INSERT`` are concatenated and passed to ``executescript()``, which uses a single
    implicit transaction for the whole script (so a failure rolls back DDL and insert).

    If any migration raises, that error is propagated and **no later files** in filename
    order are attempted. Already-completed migrations in this run stay committed.
    """
    conn.execute("PRAGMA foreign_keys = ON")
    applied = read_applied_migration_ids(conn)
    ran: list[str] = []
    for migration_id, sql_path in migration_sql_files():
        if migration_id in applied:
            continue
        body = sql_path.read_text(encoding="utf-8").rstrip()
        script = f"{body}\n{migration_bookkeeping_insert_sql(migration_id)}"
        try:
            conn.executescript(script)
        except sqlite3.Error:
            conn.rollback()
            raise  # abort entire run; do not apply later migration files
        applied.add(migration_id)
        ran.append(migration_id)
    return ran


# Backwards-compatible names for tests and callers that imported private helpers.
_migration_bookkeeping_sql = migration_bookkeeping_insert_sql
