"""HTTP client for NewsAPI.org (``/v2/everything`` and ``/v2/top-headlines``)."""

from __future__ import annotations

import httpx
from pydantic import ValidationError

from .models import NewsApiResponse
from .settings import DEFAULT_BASE_URL, NewsApiSettings


class NewsApiClientError(Exception):
    """HTTP or contract failure when calling a NewsAPI endpoint."""

    def __init__(self, message: str, status_code: int, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class NewsApiClient:
    """Fetches one page from ``/v2/everything`` or ``/v2/top-headlines``."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        http_client: httpx.Client | None = None,
        request_timeout_seconds: float = 30.0,
        settings: NewsApiSettings | None = None,
    ) -> None:
        if settings is None and api_key is None:
            settings = NewsApiSettings()
        self._api_key = api_key if api_key is not None else settings.api_key  # type: ignore[union-attr]
        fallback_base = settings.base_url if settings is not None else DEFAULT_BASE_URL
        self._base_url = (base_url if base_url is not None else fallback_base).rstrip("/")
        self._own_client = http_client is None
        self._client = http_client or httpx.Client(timeout=request_timeout_seconds)

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> NewsApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def fetch_page(
        self,
        *,
        endpoint: str = "everything",
        params: dict[str, str] | None = None,
    ) -> NewsApiResponse:
        """Call ``/v2/{endpoint}`` with the given query parameters."""
        url = f"{self._base_url}/v2/{endpoint}"
        headers = {
            "X-Api-Key": self._api_key,
            "Accept": "application/json",
        }
        try:
            response = self._client.get(url, params=params or {}, headers=headers)
        except httpx.RequestError as exc:
            raise NewsApiClientError(
                f"NewsAPI request failed: {exc}",
                502,
            ) from exc

        body_text = response.text
        if response.status_code == 401:
            raise NewsApiClientError(
                "NewsAPI rejected the API key (401). Check NEWSAPI_API_KEY.",
                401,
                body_text,
            )
        if response.status_code == 429:
            raise NewsApiClientError(
                "NewsAPI rate limited the request (429). Try again later.",
                429,
                body_text,
            )
        if response.status_code != httpx.codes.OK:
            raise NewsApiClientError(
                f"NewsAPI request failed with status {response.status_code}.",
                response.status_code,
                body_text,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise NewsApiClientError(
                "NewsAPI response is not valid JSON.",
                502,
            ) from exc
        try:
            return NewsApiResponse.model_validate(payload)
        except ValidationError as exc:
            raise NewsApiClientError(
                "NewsAPI response does not match the expected schema.",
                502,
            ) from exc
