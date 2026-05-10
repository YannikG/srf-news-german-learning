"""Bootstrap ``vectors.db`` with sqlite-vec (vec0) only."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ..db.migration_bookkeeping import migration_bookkeeping_insert_sql, read_applied_migration_ids
from ..db.migration_tx import execute_script_as_transaction
from .extension import try_load_sqlite_vec

_SQL_DIR = Path(__file__).resolve().parent / "sql"

VEC_MIGRATION_ID = "001_word_embeddings_vec0"
_LEGACY_NUMPY_MIGRATION_ID = "001_word_embeddings_numpy"


def init_vectors_database(path: str | Path) -> list[str]:
    """Create ``vectors.db`` when missing and apply the initial vec0 migration.

    Raises ``RuntimeError`` if sqlite-vec cannot be loaded (no application-level
    fallback). Returns migration stems applied in this call (empty if already
    initialized). The vec0 migration runs atomically via ``execute_script_as_transaction``.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        applied = read_applied_migration_ids(conn)
        if _LEGACY_NUMPY_MIGRATION_ID in applied:
            msg = (
                f"{p}: vectors database was created with a legacy non-vec schema; "
                "remove this file and restart so sqlite-vec can create a fresh vec0 schema."
            )
            raise RuntimeError(msg)
        if VEC_MIGRATION_ID in applied:
            return []

        if not try_load_sqlite_vec(conn):
            msg = (
                "sqlite-vec could not be loaded into SQLite (missing wheel, disabled "
                "extensions, or unsupported platform). Install the sqlite-vec package "
                "and use a Python build with loadable SQLite extensions (see backend "
                "Dockerfile)."
            )
            raise RuntimeError(msg)

        body = (_SQL_DIR / "001_word_embeddings_vec0.sql").read_text(encoding="utf-8").rstrip()
        script = f"{body}\n{migration_bookkeeping_insert_sql(VEC_MIGRATION_ID)}"
        execute_script_as_transaction(conn, script)
        return [VEC_MIGRATION_ID]
    finally:
        conn.close()
