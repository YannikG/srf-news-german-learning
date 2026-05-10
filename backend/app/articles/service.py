"""Validation and orchestration for read-only article APIs."""

from __future__ import annotations

import base64
import json
from datetime import UTC, date, datetime
from typing import Any

from .ports import ArticlesRepositoryPort


class ArticleServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def default_list_filter_date() -> date:
    """UTC calendar date used when ``GET /api/articles`` omits ``date``."""
    return datetime.now(UTC).date()


class ArticlesService:
    def __init__(self, repo: ArticlesRepositoryPort) -> None:
        self._repo = repo

    def list_articles(
        self,
        *,
        filter_date: date | None,
        limit: int,
        cursor_token: str | None,
        search_query: str | None,
    ) -> dict[str, Any]:
        day = filter_date if filter_date is not None else default_list_filter_date()
        after_id = _decode_cursor(cursor_token) if cursor_token else None
        rows = self._repo.list_for_day(
            filter_date=day,
            limit=limit,
            after_id=after_id,
            search_query=search_query,
        )
        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor: str | None = None
        if has_more and page:
            next_cursor = _encode_cursor(int(page[-1]["id"]))
        return {"items": page, "next_cursor": next_cursor}

    def get_article(self, article_id: int) -> dict[str, Any]:
        row = self._repo.get(article_id)
        if row is None:
            raise ArticleServiceError("Article not found", 404)
        return row


def _encode_cursor(after_id: int) -> str:
    payload = json.dumps({"after_id": after_id}, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(token: str) -> int:
    s = token.strip()
    if not s:
        raise ArticleServiceError("Invalid cursor", 400)
    pad = "=" * (-len(s) % 4)
    try:
        raw = base64.urlsafe_b64decode(s + pad)
        obj = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ArticleServiceError("Invalid cursor", 400) from exc
    if not isinstance(obj, dict):
        raise ArticleServiceError("Invalid cursor", 400)
    val = obj.get("after_id")
    if not isinstance(val, int) or isinstance(val, bool):
        raise ArticleServiceError("Invalid cursor", 400)
    return val
