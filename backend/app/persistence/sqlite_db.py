"""SQLAlchemy Core engine for SQLite (repository layer; no ORM)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.engine import Connection, Engine

from .sqlite_engine import apply_foreign_keys_pragma, create_sqlite_engine

# Key in ``Flask.extensions``; documented in ``backend/docs/architecture.md``.
SQL_DATABASE_EXTENSION_KEY = "sql_database"


def _on_sqlite_engine_connect(dbapi_connection: sqlite3.Connection, _record: object) -> None:
    apply_foreign_keys_pragma(dbapi_connection)


class SqlDatabase:
    """Path-scoped SQLAlchemy ``Engine`` for ``app.db``.

    Repositories run each operation in ``engine.begin()`` so commits and rollbacks
    match the previous sqlite3 context-manager behavior. ``PRAGMA foreign_keys=ON``
    is applied on every new DBAPI connection.
    """

    def __init__(self, path: str | Path) -> None:
        self._path, self._engine = create_sqlite_engine(path, _on_sqlite_engine_connect)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def begin(self) -> Iterator[Connection]:
        """One transaction scope; commits on success, rolls back on exception."""
        with self._engine.begin() as conn:
            yield conn

    def dispose(self) -> None:
        """Release pool resources (e.g. teardown in tests or worker shutdown)."""
        self._engine.dispose()
