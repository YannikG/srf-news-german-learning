"""Tests for POST /api/news/refresh (cooldown, ingest, regressions)."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from freezegun import freeze_time
from sqlalchemy import text

from app import create_app
from app.news.factory import build_default_news_refresh_service
from app.news.routes import NEWS_REFRESH_SERVICE_CONFIG_KEY
from app.news.service import NewsRefreshService
from app.persistence import SQL_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase
from app.srg_articles import SrgArticlesApiClient
from app.srg_oauth import SrgOAuthClient

_FIXTURE_PAGE = Path(__file__).resolve().parent / "fixtures" / "srg_article_page.json"


def _load_article_page_json() -> dict:
    return json.loads(_FIXTURE_PAGE.read_text(encoding="utf-8"))


def _make_refresh_app(tmp_path_factory: pytest.TempPathFactory, handler) -> tuple:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
        },
    )
    db = application.extensions[SQL_DATABASE_EXTENSION_KEY]
    assert isinstance(db, SqlDatabase)
    shared = httpx.Client(transport=httpx.MockTransport(handler), timeout=30.0)
    oauth = SrgOAuthClient(
        "test-key",
        "test-secret",
        token_url="https://api.srgssr.ch/oauth/v1/accesstoken",
        user_agent="test-agent",
        http_client=shared,
    )
    articles = SrgArticlesApiClient(
        base_url="https://api.srgssr.ch/srgssr-articles/v2",
        user_agent="test-agent",
        http_client=shared,
    )
    service = NewsRefreshService(db, oauth, articles)
    application.config[NEWS_REFRESH_SERVICE_CONFIG_KEY] = service
    return application, db


def test_second_refresh_within_cooldown_skips_articles_http(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    page = _load_article_page_json()
    article_requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if request.method == "POST" and "accesstoken" in u:
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 300})
        if request.method == "GET" and "/articles" in u:
            article_requests.append(u)
            return httpx.Response(200, json=page)
        return httpx.Response(404, text=u)

    app, _db = _make_refresh_app(tmp_path_factory, handler)
    client = app.test_client()
    start = "2024-06-01T12:00:00+00:00"
    with freeze_time(start) as frozen:
        r1 = client.post("/api/news/refresh")
        assert r1.status_code == 200
        body1 = r1.get_json()
        assert body1["fetched"] is True
        assert body1["articles_upserted"] == 1
        assert len(article_requests) == 1

        frozen.tick(timedelta(seconds=60))
        r2 = client.post("/api/news/refresh")
        assert r2.status_code == 200
        body2 = r2.get_json()
        assert body2["fetched"] is False
        assert body2["articles_upserted"] == 0
        assert "next_allowed_fetch_at" in body2
        assert len(article_requests) == 1


def test_cooldown_allows_fetch_at_exactly_900_seconds(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    page = _load_article_page_json()
    article_requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if request.method == "POST" and "accesstoken" in u:
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 300})
        if request.method == "GET" and "/articles" in u:
            article_requests.append(u)
            return httpx.Response(200, json=page)
        return httpx.Response(404, text=u)

    app, _ = _make_refresh_app(tmp_path_factory, handler)
    client = app.test_client()
    with freeze_time("2024-06-10T08:00:00+00:00") as frozen:
        assert client.post("/api/news/refresh").status_code == 200
        assert len(article_requests) == 1
        frozen.tick(timedelta(seconds=899))
        assert client.post("/api/news/refresh").get_json()["fetched"] is False
        frozen.tick(timedelta(seconds=1))
        assert client.post("/api/news/refresh").get_json()["fetched"] is True
        assert len(article_requests) == 2


def test_get_articles_does_not_call_srg_http(tmp_path_factory: pytest.TempPathFactory) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if "accesstoken" in str(request.url):
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 300})
        if "/articles" in str(request.url):
            return httpx.Response(200, json=_load_article_page_json())
        return httpx.Response(404)

    app, _ = _make_refresh_app(tmp_path_factory, handler)
    client = app.test_client()
    calls.clear()
    r = client.get("/api/articles")
    assert r.status_code == 200
    assert calls == []


def test_duplicate_external_id_is_idempotent(tmp_path_factory: pytest.TempPathFactory) -> None:
    page = _load_article_page_json()

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if request.method == "POST" and "accesstoken" in u:
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 300})
        if request.method == "GET" and "/articles" in u:
            return httpx.Response(200, json=page)
        return httpx.Response(404)

    app, db = _make_refresh_app(tmp_path_factory, handler)
    client = app.test_client()
    with freeze_time("2024-07-01T10:00:00+00:00") as frozen:
        assert client.post("/api/news/refresh").status_code == 200
        frozen.tick(timedelta(seconds=900))
        assert client.post("/api/news/refresh").status_code == 200
    ext_id = page["results"][0]["id"]
    with db.begin() as conn:
        n = conn.execute(
            text("SELECT COUNT(*) AS c FROM articles WHERE external_id = :e"),
            {"e": ext_id},
        ).scalar_one()
    assert int(n) == 1


def test_oauth_401_is_user_friendly_json(tmp_path_factory: pytest.TempPathFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "accesstoken" in str(request.url):
            return httpx.Response(401, text="invalid_client")
        return httpx.Response(404)

    app, _ = _make_refresh_app(tmp_path_factory, handler)
    r = app.test_client().post("/api/news/refresh")
    assert r.status_code == 401
    data = r.get_json()
    assert "error" in data
    assert data.get("code") == "upstream_auth"


def test_articles_429_is_user_friendly_json(tmp_path_factory: pytest.TempPathFactory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if request.method == "POST" and "accesstoken" in u:
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 300})
        if "/articles" in u:
            return httpx.Response(429, text="slow down")
        return httpx.Response(404)

    app, _ = _make_refresh_app(tmp_path_factory, handler)
    r = app.test_client().post("/api/news/refresh")
    assert r.status_code == 429
    data = r.get_json()
    assert data.get("code") == "upstream_rate_limited"


def test_default_service_factory_builds(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SRGSSR_CONSUMER_KEY", "k")
    monkeypatch.setenv("SRGSSR_CONSUMER_SECRET", "s")
    db_path = tmp_path_factory.mktemp("db2") / "app.db"
    app = create_app({"TESTING": True, "DATABASE_PATH": str(db_path)})
    svc = build_default_news_refresh_service(app)
    assert isinstance(svc, NewsRefreshService)
