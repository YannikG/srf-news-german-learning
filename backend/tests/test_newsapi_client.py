"""Tests for NewsApiClient (httpx mock transport, no network)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from app.newsapi.client import NewsApiClient, NewsApiClientError

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "newsapi_everything_page.json"


def _load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_successful_page_parse() -> None:
    payload = _load_fixture()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Api-Key"] == "test-key"
        assert "apiKey" not in str(request.url)
        return httpx.Response(200, json=payload)

    client = NewsApiClient(
        api_key="test-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    response = client.fetch_page(endpoint="everything", params={"q": "Schweiz"})
    assert response.status == "ok"
    assert response.total_results == 2
    assert len(response.articles) == 2
    assert response.articles[0].title == "Schweizer Wirtschaft wächst überraschend stark"
    assert response.articles[0].source.name == "Spiegel Online"
    assert response.articles[1].published_at == "2026-05-09T14:15:00Z"


def test_api_key_in_header_not_query() -> None:
    """Auth via X-Api-Key header, not apiKey query string."""
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        return httpx.Response(200, json=_load_fixture())

    client = NewsApiClient(
        api_key="secret-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    client.fetch_page(endpoint="everything", params={"q": "test"})
    req = seen_requests[0]
    assert req.headers["X-Api-Key"] == "secret-key"
    assert "apiKey" not in str(req.url)
    assert "secret-key" not in str(req.url)


def test_401_raises_client_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    client = NewsApiClient(
        api_key="bad-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(NewsApiClientError) as exc_info:
        client.fetch_page(endpoint="everything", params={"q": "test"})
    assert exc_info.value.status_code == 401
    assert "401" in str(exc_info.value)


def test_429_raises_client_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Rate limited")

    client = NewsApiClient(
        api_key="test-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(NewsApiClientError) as exc_info:
        client.fetch_page(endpoint="everything", params={"q": "test"})
    assert exc_info.value.status_code == 429


def test_500_raises_client_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client = NewsApiClient(
        api_key="test-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(NewsApiClientError) as exc_info:
        client.fetch_page(endpoint="everything", params={"q": "test"})
    assert exc_info.value.status_code == 500


def test_invalid_json_raises_client_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json {{{")

    client = NewsApiClient(
        api_key="test-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(NewsApiClientError, match="not valid JSON"):
        client.fetch_page(endpoint="everything", params={"q": "test"})


def test_context_manager() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_load_fixture())

    with NewsApiClient(
        api_key="test-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    ) as client:
        resp = client.fetch_page(endpoint="everything", params={"q": "test"})
        assert resp.status == "ok"


def test_network_error_raises_502() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    client = NewsApiClient(
        api_key="test-key",
        base_url="https://newsapi.org",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(NewsApiClientError) as exc_info:
        client.fetch_page(endpoint="everything", params={"q": "test"})
    assert exc_info.value.status_code == 502
