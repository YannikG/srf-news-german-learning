"""Tests for Ollama streaming chat client (P5-I03)."""

from __future__ import annotations

import httpx
import pytest

from app.ollama.chat_stream import (
    OllamaChatStreamClient,
    OllamaChatStreamIncompleteError,
)


def test_chat_stream_raises_when_done_frame_missing() -> None:
    body = b'{"message":{"role":"assistant","content":"x"},"done":false}\n'

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    client = OllamaChatStreamClient(
        base_url="http://ollama.test",
        model="m",
        http_client=http,
    )
    try:
        with pytest.raises(OllamaChatStreamIncompleteError):
            list(client.stream_assistant_text(system="s", user="u"))
    finally:
        client.close()


def test_chat_stream_yields_content_then_requires_done() -> None:
    body = (
        b'{"message":{"role":"assistant","content":"hello"},"done":false}\n'
        b'{"message":{"role":"assistant","content":""},"done":true}\n'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    client = OllamaChatStreamClient(
        base_url="http://ollama.test",
        model="m",
        http_client=http,
    )
    try:
        parts = list(client.stream_assistant_text(system="s", user="u"))
        assert "".join(parts) == "hello"
    finally:
        client.close()
