"""Streaming chat completion client for Ollama ``/api/chat`` (Phase 5 P5-I03)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx

CHAT_PATH = "/api/chat"


class OllamaChatStreamError(Exception):
    """Raised when the Ollama chat HTTP call fails or returns unusable data."""


class OllamaChatStreamIncompleteError(OllamaChatStreamError):
    """Raised when the stream ends before Ollama reports ``done: true``."""


class OllamaChatStreamClient:
    """Streams assistant ``content`` deltas from Ollama ``/api/chat``."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float = 300.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    @property
    def model(self) -> str:
        return self._model

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def stream_assistant_text(
        self,
        *,
        system: str,
        user: str,
    ) -> Iterator[str]:
        """Yield assistant ``message.content`` fragments; validates final ``done`` flag.

        Raises:
            OllamaChatStreamError: on HTTP errors or malformed JSON lines.
            OllamaChatStreamIncompleteError: if the HTTP body ends without ``done: true``.
        """
        url = f"{self._base}{CHAT_PATH}"
        payload: dict[str, Any] = {
            "model": self._model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            with self._client.stream(
                "POST",
                url,
                json=payload,
                timeout=self._timeout,
            ) as response:
                if response.status_code != 200:
                    detail = (
                        response.text[:500] if response.text else f"HTTP {response.status_code}"
                    )
                    raise OllamaChatStreamError(
                        f"Ollama chat HTTP {response.status_code}: {detail}",
                    )
                saw_done = False
                for line in response.iter_lines():
                    if line is None or line == "":
                        continue
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", errors="replace")
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError as exc:
                        msg = f"Ollama chat stream line is not JSON: {line!r}"
                        raise OllamaChatStreamError(msg) from exc
                    if not isinstance(obj, dict):
                        continue
                    if obj.get("done") is True:
                        saw_done = True
                    msg = obj.get("message")
                    if isinstance(msg, dict):
                        piece = msg.get("content")
                        if isinstance(piece, str) and piece:
                            yield piece
                if not saw_done:
                    raise OllamaChatStreamIncompleteError(
                        "Ollama chat stream ended without a terminal done frame",
                    )
        except httpx.RequestError as exc:
            raise OllamaChatStreamError(f"Ollama chat request failed: {exc}") from exc
