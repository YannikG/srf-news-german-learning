"""Construct the default :class:`~app.news.service.NewsRefreshService` (OAuth + articles HTTP)."""

from __future__ import annotations

import httpx
from flask import Flask
from pydantic import ValidationError

from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from ..srg_articles import SrgArticlesApiClient, SrgArticlesApiSettings
from ..srg_oauth import build_srg_oauth_client
from .service import NewsRefreshError, NewsRefreshService


def build_default_news_refresh_service(app: Flask) -> NewsRefreshService:
    """Wire SQLite, shared ``httpx.Client``, OAuth token client, and articles API client."""
    db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(db, SqlDatabase):
        msg = (
            "sql_database extension missing or wrong type; "
            "ensure DATABASE_PATH is set in create_app."
        )
        raise RuntimeError(msg)

    shared_client = httpx.Client(timeout=30.0)
    try:
        oauth = build_srg_oauth_client(http_client=shared_client)
    except ValidationError as exc:
        raise NewsRefreshError(
            "SRG OAuth is not configured: set SRGSSR_CONSUMER_KEY and "
            "SRGSSR_CONSUMER_SECRET in the environment.",
            503,
            code="oauth_not_configured",
        ) from exc
    articles_settings = SrgArticlesApiSettings()
    articles = SrgArticlesApiClient(
        settings=articles_settings,
        http_client=shared_client,
    )
    return NewsRefreshService(db, oauth, articles)
