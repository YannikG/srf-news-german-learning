"""HTTP client for the PONS Dictionary API (``GET /v1/dictionary``)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

PONS_API_BASE = "https://api.pons.com"
REQUEST_TIMEOUT_SECONDS = 10.0

ALLOWED_DICTIONARIES = frozenset({"deen", "deuk", "dees", "defr", "deit", "dept"})


class PonsDictionaryError(Exception):
    """Domain error raised when the PONS lookup fails."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class PonsLookupResult:
    """Normalised result from a single PONS dictionary query."""

    hits: list[dict[str, Any]] = field(default_factory=list)


class PonsDictionaryClient:
    """Proxies a single term lookup to ``api.pons.com``."""

    def __init__(
        self,
        *,
        api_secret: str,
        http_client: httpx.Client | None = None,
        base_url: str = PONS_API_BASE,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self._secret = api_secret
        self._base = base_url.rstrip("/")
        self._own_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        if self._own_client:
            self._client.close()

    def __enter__(self) -> PonsDictionaryClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def lookup(self, query: str, dictionary: str) -> PonsLookupResult:
        """Look up *query* in the given PONS *dictionary* (e.g. ``deen``)."""
        url = f"{self._base}/v1/dictionary"
        headers = {
            "X-Secret": self._secret,
            "Accept": "application/json",
        }
        params = {"q": query, "l": dictionary}

        try:
            response = self._client.get(url, headers=headers, params=params)
        except httpx.RequestError as exc:
            raise PonsDictionaryError(f"PONS request failed: {exc}", 502) from exc

        if response.status_code == 204:
            return PonsLookupResult(hits=[])

        if response.status_code == 403:
            raise PonsDictionaryError("PONS API secret invalid or dictionary not permitted", 502)

        if response.status_code == 503:
            raise PonsDictionaryError("PONS Tageslimit erreicht", 503)

        if response.status_code != 200:
            raise PonsDictionaryError(
                f"PONS returned unexpected status {response.status_code}", 502
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PonsDictionaryError("PONS response is not valid JSON", 502) from exc

        if not isinstance(payload, list):
            return PonsLookupResult(hits=[])

        return PonsLookupResult(hits=payload)
