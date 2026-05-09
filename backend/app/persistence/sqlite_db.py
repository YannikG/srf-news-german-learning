"""SQLAlchemy Core engine for SQLite (repository layer; no ORM)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Connection, Engine

# Key in ``Flask.extensions``; documented in ``backend/docs/architecture.md``.
SQL_DATABASE_EXTENSION_KEY = "sql_database"


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

        @event.listens_for(self._engine, "connect")
        def _enable_foreign_keys(
            dbapi_connection: object,
            _connection_record: object,
        ) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

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
