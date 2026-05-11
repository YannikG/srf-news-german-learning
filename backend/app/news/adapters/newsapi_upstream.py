"""NewsAPI.org adapter implementing ``NewsIngestUpstreamPort``."""

from __future__ import annotations

from typing import Any

from ...newsapi.client import NewsApiClient, NewsApiClientError
from ...newsapi.mapping import map_newsapi_article_to_app_db_fields
from ...newsapi.settings import NewsApiSettings
from ..errors import NewsRefreshError
from ..upstream_port import NewsIngestUpstreamPort, NormalizedArticlePage


class NewsApiUpstreamAdapter(NewsIngestUpstreamPort):
    """Maps NewsAPI.org list fetch to normalized SQLite upsert rows."""

    def __init__(
        self,
        client: NewsApiClient,
        settings: NewsApiSettings,
        *,
        news_provider: str,
    ) -> None:
        self._client = client
        self._settings = settings
        self._news_provider = news_provider

    def fetch_normalized_page(
        self,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> NormalizedArticlePage:
        page_number = int(cursor) if cursor else 1
        params = self._build_params(limit=limit, page=page_number)

        try:
            response = self._client.fetch_page(
                endpoint=self._settings.endpoint,
                params=params,
            )
        except NewsApiClientError as exc:
            if exc.status_code == 401:
                raise NewsRefreshError(
                    "NewsAPI rejected the API key (401).",
                    401,
                    code="upstream_auth",
                ) from exc
            if exc.status_code == 429:
                raise NewsRefreshError(
                    "NewsAPI rate limited the request (429). Try again later.",
                    429,
                    code="upstream_rate_limited",
                ) from exc
            detail = (exc.body or "").strip().replace("\r\n", " ").replace("\n", " ")
            if len(detail) > 400:
                detail = detail[:400] + "…"
            msg = f"NewsAPI request failed (HTTP {exc.status_code})"
            if detail:
                msg = f"{msg}: {detail}"
            raise NewsRefreshError(
                f"{msg}.",
                502,
                code="upstream_error",
            ) from exc

        language = self._settings.default_language or None
        slug = self._news_provider
        rows: list[dict[str, Any]] = []
        for article in response.articles:
            if not article.url:
                continue
            row = map_newsapi_article_to_app_db_fields(article, language=language)
            row["news_provider"] = slug
            rows.append(row)

        next_cursor: str | None = None
        page_size = limit
        if page_number * page_size < response.total_results:
            next_cursor = str(page_number + 1)

        return NormalizedArticlePage(rows=rows, next_cursor=next_cursor)

    def _build_params(self, *, limit: int, page: int) -> dict[str, str]:
        s = self._settings
        params: dict[str, str] = {
            "pageSize": str(min(limit, 100)),
            "page": str(page),
        }

        if s.endpoint == "everything":
            if s.default_query.strip():
                params["q"] = s.default_query.strip()
            if s.default_domains.strip():
                params["domains"] = s.default_domains.strip()
            if s.default_sources.strip():
                params["sources"] = s.default_sources.strip()
            if s.default_language.strip():
                params["language"] = s.default_language.strip()
            if s.default_sort_by.strip():
                params["sortBy"] = s.default_sort_by.strip()
        else:
            if s.default_country.strip():
                params["country"] = s.default_country.strip()
            if s.default_query.strip():
                params["q"] = s.default_query.strip()
            if s.default_sources.strip():
                params["sources"] = s.default_sources.strip()

        return params
