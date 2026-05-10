"""SQLite implementation of ``WordsRepositoryPort`` via SQLAlchemy Core."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase
from .constants import QUERY_CEFR_NONE

_SELECT_COLUMNS = (
    "id, german_label, category, difficulty, translation, cefr_level, created_at, updated_at"
)


class SqliteWordsRepository:
    """CRUD for ``words`` using ``SqlDatabase.begin()`` (one transaction per operation)."""

    def __init__(self, db: SqlDatabase) -> None:
        self._db = db

    def count_words(self) -> int:
        with self._db.begin() as conn:
            row = conn.execute(text("SELECT COUNT(*) AS n FROM words")).mappings().one()
            return int(row["n"])

    def ids_in_lexicon(self, ids: Sequence[int]) -> set[int]:
        raw = [int(i) for i in ids]
        if not raw:
            return set()
        unique: list[int] = []
        seen: set[int] = set()
        for i in raw:
            if i not in seen:
                seen.add(i)
                unique.append(i)
        keys = [f"id_{j}" for j in range(len(unique))]
        placeholders = ", ".join(f":{k}" for k in keys)
        params = dict(zip(keys, unique, strict=True))
        stmt = text(f"SELECT id FROM words WHERE id IN ({placeholders})")
        with self._db.begin() as conn:
            rows = conn.execute(stmt, params).fetchall()
            return {int(r[0]) for r in rows}

    def list(
        self,
        *,
        category: str | None = None,
        cefr_level: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if category is not None:
            clauses.append("category = :category")
            params["category"] = category
        if cefr_level is not None:
            if cefr_level == QUERY_CEFR_NONE:
                clauses.append("cefr_level IS NULL")
            else:
                clauses.append("cefr_level = :cefr_level")
                params["cefr_level"] = cefr_level
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        stmt = text(f"SELECT {_SELECT_COLUMNS} FROM words{where} ORDER BY id")
        with self._db.begin() as conn:
            result = conn.execute(stmt, params) if params else conn.execute(stmt)
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
            upd = text(
                f"UPDATE words SET {set_clause} WHERE id = :word_id RETURNING {_SELECT_COLUMNS}",
            )
            row = conn.execute(upd, params).mappings().first()
            return dict(row) if row else None

    def delete(self, word_id: int) -> bool:
        with self._db.begin() as conn:
            result = conn.execute(text("DELETE FROM words WHERE id = :id"), {"id": word_id})
            return result.rowcount > 0
