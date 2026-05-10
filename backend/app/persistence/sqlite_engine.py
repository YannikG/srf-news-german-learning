"""Shared SQLAlchemy SQLite engine setup (used by ``app.db`` and ``vectors.db`` pools)."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, Engine

ConnectListener = Callable[[sqlite3.Connection, object], None]


def apply_foreign_keys_pragma(dbapi_connection: sqlite3.Connection) -> None:
    """Run ``PRAGMA foreign_keys=ON`` on a new SQLite DBAPI connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_sqlite_engine(
    path: str | Path,
    *connect_listeners: ConnectListener,
) -> tuple[Path, Engine]:
    """Resolve ``path``, build an engine, register ``connect`` listeners, return path and engine."""
    resolved = Path(path).expanduser().resolve()
    url = URL.create(drivername="sqlite", database=str(resolved))
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
    )
    for listener in connect_listeners:
        event.listen(engine, "connect", listener)
    return resolved, engine
