"""Tests for ``app.pons.client.PonsDictionaryClient``."""

from __future__ import annotations

import json

import httpx
import pytest

from app.pons.client import PonsDictionaryClient, PonsDictionaryError, PonsLookupResult

FAKE_SECRET = "test-secret-123"


def _mock_transport(status: int, body: object | None = None) -> httpx.MockTransport:
    content = json.dumps(body).encode() if body is not None else b""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Secret"] == FAKE_SECRET
        return httpx.Response(status, content=content)

    return httpx.MockTransport(handler)


class TestLookupSuccess:
    def test_returns_hits(self) -> None:
        hits_payload = [{"type": "entry", "roms": []}]
        transport = _mock_transport(200, hits_payload)
        http = httpx.Client(transport=transport)
        client = PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http)

        result = client.lookup("Haus", "deen")

        assert isinstance(result, PonsLookupResult)
        assert result.hits == hits_payload

    def test_sends_correct_params(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["q"] == "Küche"
            assert request.url.params["l"] == "deuk"
            return httpx.Response(200, content=b"[]")

        http = httpx.Client(transport=httpx.MockTransport(handler))
        client = PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http)
        result = client.lookup("Küche", "deuk")
        assert result.hits == []


class TestLookupNoContent:
    def test_204_returns_empty_hits(self) -> None:
        transport = _mock_transport(204)
        http = httpx.Client(transport=transport)
        client = PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http)

        result = client.lookup("xyznonexistent", "deen")

        assert result.hits == []


class TestLookupForbidden:
    def test_403_raises_error(self) -> None:
        transport = _mock_transport(403, {"msg": "Forbidden"})
        http = httpx.Client(transport=transport)
        client = PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http)

        with pytest.raises(PonsDictionaryError, match="secret invalid"):
            client.lookup("Haus", "deen")


class TestLookupRateLimit:
    def test_503_raises_error(self) -> None:
        transport = _mock_transport(503, {"msg": "limit"})
        http = httpx.Client(transport=transport)
        client = PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http)

        with pytest.raises(PonsDictionaryError, match="Tageslimit"):
            client.lookup("Haus", "deen")

    def test_503_status_code(self) -> None:
        transport = _mock_transport(503, {"msg": "limit"})
        http = httpx.Client(transport=transport)
        client = PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http)

        with pytest.raises(PonsDictionaryError) as exc_info:
            client.lookup("Haus", "deen")
        assert exc_info.value.status_code == 503


class TestLookupUnexpectedStatus:
    def test_500_raises_502(self) -> None:
        transport = _mock_transport(500, {"error": "internal"})
        http = httpx.Client(transport=transport)
        client = PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http)

        with pytest.raises(PonsDictionaryError) as exc_info:
            client.lookup("Haus", "deen")
        assert exc_info.value.status_code == 502


class TestContextManager:
    def test_enter_exit(self) -> None:
        transport = _mock_transport(204)
        http = httpx.Client(transport=transport)
        with PonsDictionaryClient(api_secret=FAKE_SECRET, http_client=http) as client:
            result = client.lookup("test", "deen")
        assert result.hits == []
