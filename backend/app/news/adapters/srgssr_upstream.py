"""SRGSSR OAuth and Articles API adapter implementing ``NewsIngestUpstreamPort``."""

from __future__ import annotations

from typing import Any

from ...srg_articles.client import SrgArticlesApiClient, SrgArticlesApiError
from ...srg_articles.mapping import map_article_to_app_db_fields
from ...srg_oauth.client import SrgOAuthClient, SrgOAuthClientError, SrgOAuthHttpError
from ..errors import NewsRefreshError
from ..upstream_port import NewsIngestUpstreamPort, NormalizedArticlePage


class SrgSsrNewsUpstreamAdapter(NewsIngestUpstreamPort):
    """Maps SRGSSR list fetch to normalized SQLite upsert rows."""

    def __init__(
        self,
        oauth_client: SrgOAuthClient,
        articles_client: SrgArticlesApiClient,
        *,
        news_provider: str,
        publisher: str = "SRF",
    ) -> None:
        self._oauth = oauth_client
        self._articles = articles_client
        self._news_provider = news_provider
        self._publisher = publisher

    def fetch_normalized_page(
        self,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> NormalizedArticlePage:
        try:
            token = self._oauth.get_access_token()
            page = self._articles.fetch_articles_page(
                token,
                publisher=self._publisher,
                limit=limit,
                cursor=cursor,
            )
        except SrgOAuthHttpError as exc:
            if exc.status_code == 401:
                raise NewsRefreshError(
                    "SRG OAuth rejected the client credentials (401).",
                    401,
                    code="upstream_auth",
                ) from exc
            if exc.status_code == 429:
                raise NewsRefreshError(
                    "SRG OAuth rate limited token requests (429). Try again later.",
                    429,
                    code="upstream_rate_limited",
                ) from exc
            detail = (exc.body or "").strip().replace("\r\n", " ").replace("\n", " ")
            if len(detail) > 400:
                detail = detail[:400] + "…"
            if detail:
                raise NewsRefreshError(
                    f"SRG OAuth token request failed (HTTP {exc.status_code}): {detail}",
                    502,
                    code="upstream_error",
                ) from exc
            raise NewsRefreshError(
                f"SRG OAuth token request failed (HTTP {exc.status_code}).",
                502,
                code="upstream_error",
            ) from exc
        except SrgOAuthClientError as exc:
            raise NewsRefreshError(
                "SRG OAuth client error while fetching a token.",
                502,
                code="upstream_error",
            ) from exc
        except SrgArticlesApiError as exc:
            if exc.status_code == 401:
                raise NewsRefreshError(
                    "SRG articles API rejected the bearer token (401).",
                    401,
                    code="upstream_auth",
                ) from exc
            if exc.status_code == 429:
                raise NewsRefreshError(
                    "SRG articles API rate limited the request (429). Try again later.",
                    429,
                    code="upstream_rate_limited",
                ) from exc
            detail = (exc.body or "").strip().replace("\r\n", " ").replace("\n", " ")
            if len(detail) > 400:
                detail = detail[:400] + "…"
            if detail:
                raise NewsRefreshError(
                    f"SRG articles request failed (HTTP {exc.status_code}): {detail}",
                    502,
                    code="upstream_error",
                ) from exc
            raise NewsRefreshError(
                f"SRG articles request failed (HTTP {exc.status_code}).",
                502,
                code="upstream_error",
            ) from exc

        slug = self._news_provider
        rows: list[dict[str, Any]] = []
        for record in page.results:
            row = map_article_to_app_db_fields(record)
            row["news_provider"] = slug
            rows.append(row)
        return NormalizedArticlePage(rows=rows, next_cursor=page.cursor)
