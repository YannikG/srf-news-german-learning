"""Tests for POST /api/news/refresh (cooldown, ingest, regressions)."""

from __future__ import annotations

import copy
import json
from datetime import timedelta
from pathlib import Path

import httpx
import pytest
from freezegun import freeze_time
from sqlalchemy import text

from app import create_app
from app.news.adapters import SrgSsrNewsUpstreamAdapter
from app.news.constants import metadata_key_for_provider
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
            "NEWS_ACTIVE_PROVIDER": "srgssr",
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
    upstream = SrgSsrNewsUpstreamAdapter(oauth, articles, news_provider="srgssr")
    service = NewsRefreshService(db, upstream, provider_slug="srgssr")
    application.config[NEWS_REFRESH_SERVICE_CONFIG_KEY] = service
    return application, db


def test_corrupt_last_fetch_metadata_does_not_block_refresh(
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

    app, db = _make_refresh_app(tmp_path_factory, handler)
    with db.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO srg_sync_metadata (key, value) VALUES (:k, :v) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            ),
            {"k": metadata_key_for_provider("srgssr"), "v": "not-a-valid-timestamp"},
        )
    client = app.test_client()
    with freeze_time("2024-08-01T12:00:00+00:00"):
        r = client.post("/api/news/refresh")
    assert r.status_code == 200
    assert r.get_json()["fetched"] is True
    assert len(article_requests) == 1
    with db.begin() as conn:
        row = conn.execute(text("SELECT news_provider FROM articles LIMIT 1")).fetchone()
    assert row is not None
    assert row[0] == "srgssr"


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


def test_single_refresh_batch_upserts_two_distinct_articles(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    page = copy.deepcopy(_load_article_page_json())
    second = copy.deepcopy(page["results"][0])
    second["id"] = "urn:pdp:faro_srf:article:fixture-002"
    second["identifiers"] = [{"value": second["id"], "type": "PdpId"}]
    page["results"].append(second)

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if request.method == "POST" and "accesstoken" in u:
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 300})
        if request.method == "GET" and "/articles" in u:
            return httpx.Response(200, json=page)
        return httpx.Response(404, text=u)

    app, db = _make_refresh_app(tmp_path_factory, handler)
    r = app.test_client().post("/api/news/refresh")
    assert r.status_code == 200
    assert r.get_json()["articles_upserted"] == 2
    ids = (
        "srgssr:urn:pdp:faro_srf:article:fixture-001",
        "srgssr:urn:pdp:faro_srf:article:fixture-002",
    )
    with db.begin() as conn:
        n = conn.execute(
            text(
                "SELECT COUNT(*) AS c FROM articles WHERE external_id IN (:a, :b)",
            ),
            {"a": ids[0], "b": ids[1]},
        ).scalar_one()
    assert int(n) == 2


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
    ext_id = "srgssr:" + page["results"][0]["id"]
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


def test_refresh_without_oauth_env_returns_503_json(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SRGSSR_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("SRGSSR_CONSUMER_SECRET", raising=False)
    db_path = tmp_path_factory.mktemp("no_oauth_env") / "app.db"
    app = create_app(
        {"TESTING": True, "DATABASE_PATH": str(db_path), "NEWS_ACTIVE_PROVIDER": "srgssr"},
    )
    r = app.test_client().post("/api/news/refresh")
    assert r.status_code == 503
    data = r.get_json()
    assert isinstance(data, dict)
    assert data.get("code") == "oauth_not_configured"
    assert "error" in data


def test_refresh_newsapi_without_api_key_returns_503_json(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)
    db_path = tmp_path_factory.mktemp("no_newsapi_key") / "app.db"
    app = create_app(
        {"TESTING": True, "DATABASE_PATH": str(db_path), "NEWS_ACTIVE_PROVIDER": "newsapi"},
    )
    r = app.test_client().post("/api/news/refresh")
    assert r.status_code == 503
    data = r.get_json()
    assert isinstance(data, dict)
    assert data.get("code") == "newsapi_not_configured"
    assert "error" in data


def test_default_service_factory_builds(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SRGSSR_CONSUMER_KEY", "k")
    monkeypatch.setenv("SRGSSR_CONSUMER_SECRET", "s")
    db_path = tmp_path_factory.mktemp("db2") / "app.db"
    app = create_app(
        {"TESTING": True, "DATABASE_PATH": str(db_path), "NEWS_ACTIVE_PROVIDER": "srgssr"},
    )
    svc = build_default_news_refresh_service(app)
    assert isinstance(svc, NewsRefreshService)


# ---------------------------------------------------------------------------
# Per-provider cooldown (P8-I03)
# ---------------------------------------------------------------------------


class _FakeUpstream:
    """Minimal upstream port returning one deterministic article row."""

    def __init__(self, provider: str) -> None:
        self._provider = provider
        self.call_count = 0

    def fetch_normalized_page(self, *, limit: int, cursor: str | None = None):
        from app.news.upstream_port import NormalizedArticlePage

        self.call_count += 1
        return NormalizedArticlePage(
            rows=[
                {
                    "external_id": f"fake-id-{self.call_count}",
                    "publisher": "test",
                    "provenance": "https://example.com",
                    "title": "Test",
                    "lead": "Lead",
                    "markdown_original": "body",
                    "release_date": "2024-01-01",
                    "modification_date": "2024-01-01",
                    "news_provider": self._provider,
                    "language": None,
                }
            ],
            next_cursor=None,
        )


def test_cross_provider_cooldown_does_not_block_other_provider(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Refresh for provider A then immediately for B succeeds (separate cooldown keys)."""
    db_path = tmp_path_factory.mktemp("cross") / "app.db"
    app = create_app(
        {"TESTING": True, "DATABASE_PATH": str(db_path), "NEWS_ACTIVE_PROVIDER": "srgssr"},
    )
    db = app.extensions[SQL_DATABASE_EXTENSION_KEY]
    assert isinstance(db, SqlDatabase)

    upstream_a = _FakeUpstream("provider_a")
    upstream_b = _FakeUpstream("provider_b")

    svc_a = NewsRefreshService(db, upstream_a, provider_slug="provider_a")
    svc_b = NewsRefreshService(db, upstream_b, provider_slug="provider_b")

    with app.app_context(), freeze_time("2024-09-01T10:00:00+00:00") as frozen:
        result_a = svc_a.refresh()
        assert result_a["fetched"] is True
        assert upstream_a.call_count == 1

        frozen.tick(timedelta(seconds=60))

        result_b = svc_b.refresh()
        assert result_b["fetched"] is True
        assert upstream_b.call_count == 1

        result_a2 = svc_a.refresh()
        assert result_a2["fetched"] is False
        assert upstream_a.call_count == 1


def test_same_provider_cooldown_still_blocks(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Second refresh for the *same* provider within 900s is blocked."""
    db_path = tmp_path_factory.mktemp("same") / "app.db"
    app = create_app(
        {"TESTING": True, "DATABASE_PATH": str(db_path), "NEWS_ACTIVE_PROVIDER": "srgssr"},
    )
    db = app.extensions[SQL_DATABASE_EXTENSION_KEY]
    assert isinstance(db, SqlDatabase)

    upstream = _FakeUpstream("srgssr")
    svc = NewsRefreshService(db, upstream, provider_slug="srgssr")

    with app.app_context(), freeze_time("2024-09-01T10:00:00+00:00") as frozen:
        assert svc.refresh()["fetched"] is True
        assert upstream.call_count == 1

        frozen.tick(timedelta(seconds=60))
        assert svc.refresh()["fetched"] is False
        assert upstream.call_count == 1

        frozen.tick(timedelta(seconds=840))
        assert svc.refresh()["fetched"] is True
        assert upstream.call_count == 2
