"""OAuth2 client_credentials client for ``api.srgssr.ch`` access tokens."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx

from .defaults import DEFAULT_TOKEN_URL, DEFAULT_USER_AGENT

TOKEN_URL = DEFAULT_TOKEN_URL
USER_AGENT = DEFAULT_USER_AGENT
_DEFAULT_EXPIRES_IN = 3600


def _token_url_with_grant_query(token_url: str) -> str:
    """SRG expects ``grant_type=client_credentials`` in the URL query and an empty POST body."""
    parts = urlsplit(token_url.strip())
    parsed = parse_qsl(parts.query, keep_blank_values=True)
    q_pairs = [(k, v) for k, v in parsed if k != "grant_type"]
    q_pairs.append(("grant_type", "client_credentials"))
    query = urlencode(q_pairs)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


class SrgOAuthClientError(Exception):
    """Base class for SRG OAuth client failures."""


class SrgOAuthHttpError(SrgOAuthClientError):
    """HTTP error from the token endpoint (e.g. 401, 429)."""

    def __init__(self, message: str, status_code: int, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class SrgOAuthTokenResponseError(SrgOAuthClientError):
    """Token response missing ``access_token`` or invalid JSON."""


class SrgOAuthClient:
    """Fetches and caches bearer tokens; refreshes about ``refresh_skew_seconds`` before expiry."""

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        *,
        token_url: str = DEFAULT_TOKEN_URL,
        user_agent: str = DEFAULT_USER_AGENT,
        http_client: httpx.Client | None = None,
        refresh_skew_seconds: int = 60,
        request_timeout_seconds: float = 30.0,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._token_url = token_url
        self._user_agent = user_agent
        self._refresh_skew = refresh_skew_seconds
        self._mono: Callable[[], float] = monotonic if monotonic is not None else time.monotonic
        self._own_client = http_client is None
        self._client = http_client or httpx.Client(timeout=request_timeout_seconds)
        self._cache_lock = threading.Lock()
        self._fetch_lock = threading.Lock()
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
        with self._cache_lock:
            now = self._mono()
            if (
                self._token is not None
                and self._cache_until_mono is not None
                and now < self._cache_until_mono
            ):
                return self._token

        with self._fetch_lock:
            with self._cache_lock:
                now = self._mono()
                if (
                    self._token is not None
                    and self._cache_until_mono is not None
                    and now < self._cache_until_mono
                ):
                    return self._token

            token, cache_seconds = self._do_token_request()

            with self._cache_lock:
                now = self._mono()
                self._token = token
                self._cache_until_mono = now + cache_seconds
                return token

    def _do_token_request(self) -> tuple[str, float]:
        try:
            url = _token_url_with_grant_query(self._token_url)
            response = self._client.post(
                url,
                auth=(self._consumer_key, self._consumer_secret),
                content=b"",
                headers={
                    "User-Agent": self._user_agent,
                    "Cache-Control": "no-cache",
                },
            )
        except httpx.RequestError as exc:
            raise SrgOAuthClientError(f"SRG OAuth token request failed: {exc}") from exc

        body = response.text
        if response.status_code == 401:
            raise SrgOAuthHttpError("SRG OAuth token request rejected (401).", 401, body)
        if response.status_code == 429:
            raise SrgOAuthHttpError("SRG OAuth token rate limited (429).", 429, body)
        if response.status_code != httpx.codes.OK:
            raise SrgOAuthHttpError(
                f"SRG OAuth token request failed with status {response.status_code}.",
                response.status_code,
                body,
            )
        try:
            parsed = response.json()
        except ValueError as exc:
            raise SrgOAuthTokenResponseError("Token response is not valid JSON.") from exc
        if not isinstance(parsed, dict):
            raise SrgOAuthTokenResponseError("Token response JSON must be an object.")
        access_token = parsed.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise SrgOAuthTokenResponseError("Token response missing access_token string.")
        expires_in_raw = parsed.get("expires_in", _DEFAULT_EXPIRES_IN)
        try:
            expires_in = int(expires_in_raw)
        except (TypeError, ValueError):
            expires_in = _DEFAULT_EXPIRES_IN
        cache_seconds = max(0, expires_in - self._refresh_skew)
        return access_token, float(cache_seconds)
