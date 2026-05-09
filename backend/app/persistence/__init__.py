"""Shared SQLAlchemy SQLite engine for repositories (foreign keys on connect)."""

from __future__ import annotations

from .sqlite_db import SQL_DATABASE_EXTENSION_KEY, SqlDatabase

__all__ = ["SQL_DATABASE_EXTENSION_KEY", "SqlDatabase"]
