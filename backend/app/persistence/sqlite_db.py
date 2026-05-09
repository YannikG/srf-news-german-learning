"""Konfigurierte SQLite-Verbindungen für das Repository-Pattern."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Schlüssel in ``Flask.extensions``; identisch in Architektur-Doku.
SQL_DATABASE_EXTENSION_KEY = "sql_database"


class SqlDatabase:
    """Pfad-bewusster Zugang zu ``app.db``; Repositories nutzen kurze Transaktionen.

    Der Contextmanager committet nach erfolgreichem ``yield``, rollt bei Exceptions zurück,
    und schliesst die Connection (SQLite verwirft sonst uncommittete Schreibvorgänge).
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
