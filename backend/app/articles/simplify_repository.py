"""Persistence for article simplifications (P5-I03)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase

_WORD_RETURNING = (
    "id, german_label, category, difficulty, translation, cefr_level, created_at, updated_at"
)


class SqliteArticleSimplifyRepository:
    """Writes ``article_simplifications`` and related junction rows."""

    def __init__(self, db: SqlDatabase) -> None:
        self._db = db

    def replace_simplification_with_new_words(
        self,
        *,
        article_id: int,
        cefr_level: str,
        markdown_simplified: str,
        used_word_ids: list[int],
        new_words: list[dict[str, str | None]],
    ) -> tuple[int, list[int]]:
        """Insert suggestion words, upsert simplification, junctions, in one transaction.

        Returns ``(simplification_id, new_word_ids)`` in insertion order for ``new_words``.
        """
        with self._db.begin() as conn:
            suggested_word_ids: list[int] = []
            for nw in new_words:
                wrow = (
                    conn.execute(
                        text(
                            "INSERT INTO words "
                            "(german_label, category, difficulty, translation, cefr_level) "
                            "VALUES (:german_label, :category, :difficulty, :translation, "
                            ":cefr_level) "
                            f"RETURNING {_WORD_RETURNING}",
                        ),
                        {
                            "german_label": nw["german_label"],
                            "category": nw["category"],
                            "difficulty": nw["difficulty"],
                            "translation": nw["translation"],
                            "cefr_level": nw["cefr_level"],
                        },
                    )
                    .mappings()
                    .one()
                )
                suggested_word_ids.append(int(wrow["id"]))

            row = (
                conn.execute(
                    text(
                        "INSERT INTO article_simplifications "
                        "(article_id, cefr_level, markdown_simplified) "
                        "VALUES (:article_id, :cefr, :md) "
                        "ON CONFLICT(article_id, cefr_level) DO UPDATE SET "
                        "markdown_simplified = excluded.markdown_simplified, "
                        "updated_at = datetime('now') "
                        "RETURNING id",
                    ),
                    {
                        "article_id": article_id,
                        "cefr": cefr_level,
                        "md": markdown_simplified,
                    },
                )
                .mappings()
                .one()
            )
            sid = int(row["id"])

            conn.execute(
                text(
                    "DELETE FROM article_simplification_used_words WHERE simplification_id = :sid",
                ),
                {"sid": sid},
            )
            conn.execute(
                text(
                    "DELETE FROM article_simplification_suggested_words "
                    "WHERE simplification_id = :sid",
                ),
                {"sid": sid},
            )

            for wid in used_word_ids:
                conn.execute(
                    text(
                        "INSERT INTO article_simplification_used_words "
                        "(simplification_id, word_id) VALUES (:sid, :wid)",
                    ),
                    {"sid": sid, "wid": wid},
                )

            for wid in suggested_word_ids:
                conn.execute(
                    text(
                        "INSERT INTO article_simplification_suggested_words "
                        "(simplification_id, word_id) VALUES (:sid, :wid)",
                    ),
                    {"sid": sid, "wid": wid},
                )
                conn.execute(
                    text(
                        "INSERT OR IGNORE INTO article_words (article_id, word_id) "
                        "VALUES (:aid, :wid)",
                    ),
                    {"aid": article_id, "wid": wid},
                )

            return sid, suggested_word_ids

    def get_simplification(
        self,
        *,
        article_id: int,
        cefr_level: str,
    ) -> dict[str, Any] | None:
        """Return simplification row or ``None``."""
        with self._db.begin() as conn:
            row = (
                conn.execute(
                    text(
                        "SELECT id, article_id, cefr_level, markdown_simplified, "
                        "created_at, updated_at FROM article_simplifications "
                        "WHERE article_id = :aid AND cefr_level = :cefr",
                    ),
                    {"aid": article_id, "cefr": cefr_level},
                )
                .mappings()
                .first()
            )
            return dict(row) if row else None
