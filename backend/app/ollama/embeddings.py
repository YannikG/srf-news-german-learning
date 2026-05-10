"""HTTP client for Ollama embedding vectors (``/api/embed``)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..vectors.constants import EMBEDDING_DIM

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
EMBED_PATH = "/api/embed"


class OllamaEmbedClient:
    """Fetches float embeddings from a running Ollama instance."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str = DEFAULT_EMBEDDING_MODEL,
        timeout: float = 120.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def embed_text(self, text: str) -> list[float]:
        """Return a single embedding vector for ``text`` (length ``EMBEDDING_DIM``)."""
        url = f"{self._base}{EMBED_PATH}"
        payload: dict[str, Any] = {"model": self._model, "input": text}
        try:
            response = self._client.post(url, json=payload)
        except httpx.RequestError as exc:
            msg = f"Ollama embed request failed: {exc}"
            raise OllamaEmbedError(msg) from exc

        if response.status_code != 200:
            detail = response.text[:500] if response.text else f"HTTP {response.status_code}"
            raise OllamaEmbedError(f"Ollama embed HTTP {response.status_code}: {detail}")

        try:
            body = response.json()
        except ValueError as exc:
            raise OllamaEmbedError("Ollama embed response is not valid JSON") from exc

        vec = _parse_embedding_vector(body)
        if len(vec) != EMBEDDING_DIM:
            raise OllamaEmbedError(
                f"Ollama embed length {len(vec)} does not match expected {EMBEDDING_DIM}",
            )
        return vec


class OllamaEmbedError(Exception):
    """Raised when the Ollama embedding HTTP call fails or returns unusable data."""


def _parse_embedding_vector(body: Any) -> list[float]:
    """Extract the first embedding list from an Ollama ``/api/embed`` JSON body."""
    if not isinstance(body, dict):
        raise OllamaEmbedError("Ollama embed JSON must be an object")

    if "embeddings" in body:
        embeddings = body["embeddings"]
        if not isinstance(embeddings, list) or not embeddings:
            raise OllamaEmbedError("Ollama embed response missing embeddings array")
        first = embeddings[0]
        if not isinstance(first, list):
            raise OllamaEmbedError("Ollama embed embeddings[0] must be a list")
        return [float(x) for x in first]

    legacy = body.get("embedding")
    if isinstance(legacy, list):
        return [float(x) for x in legacy]

    raise OllamaEmbedError("Ollama embed response has no embeddings or embedding field")
