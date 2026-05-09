"""SQLite repository for ``settings`` (single row, ``id = 1``)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase

_SELECT_COLUMNS = "id, default_cefr, translation_language, retrieval_top_k"


class SqliteSettingsRepository:
    """Read/update ``settings`` via ``SqlDatabase.begin()``."""

    def __init__(self, db: SqlDatabase) -> None:
        self._db = db

    def get_row(self) -> dict[str, Any] | None:
        with self._db.begin() as conn:
            stmt = text(f"SELECT {_SELECT_COLUMNS} FROM settings WHERE id = 1")
            row = conn.execute(stmt).mappings().first()
            return dict(row) if row else None

    def update_row(self, fields: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {"default_cefr", "translation_language", "retrieval_top_k"}
        subset = {k: v for k, v in fields.items() if k in allowed}
        with self._db.begin() as conn:
            if not subset:
                stmt = text(f"SELECT {_SELECT_COLUMNS} FROM settings WHERE id = 1")
                row = conn.execute(stmt).mappings().first()
                return dict(row) if row else None
            set_clause = ", ".join(f"{name} = :{name}" for name in subset)
            params: dict[str, Any] = {**subset, "sid": 1}
            stmt = text(
                f"UPDATE settings SET {set_clause} WHERE id = :sid RETURNING {_SELECT_COLUMNS}",
            )
            row = conn.execute(stmt, params).mappings().first()
            return dict(row) if row else None
