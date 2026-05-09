"""SQLite implementation of ``WordsRepositoryPort``."""

from __future__ import annotations

import sqlite3
from typing import Any

from ..persistence.sqlite_db import SqlDatabase


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


class SqliteWordsRepository:
    """CRUD for the ``words`` table via ``SqlDatabase`` (one connection per operation)."""

    _SELECT = (
        "SELECT id, german_label, category, difficulty, translation, cefr_level, "
        "created_at, updated_at FROM words WHERE id = ?"
    )

    def __init__(self, db: SqlDatabase) -> None:
        self._db = db

    def list(self, *, category: str | None = None) -> list[dict[str, Any]]:
        with self._db.connection() as conn:
            if category is None:
                cur = conn.execute(
                    "SELECT id, german_label, category, difficulty, translation, cefr_level, "
                    "created_at, updated_at FROM words ORDER BY id",
                )
            else:
                cur = conn.execute(
                    "SELECT id, german_label, category, difficulty, translation, cefr_level, "
                    "created_at, updated_at FROM words WHERE category = ? ORDER BY id",
                    (category,),
                )
            return [_row_to_dict(r) for r in cur.fetchall()]

    def get(self, word_id: int) -> dict[str, Any] | None:
        with self._db.connection() as conn:
            cur = conn.execute(self._SELECT, (word_id,))
            row = cur.fetchone()
            return _row_to_dict(row) if row else None

    def create(
        self,
        *,
        german_label: str,
        category: str,
        difficulty: str,
        translation: str,
        cefr_level: str | None,
    ) -> dict[str, Any]:
        with self._db.connection() as conn:
            cur = conn.execute(
                "INSERT INTO words (german_label, category, difficulty, translation, cefr_level) "
                "VALUES (?, ?, ?, ?, ?)",
                (german_label, category, difficulty, translation, cefr_level),
            )
            wid = int(cur.lastrowid)
            cur2 = conn.execute(self._SELECT, (wid,))
            row = cur2.fetchone()
            assert row is not None
            return _row_to_dict(row)

    def update(self, word_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {"german_label", "category", "difficulty", "translation", "cefr_level"}
        subset = {k: v for k, v in fields.items() if k in allowed}
        with self._db.connection() as conn:
            if not subset:
                cur = conn.execute(self._SELECT, (word_id,))
                row = cur.fetchone()
                return _row_to_dict(row) if row else None
            columns = ", ".join(f"{name} = ?" for name in subset)
            values = list(subset.values())
            values.append(word_id)
            cur = conn.execute(f"UPDATE words SET {columns} WHERE id = ?", values)
            if cur.rowcount == 0:
                return None
            cur2 = conn.execute(self._SELECT, (word_id,))
            row = cur2.fetchone()
            assert row is not None
            return _row_to_dict(row)

    def delete(self, word_id: int) -> bool:
        with self._db.connection() as conn:
            cur = conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
            return cur.rowcount > 0
