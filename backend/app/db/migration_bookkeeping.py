"""Shared SQLite ``_migrations`` bookkeeping for any SQL file bundle (app.db, vectors.db)."""

from __future__ import annotations

import re
import sqlite3

# Stems only; used to build a single-quoted SQL literal after validation.
MIGRATION_ID_STEM_PATTERN = re.compile(r"^[0-9]{3}_[a-zA-Z0-9_]+$")


def assert_migration_id_safe(migration_id: str) -> None:
    """Raise ``ValueError`` if ``migration_id`` is not a safe SQL stem."""
    if not MIGRATION_ID_STEM_PATTERN.fullmatch(migration_id):
        msg = f"migration_id must match {MIGRATION_ID_STEM_PATTERN.pattern}, got {migration_id!r}"
        raise ValueError(msg)


def migration_bookkeeping_insert_sql(migration_id: str) -> str:
    """Return the trailing ``INSERT INTO _migrations`` line for ``executescript`` bundles."""
    assert_migration_id_safe(migration_id)
    escaped = migration_id.replace("'", "''")
    return f"INSERT INTO _migrations (migration_id) VALUES ('{escaped}');\n"


def read_applied_migration_ids(conn: sqlite3.Connection) -> set[str]:
    """Return migration stems already recorded on ``conn`` (empty if no table yet)."""
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = '_migrations'",
    )
    if cur.fetchone() is None:
        return set()
    return {row[0] for row in conn.execute("SELECT migration_id FROM _migrations")}
