"""Tests for NewsApiUpstreamAdapter (adapter level, no Flask)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.news.adapters import NewsApiUpstreamAdapter
from app.news.errors import NewsRefreshError
from app.newsapi.client import NewsApiClient
from app.newsapi.settings import NewsApiSettings

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "newsapi_everything_page.json"


def _load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _make_adapter(handler) -> NewsApiUpstreamAdapter:
    settings = NewsApiSettings(
        api_key="test-key",
        endpoint="everything",
        default_query="Schweiz",
        default_language="de",
    )
    client = NewsApiClient(
        settings=settings,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return NewsApiUpstreamAdapter(client, settings, news_provider="newsapi")


def test_fetch_normalized_page_success() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_load_fixture())

    adapter = _make_adapter(handler)
    page = adapter.fetch_normalized_page(limit=20)

    assert len(page.rows) == 2
    assert page.rows[0]["news_provider"] == "newsapi"
    assert page.rows[0]["title"] == "Schweizer Wirtschaft wächst überraschend stark"
    assert page.rows[0]["publisher"] == "Spiegel Online"
    assert page.rows[0]["language"] == "de"
    assert (
        page.rows[0]["external_id"] == "https://www.example.com/articles/schweizer-wirtschaft-2026"
    )
    assert page.next_cursor is None


def test_fetch_normalized_page_pagination() -> None:
    fixture = _load_fixture()
    fixture["totalResults"] = 50

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    adapter = _make_adapter(handler)
    page = adapter.fetch_normalized_page(limit=20)

    assert page.next_cursor == "2"


def test_fetch_with_cursor() -> None:
    seen_params: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_params.append(dict(request.url.params))
        return httpx.Response(200, json=_load_fixture())

    adapter = _make_adapter(handler)
    adapter.fetch_normalized_page(limit=10, cursor="3")

    assert seen_params[0]["page"] == "3"
    assert seen_params[0]["pageSize"] == "10"


def test_articles_without_url_skipped() -> None:
    fixture = _load_fixture()
    fixture["articles"][0]["url"] = None

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=fixture)

    adapter = _make_adapter(handler)
    page = adapter.fetch_normalized_page(limit=20)

    assert len(page.rows) == 1
    assert page.rows[0]["title"] == "Neues Klimagesetz tritt in Kraft"


def test_401_raises_upstream_auth() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    adapter = _make_adapter(handler)
    with pytest.raises(NewsRefreshError) as exc_info:
        adapter.fetch_normalized_page(limit=20)
    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "upstream_auth"


def test_429_raises_upstream_rate_limited() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Rate limited")

    adapter = _make_adapter(handler)
    with pytest.raises(NewsRefreshError) as exc_info:
        adapter.fetch_normalized_page(limit=20)
    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "upstream_rate_limited"


def test_500_raises_upstream_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    adapter = _make_adapter(handler)
    with pytest.raises(NewsRefreshError) as exc_info:
        adapter.fetch_normalized_page(limit=20)
    assert exc_info.value.status_code == 502
    assert exc_info.value.code == "upstream_error"


def test_everything_params_include_query_and_language() -> None:
    seen_params: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_params.append(dict(request.url.params))
        return httpx.Response(200, json=_load_fixture())

    adapter = _make_adapter(handler)
    adapter.fetch_normalized_page(limit=20)

    assert seen_params[0]["q"] == "Schweiz"
    assert seen_params[0]["language"] == "de"
    assert seen_params[0]["sortBy"] == "publishedAt"


def test_top_headlines_params_include_country() -> None:
    seen_params: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_params.append(dict(request.url.params))
        return httpx.Response(200, json=_load_fixture())

    settings = NewsApiSettings(
        api_key="test-key",
        endpoint="top-headlines",
        default_country="de",
    )
    client = NewsApiClient(
        settings=settings,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    adapter = NewsApiUpstreamAdapter(client, settings, news_provider="newsapi")
    adapter.fetch_normalized_page(limit=20)

    assert seen_params[0]["country"] == "de"
    assert "language" not in seen_params[0]
