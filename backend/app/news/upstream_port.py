"""Port for fetching one page of articles from an upstream news provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class NormalizedArticlePage:
    """One page of rows ready for ``articles`` upsert (including ``news_provider``)."""

    rows: list[dict[str, Any]]
    next_cursor: str | None


class NewsIngestUpstreamPort(Protocol):
    """Fetches normalized article rows for a single list page."""

    def fetch_normalized_page(
        self,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> NormalizedArticlePage:
        """Return upsert-ready rows; may raise :class:`~app.news.errors.NewsRefreshError`."""
        ...
