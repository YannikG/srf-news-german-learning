"""SQLite implementation of ``ArticlesRepositoryPort`` (list + detail, FTS5 title)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase

_LIST_COLUMNS = (
    "id, external_id, publisher, provenance, title, lead, release_date, "
    "modification_date, cefr_level, created_at, updated_at"
)

_LIST_COLUMNS_QUALIFIED = (
    "a.id, a.external_id, a.publisher, a.provenance, a.title, a.lead, a.release_date, "
    "a.modification_date, a.cefr_level, a.created_at, a.updated_at"
)

_DETAIL_COLUMNS = _LIST_COLUMNS + ", markdown_original"

# Letters, digits, and common Latin-1 / Latin Extended-A letters (incl. German umlauts).
_TOKEN_RE = re.compile(r"[0-9A-Za-z\u00C0-\u024F]+", re.UNICODE)


def _fts_prefix_match_expression(user_query: str) -> str | None:
    """Build an FTS5 ``MATCH`` expression: each token is mandatory-prefix (``tok*``)."""
    tokens = _TOKEN_RE.findall(user_query)
    if not tokens:
        return None
    parts: list[str] = []
    for raw in tokens:
        escaped = raw.replace('"', '""')
        parts.append(f'"{escaped}"*')
    return " AND ".join(parts)


class SqliteArticlesRepository:
    """Read-only article queries using ``articles`` and ``articles_fts``."""

    def __init__(self, db: SqlDatabase) -> None:
        self._db = db

    def list_for_day(
        self,
        *,
        filter_date: date,
        limit: int,
        after_id: int | None,
        search_query: str | None,
    ) -> list[dict[str, Any]]:
        day = filter_date.isoformat()
        fts_expr: str | None = None
        if search_query:
            fts_expr = _fts_prefix_match_expression(search_query)
            if fts_expr is None:
                return []
        fetch = limit + 1
        with self._db.begin() as conn:
            if fts_expr is None:
                stmt = text(
                    f"SELECT {_LIST_COLUMNS} FROM articles "
                    "WHERE release_date >= :day AND release_date < date(:day, '+1 day') "
                    "AND (:after_id IS NULL OR id < :after_id) "
                    "ORDER BY id DESC "
                    "LIMIT :lim",
                )
                result = conn.execute(
                    stmt,
                    {"day": day, "after_id": after_id, "lim": fetch},
                )
            else:
                stmt = text(
                    f"SELECT {_LIST_COLUMNS_QUALIFIED} FROM articles AS a "
                    "INNER JOIN articles_fts ON articles_fts.rowid = a.id "
                    "WHERE a.release_date >= :day AND a.release_date < date(:day, '+1 day') "
                    "AND (:after_id IS NULL OR a.id < :after_id) "
                    "AND articles_fts MATCH :fts "
                    "ORDER BY a.id DESC "
                    "LIMIT :lim",
                )
                result = conn.execute(
                    stmt,
                    {"day": day, "after_id": after_id, "fts": fts_expr, "lim": fetch},
                )
            return [dict(row) for row in result.mappings().all()]

    def get(self, article_id: int) -> dict[str, Any] | None:
        with self._db.begin() as conn:
            stmt = text(f"SELECT {_DETAIL_COLUMNS} FROM articles WHERE id = :id")
            row = conn.execute(stmt, {"id": article_id}).mappings().first()
            return dict(row) if row else None
