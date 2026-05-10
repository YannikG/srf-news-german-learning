"""HTTP client for SRGSSR Articles API v2 (Bearer-authenticated ``GET /articles``)."""

from __future__ import annotations

from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from .models import ArticleListPage
from .settings import SrgArticlesApiSettings


class SrgArticlesApiError(Exception):
    """HTTP or contract failure when calling the articles list endpoint."""

    def __init__(self, message: str, status_code: int, body: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class SrgArticlesApiClient:
    """Fetches one page from ``GET {base_url}/articles``."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        user_agent: str | None = None,
        http_client: httpx.Client | None = None,
        request_timeout_seconds: float = 30.0,
        settings: SrgArticlesApiSettings | None = None,
    ) -> None:
        resolved = settings if settings is not None else SrgArticlesApiSettings()
        self._base_url = (base_url if base_url is not None else resolved.base_url).rstrip("/")
        self._user_agent = user_agent if user_agent is not None else resolved.user_agent
        self._own_client = http_client is None
        self._client = http_client or httpx.Client(timeout=request_timeout_seconds)

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> SrgArticlesApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def fetch_articles_page(
        self,
        access_token: str,
        *,
        publisher: str = "SRF",
        limit: int = 10,
        cursor: str | None = None,
    ) -> ArticleListPage:
        """Return the first (or ``cursor``) page; ``limit`` must stay within API bounds (1–10)."""
        if limit < 1 or limit > 10:
            msg = "limit must be between 1 and 10 for the SRG articles API"
            raise ValueError(msg)
        url = urljoin(self._base_url + "/", "articles")
        params: dict[str, str] = {"publisher": publisher, "limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "User-Agent": self._user_agent,
        }
        try:
            response = self._client.get(url, params=params, headers=headers)
        except httpx.RequestError as exc:
            raise SrgArticlesApiError(f"SRG articles request failed: {exc}", 502) from exc

        body_text = response.text
        if response.status_code == 401:
            raise SrgArticlesApiError(
                "SRG articles API rejected the token (401). Check credentials and token scope.",
                401,
                body_text,
            )
        if response.status_code == 429:
            raise SrgArticlesApiError(
                "SRG articles API rate limited the request (429). Try again later.",
                429,
                body_text,
            )
        if response.status_code != httpx.codes.OK:
            raise SrgArticlesApiError(
                f"SRG articles request failed with status {response.status_code}.",
                response.status_code,
                body_text,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise SrgArticlesApiError("Articles response is not valid JSON.", 502) from exc
        try:
            return ArticleListPage.model_validate(payload)
        except ValidationError as exc:
            raise SrgArticlesApiError(
                "Articles response does not match the expected schema.",
                502,
            ) from exc
