"""SQLAlchemy SQLite engine for ``vectors.db`` (sqlite-vec loaded per connection when possible)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.engine import Connection, Engine

from ..vectors.extension import try_load_sqlite_vec
from .sqlite_engine import apply_foreign_keys_pragma, create_sqlite_engine

VECTORS_DATABASE_EXTENSION_KEY = "vectors_database"


def _on_vectors_sqlite_connect(dbapi_connection: sqlite3.Connection, _record: object) -> None:
    apply_foreign_keys_pragma(dbapi_connection)
    try_load_sqlite_vec(dbapi_connection)


class VectorsDatabase:
    """Path-scoped engine for ``vectors.db``.

    Each new DBAPI connection runs ``PRAGMA foreign_keys=ON`` and attempts
    ``sqlite-vec`` load so vec0 queries match the schema created at bootstrap.
    """

    def __init__(self, path: str | Path) -> None:
        self._path, self._engine = create_sqlite_engine(path, _on_vectors_sqlite_connect)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def begin(self) -> Iterator[Connection]:
        with self._engine.begin() as conn:
            yield conn

    def dispose(self) -> None:
        self._engine.dispose()
