"""SQLAlchemy Core engine for SQLite (repository layer; no ORM)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Connection, Engine

# Key in ``Flask.extensions``; documented in ``backend/docs/architecture.md``.
SQL_DATABASE_EXTENSION_KEY = "sql_database"


def _apply_sqlite_foreign_keys_pragma(dbapi_connection: sqlite3.Connection) -> None:
    """Run once per new DBAPI connection (SQLite only)."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _on_sqlite_engine_connect(dbapi_connection: sqlite3.Connection, _record: object) -> None:
    _apply_sqlite_foreign_keys_pragma(dbapi_connection)


class SqlDatabase:
    """Path-scoped SQLAlchemy ``Engine`` for ``app.db``.

    Repositories run each operation in ``engine.begin()`` so commits and rollbacks
    match the previous sqlite3 context-manager behavior. ``PRAGMA foreign_keys=ON``
    is applied on every new DBAPI connection.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser().resolve()
        url = URL.create(drivername="sqlite", database=str(self._path))
        self._engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
        )
        event.listen(self._engine, "connect", _on_sqlite_engine_connect)

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
