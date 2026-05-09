"""Configured SQLite connections for the repository layer."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Key in ``Flask.extensions``; documented in ``backend/docs/architecture.md``.
SQL_DATABASE_EXTENSION_KEY = "sql_database"


class SqlDatabase:
    """Path-scoped access to ``app.db``; repositories use short per-operation transactions.

    The context manager commits after a successful ``yield``, rolls back on exceptions,
    then closes the connection (SQLite drops uncommitted writes on close otherwise).
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()
