"""OAuth2 client_credentials client for ``api.srgssr.ch`` access tokens."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

import httpx

TOKEN_URL = "https://api.srgssr.ch/oauth/v1/accesstoken"
USER_AGENT = "srf-news-german-learning"
_DEFAULT_EXPIRES_IN = 3600


class SrgOAuthClientError(Exception):
    """Base class for SRG OAuth client failures."""


class SrgOAuthHttpError(SrgOAuthClientError):
    """HTTP error from the token endpoint (e.g. 401, 429)."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class SrgOAuthTokenResponseError(SrgOAuthClientError):
    """Token response missing ``access_token`` or invalid JSON."""


class SrgOAuthClient:
    """Fetches and caches bearer tokens; refreshes about ``refresh_skew_seconds`` before expiry."""

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        *,
        http_client: httpx.Client | None = None,
        refresh_skew_seconds: int = 60,
        request_timeout_seconds: float = 30.0,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._refresh_skew = refresh_skew_seconds
        self._mono: Callable[[], float] = monotonic if monotonic is not None else time.monotonic
        self._own_client = http_client is None
        self._client = http_client or httpx.Client(timeout=request_timeout_seconds)
        self._lock = threading.Lock()
        self._token: str | None = None
        self._cache_until_mono: float | None = None

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> SrgOAuthClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get_access_token(self) -> str:
        """Return a valid access token, using the in-memory cache when still fresh."""
        with self._lock:
            now = self._mono()
            if (
                self._token is not None
                and self._cache_until_mono is not None
                and now < self._cache_until_mono
            ):
                return self._token
            token, cache_seconds = self._request_token_unlocked()
            self._token = token
            self._cache_until_mono = now + cache_seconds
            return token

    def _request_token_unlocked(self) -> tuple[str, float]:
        response = self._client.post(
            TOKEN_URL,
            auth=(self._consumer_key, self._consumer_secret),
            data={"grant_type": "client_credentials"},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
            },
        )
        if response.status_code == 401:
            raise SrgOAuthHttpError("SRG OAuth token request rejected (401).", 401)
        if response.status_code == 429:
            raise SrgOAuthHttpError("SRG OAuth token rate limited (429).", 429)
        if response.status_code != httpx.codes.OK:
            raise SrgOAuthHttpError(
                f"SRG OAuth token request failed with status {response.status_code}.",
                response.status_code,
            )
        payload: dict[str, Any]
        try:
            payload = response.json()
        except ValueError as exc:
            raise SrgOAuthTokenResponseError("Token response is not valid JSON.") from exc
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise SrgOAuthTokenResponseError("Token response missing access_token string.")
        expires_in_raw = payload.get("expires_in", _DEFAULT_EXPIRES_IN)
        try:
            expires_in = int(expires_in_raw)
        except (TypeError, ValueError):
            expires_in = _DEFAULT_EXPIRES_IN
        cache_seconds = max(0, expires_in - self._refresh_skew)
        return access_token, float(cache_seconds)
