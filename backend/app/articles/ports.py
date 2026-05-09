"""Contracts between the articles service and persistence."""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol


class ArticlesRepositoryPort(Protocol):
    """Article reads; concrete implementation e.g. SQLite."""

    def list_for_day(
        self,
        *,
        filter_date: date,
        limit: int,
        after_id: int | None,
        search_query: str | None,
    ) -> list[dict[str, Any]]: ...

    def get(self, article_id: int) -> dict[str, Any] | None: ...
