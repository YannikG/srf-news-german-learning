"""Orchestrates upstream fetch via port, cooldown, and SQLite upserts."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text

from ..persistence.sqlite_db import SqlDatabase
from .constants import (
    DEFAULT_REFRESH_ARTICLES_LIMIT,
    REFRESH_COOLDOWN_SECONDS,
    metadata_key_for_provider,
)
from .errors import NewsRefreshError
from .external_id import namespace_external_id
from .upstream_port import NewsIngestUpstreamPort

__all__ = ["NewsRefreshError", "NewsRefreshService"]


_UPSERT_ARTICLE_SQL = """
INSERT INTO articles (
    external_id, publisher, provenance, title, lead, markdown_original,
    release_date, modification_date, news_provider
) VALUES (
    :external_id, :publisher, :provenance, :title, :lead, :markdown_original,
    :release_date, :modification_date, :news_provider
)
ON CONFLICT(external_id) DO UPDATE SET
    publisher = excluded.publisher,
    provenance = excluded.provenance,
    title = excluded.title,
    lead = excluded.lead,
    markdown_original = excluded.markdown_original,
    release_date = excluded.release_date,
    modification_date = excluded.modification_date,
    news_provider = excluded.news_provider
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
    """Applies cooldown, calls upstream port, upserts ``articles`` and sync metadata."""

    def __init__(
        self,
        db: SqlDatabase,
        upstream: NewsIngestUpstreamPort,
        *,
        provider_slug: str,
        now_fn: Callable[[], datetime] | None = None,
        articles_limit: int = DEFAULT_REFRESH_ARTICLES_LIMIT,
    ) -> None:
        self._db = db
        self._upstream = upstream
        self._metadata_key = metadata_key_for_provider(provider_slug)
        self._now_fn = now_fn or (lambda: datetime.now(UTC))
        self._articles_limit = articles_limit

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

        page = self._upstream.fetch_normalized_page(limit=self._articles_limit, cursor=None)
        mappings = page.rows
        for row in mappings:
            row["external_id"] = namespace_external_id(row["news_provider"], row["external_id"])
        with self._db.begin() as conn:
            if mappings:
                conn.execute(text(_UPSERT_ARTICLE_SQL), mappings)
            conn.execute(
                text(_METADATA_UPSERT_SQL),
                {
                    "key": self._metadata_key,
                    "value": _utc_now_iso(now),
                },
            )

        next_allowed = now + timedelta(seconds=REFRESH_COOLDOWN_SECONDS)
        return {
            "fetched": True,
            "articles_upserted": len(mappings),
            "next_allowed_fetch_at": _utc_now_iso(next_allowed),
        }

    def _read_last_success_at(self) -> datetime | None:
        with self._db.begin() as conn:
            row = (
                conn.execute(
                    text("SELECT value FROM srg_sync_metadata WHERE key = :key"),
                    {"key": self._metadata_key},
                )
                .mappings()
                .first()
            )
        if row is None or not row.get("value"):
            return None
        raw = row["value"]
        if not isinstance(raw, str) or not raw.strip():
            return None
        try:
            return _parse_utc_timestamp(raw)
        except ValueError:
            # Corrupt or legacy timestamp: behave like no prior successful fetch.
            return None
