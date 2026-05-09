"""SQLite implementation of ``WordsRepositoryPort`` via SQLAlchemy Core."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase

_SELECT_COLUMNS = (
    "id, german_label, category, difficulty, translation, cefr_level, created_at, updated_at"
)


class SqliteWordsRepository:
    """CRUD for ``words`` using ``SqlDatabase.engine`` (one transaction per operation)."""

    def __init__(self, db: SqlDatabase) -> None:
        self._db = db

    def list(self, *, category: str | None = None) -> list[dict[str, Any]]:
        with self._db.begin() as conn:
            if category is None:
                stmt = text(f"SELECT {_SELECT_COLUMNS} FROM words ORDER BY id")
                result = conn.execute(stmt)
            else:
                stmt = text(
                    f"SELECT {_SELECT_COLUMNS} FROM words WHERE category = :category ORDER BY id",
                )
                result = conn.execute(stmt, {"category": category})
            return [dict(row) for row in result.mappings().all()]

    def get(self, word_id: int) -> dict[str, Any] | None:
        with self._db.begin() as conn:
            stmt = text(f"SELECT {_SELECT_COLUMNS} FROM words WHERE id = :id")
            row = conn.execute(stmt, {"id": word_id}).mappings().first()
            return dict(row) if row else None

    def create(
        self,
        *,
        german_label: str,
        category: str,
        difficulty: str,
        translation: str,
        cefr_level: str | None,
    ) -> dict[str, Any]:
        with self._db.begin() as conn:
            stmt = text(
                "INSERT INTO words (german_label, category, difficulty, translation, cefr_level) "
                "VALUES (:german_label, :category, :difficulty, :translation, :cefr_level) "
                f"RETURNING {_SELECT_COLUMNS}",
            )
            row = (
                conn.execute(
                    stmt,
                    {
                        "german_label": german_label,
                        "category": category,
                        "difficulty": difficulty,
                        "translation": translation,
                        "cefr_level": cefr_level,
                    },
                )
                .mappings()
                .one()
            )
            return dict(row)

    def update(self, word_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {"german_label", "category", "difficulty", "translation", "cefr_level"}
        subset = {k: v for k, v in fields.items() if k in allowed}
        with self._db.begin() as conn:
            if not subset:
                stmt = text(f"SELECT {_SELECT_COLUMNS} FROM words WHERE id = :id")
                row = conn.execute(stmt, {"id": word_id}).mappings().first()
                return dict(row) if row else None
            set_clause = ", ".join(f"{name} = :{name}" for name in subset)
            params: dict[str, Any] = {**subset, "word_id": word_id}
            upd = text(f"UPDATE words SET {set_clause} WHERE id = :word_id")
            result = conn.execute(upd, params)
            if result.rowcount == 0:
                return None
            stmt = text(f"SELECT {_SELECT_COLUMNS} FROM words WHERE id = :id")
            row = conn.execute(stmt, {"id": word_id}).mappings().one()
            return dict(row)

    def delete(self, word_id: int) -> bool:
        with self._db.begin() as conn:
            result = conn.execute(text("DELETE FROM words WHERE id = :id"), {"id": word_id})
            return result.rowcount > 0
