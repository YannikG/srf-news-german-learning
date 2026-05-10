"""Orchestrates SRG articles fetch, cooldown, and SQLite upserts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase
from ..srg_articles.client import SrgArticlesApiClient, SrgArticlesApiError
from ..srg_articles.mapping import map_article_to_app_db_fields
from ..srg_oauth.client import SrgOAuthClient, SrgOAuthClientError, SrgOAuthHttpError
from .constants import LAST_SUCCESSFUL_FETCH_METADATA_KEY, REFRESH_COOLDOWN_SECONDS


class NewsRefreshError(Exception):
    """Raised when refresh cannot complete; maps to an HTTP error response."""

    def __init__(self, message: str, status_code: int, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


_UPSERT_ARTICLE_SQL = """
INSERT INTO articles (
    external_id, publisher, provenance, title, lead, markdown_original,
    release_date, modification_date
) VALUES (
    :external_id, :publisher, :provenance, :title, :lead, :markdown_original,
    :release_date, :modification_date
)
ON CONFLICT(external_id) DO UPDATE SET
    publisher = excluded.publisher,
    provenance = excluded.provenance,
    title = excluded.title,
    lead = excluded.lead,
    markdown_original = excluded.markdown_original,
    release_date = excluded.release_date,
    modification_date = excluded.modification_date
"""

_METADATA_UPSERT_SQL = """
INSERT INTO srg_sync_metadata (key, value) VALUES (:key, :value)
ON CONFLICT(key) DO UPDATE SET
    value = excluded.value,
    updated_at = datetime('now')
"""


def _utc_now_iso(now: datetime) -> str:
    normalized = now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)
    return normalized.isoformat().replace("+00:00", "Z")


def _parse_utc_timestamp(raw: str) -> datetime:
    text_value = raw.strip()
    if text_value.endswith("Z"):
        text_value = text_value[:-1] + "+00:00"
    dt = datetime.fromisoformat(text_value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class NewsRefreshService:
    """Applies cooldown, calls SRG, upserts ``articles`` and sync metadata."""

    def __init__(
        self,
        db: SqlDatabase,
        oauth_client: SrgOAuthClient,
        articles_client: SrgArticlesApiClient,
        *,
        now_fn: Callable[[], datetime] | None = None,
        articles_limit: int = 10,
        publisher: str = "SRF",
    ) -> None:
        self._db = db
        self._oauth = oauth_client
        self._articles = articles_client
        self._now_fn = now_fn or (lambda: datetime.now(UTC))
        self._articles_limit = articles_limit
        self._publisher = publisher

    def refresh(self) -> dict[str, Any]:
        """Run one refresh attempt; returns a JSON-serializable result dict."""
        now = self._now_fn()
        now = now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)

        last_success = self._read_last_success_at()
        if last_success is not None:
            elapsed = (now - last_success).total_seconds()
            if elapsed < REFRESH_COOLDOWN_SECONDS:
                next_allowed = last_success + timedelta(seconds=REFRESH_COOLDOWN_SECONDS)
                return {
                    "fetched": False,
                    "articles_upserted": 0,
                    "next_allowed_fetch_at": _utc_now_iso(next_allowed),
                }

        try:
            token = self._oauth.get_access_token()
            page = self._articles.fetch_articles_page(
                token,
                publisher=self._publisher,
                limit=self._articles_limit,
            )
        except SrgOAuthHttpError as exc:
            code = "upstream_auth" if exc.status_code == 401 else "upstream_rate_limited"
            if exc.status_code == 401:
                raise NewsRefreshError(
                    "SRG OAuth rejected the client credentials (401).",
                    401,
                    code=code,
                ) from exc
            if exc.status_code == 429:
                raise NewsRefreshError(
                    "SRG OAuth rate limited token requests (429). Try again later.",
                    429,
                    code=code,
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
            raise NewsRefreshError(
                f"SRG articles request failed (HTTP {exc.status_code}).",
                502,
                code="upstream_error",
            ) from exc

        with self._db.begin() as conn:
            count = 0
            for record in page.results:
                fields = map_article_to_app_db_fields(record)
                conn.execute(text(_UPSERT_ARTICLE_SQL), dict(fields))
                count += 1
            conn.execute(
                text(_METADATA_UPSERT_SQL),
                {
                    "key": LAST_SUCCESSFUL_FETCH_METADATA_KEY,
                    "value": _utc_now_iso(now),
                },
            )

        next_allowed = now + timedelta(seconds=REFRESH_COOLDOWN_SECONDS)
        return {
            "fetched": True,
            "articles_upserted": count,
            "next_allowed_fetch_at": _utc_now_iso(next_allowed),
        }

    def _read_last_success_at(self) -> datetime | None:
        with self._db.begin() as conn:
            row = (
                conn.execute(
                    text("SELECT value FROM srg_sync_metadata WHERE key = :key"),
                    {"key": LAST_SUCCESSFUL_FETCH_METADATA_KEY},
                )
                .mappings()
                .first()
            )
        if row is None or not row.get("value"):
            return None
        raw = row["value"]
        if not isinstance(raw, str) or not raw.strip():
            return None
        return _parse_utc_timestamp(raw)
