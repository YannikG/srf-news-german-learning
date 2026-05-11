"""Construct the default :class:`~app.news.service.NewsRefreshService` (upstream adapter + HTTP)."""

from __future__ import annotations

import httpx
from flask import Flask

from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from .constants import DEFAULT_REFRESH_ARTICLES_LIMIT
from .service import NewsRefreshService


def _require_sql_database(app: Flask) -> SqlDatabase:
    db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(db, SqlDatabase):
        msg = (
            "sql_database extension missing or wrong type; "
            "ensure DATABASE_PATH is set in create_app."
        )
        raise RuntimeError(msg)
    return db


def _build_srgssr_service(app: Flask, db: SqlDatabase) -> NewsRefreshService:
    from ..srg_articles import SrgArticlesApiClient, SrgArticlesApiSettings
    from ..srg_oauth import build_srg_oauth_client
    from .adapters import SrgSsrNewsUpstreamAdapter

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
    return NewsRefreshService(
        db,
        upstream,
        provider_slug=app.config["NEWS_ACTIVE_PROVIDER"],
        articles_limit=DEFAULT_REFRESH_ARTICLES_LIMIT,
    )


def _build_newsapi_service(app: Flask, db: SqlDatabase) -> NewsRefreshService:
    from ..newsapi import NewsApiClient, NewsApiSettings
    from .adapters import NewsApiUpstreamAdapter

    settings = NewsApiSettings()
    shared_client = httpx.Client(timeout=30.0)
    client = NewsApiClient(settings=settings, http_client=shared_client)
    upstream = NewsApiUpstreamAdapter(
        client,
        settings,
        news_provider=app.config["NEWS_ACTIVE_PROVIDER"],
    )
    return NewsRefreshService(
        db,
        upstream,
        provider_slug=app.config["NEWS_ACTIVE_PROVIDER"],
        articles_limit=min(settings.page_size, 100),
    )


def build_default_news_refresh_service(app: Flask) -> NewsRefreshService:
    """Wire SQLite + upstream adapter selected by ``NEWS_ACTIVE_PROVIDER``."""
    db = _require_sql_database(app)
    provider = app.config["NEWS_ACTIVE_PROVIDER"]

    if provider == "newsapi":
        return _build_newsapi_service(app, db)
    return _build_srgssr_service(app, db)
