"""Persistence for article simplifications (P5-I03)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase


class SqliteArticleSimplifyRepository:
    """Writes ``article_simplifications`` and related junction rows."""

    def __init__(self, db: SqlDatabase) -> None:
        self._db = db

    def replace_simplification(
        self,
        *,
        article_id: int,
        cefr_level: str,
        markdown_simplified: str,
        used_word_ids: list[int],
        suggested_word_ids: list[int],
    ) -> int:
        """Upsert simplification row, replace junctions, link suggested words to the article."""
        with self._db.begin() as conn:
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

            return sid

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
