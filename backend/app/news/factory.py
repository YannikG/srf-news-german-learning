"""Construct the default :class:`~app.news.service.NewsRefreshService` (upstream adapter + HTTP)."""

from __future__ import annotations

import httpx
from flask import Flask

from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from ..srg_articles import SrgArticlesApiClient, SrgArticlesApiSettings
from ..srg_oauth import build_srg_oauth_client
from .adapters import SrgSsrNewsUpstreamAdapter
from .service import NewsRefreshService


def build_default_news_refresh_service(app: Flask) -> NewsRefreshService:
    """Wire SQLite, shared ``httpx.Client``, SRGSSR upstream adapter."""
    db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(db, SqlDatabase):
        msg = (
            "sql_database extension missing or wrong type; "
            "ensure DATABASE_PATH is set in create_app."
        )
        raise RuntimeError(msg)

    shared_client = httpx.Client(timeout=30.0)
    oauth = build_srg_oauth_client(http_client=shared_client)
    articles_settings = SrgArticlesApiSettings()
    articles = SrgArticlesApiClient(
        settings=articles_settings,
        http_client=shared_client,
    )
    upstream = SrgSsrNewsUpstreamAdapter(
        oauth,
        articles,
        news_provider=app.config["NEWS_ACTIVE_PROVIDER"],
    )
    return NewsRefreshService(db, upstream, articles_limit=10)
