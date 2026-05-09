"""Gemeinsame DB-Anbindung für Repositories (SQLite, Foreign Keys, Row-Fabrik)."""

from __future__ import annotations

from .sqlite_db import SQL_DATABASE_EXTENSION_KEY, SqlDatabase

__all__ = ["SQL_DATABASE_EXTENSION_KEY", "SqlDatabase"]
