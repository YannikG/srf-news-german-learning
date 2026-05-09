"""SRG OAuth client: mocked HTTP only (no real network)."""

from __future__ import annotations

import base64

import httpx
import pytest

from app.srg_oauth.client import (
    TOKEN_URL,
    USER_AGENT,
    SrgOAuthClient,
    SrgOAuthClientError,
    SrgOAuthHttpError,
    SrgOAuthTokenResponseError,
)
from app.srg_oauth.factory import build_srg_oauth_client
from app.srg_oauth.settings import SrgSsrOAuthSettings


def _basic_header(key: str, secret: str) -> str:
    raw = base64.b64encode(f"{key}:{secret}".encode()).decode("ascii")
    return f"Basic {raw}"


def test_token_success_sets_user_agent_basic_auth_form_body_and_caches() -> None:
    http_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal http_calls
        http_calls += 1
        assert str(request.url) == TOKEN_URL
        assert request.method == "POST"
        assert request.headers.get("user-agent") == USER_AGENT
        assert request.headers.get("authorization") == _basic_header("ck", "cs")
        ct = request.headers.get("content-type", "")
        assert "application/x-www-form-urlencoded" in ct
        body = request.content.decode()
        assert "grant_type=client_credentials" in body
        if http_calls == 1:
            return httpx.Response(
                200,
                json={"access_token": "tok-1", "expires_in": 600, "token_type": "Bearer"},
            )
        return httpx.Response(
            200,
            json={"access_token": "tok-2", "expires_in": 600, "token_type": "Bearer"},
        )

    transport = httpx.MockTransport(handler)
    clock = {"t": 0.0}

    def mono() -> float:
        return clock["t"]

    client = httpx.Client(transport=transport)
    try:
        oauth = SrgOAuthClient(
            "ck",
            "cs",
            http_client=client,
            refresh_skew_seconds=60,
            monotonic=mono,
        )
        assert oauth.get_access_token() == "tok-1"
        assert oauth.get_access_token() == "tok-1"
        assert http_calls == 1
        clock["t"] = 539.0
        assert oauth.get_access_token() == "tok-1"
        assert http_calls == 1
        clock["t"] = 541.0
        assert oauth.get_access_token() == "tok-2"
        assert http_calls == 2
    finally:
        client.close()


def test_token_401_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        oauth = SrgOAuthClient("k", "s", http_client=client)
        with pytest.raises(SrgOAuthHttpError) as exc:
            oauth.get_access_token()
        assert exc.value.status_code == 401
        assert "invalid_client" in exc.value.body
    finally:
        client.close()


def test_token_429_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="slow down")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        oauth = SrgOAuthClient("k", "s", http_client=client)
        with pytest.raises(SrgOAuthHttpError) as exc:
            oauth.get_access_token()
        assert exc.value.status_code == 429
        assert "slow down" in exc.value.body
    finally:
        client.close()


def test_token_request_error_wraps_as_client_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated network failure", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        oauth = SrgOAuthClient("k", "s", http_client=client)
        with pytest.raises(SrgOAuthClientError) as exc:
            oauth.get_access_token()
        assert "SRG OAuth token request failed" in str(exc.value)
        assert exc.value.__cause__ is not None
    finally:
        client.close()


def test_token_missing_access_token_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"expires_in": 10})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        oauth = SrgOAuthClient("k", "s", http_client=client)
        with pytest.raises(SrgOAuthTokenResponseError):
            oauth.get_access_token()
    finally:
        client.close()


def test_token_json_not_object_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not-an-object"])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        oauth = SrgOAuthClient("k", "s", http_client=client)
        with pytest.raises(SrgOAuthTokenResponseError) as exc:
            oauth.get_access_token()
        assert "object" in str(exc.value).lower()
    finally:
        client.close()


def test_settings_reads_consumer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SRGSSR_CONSUMER_KEY", "env-key")
    monkeypatch.setenv("SRGSSR_CONSUMER_SECRET", "env-secret")
    s = SrgSsrOAuthSettings()
    assert s.consumer_key == "env-key"
    assert s.consumer_secret == "env-secret"


def test_build_srg_oauth_client_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SRGSSR_CONSUMER_KEY", "a")
    monkeypatch.setenv("SRGSSR_CONSUMER_SECRET", "b")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == _basic_header("a", "b")
        return httpx.Response(200, json={"access_token": "t", "expires_in": 120})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        oauth = build_srg_oauth_client(http_client=client)
        assert oauth.get_access_token() == "t"
    finally:
        client.close()
