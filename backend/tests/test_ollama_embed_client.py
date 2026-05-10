"""Tests for :class:`app.ollama.embeddings.OllamaEmbedClient`."""

from __future__ import annotations

import json

import httpx
import pytest

from app.ollama.embeddings import OllamaEmbedClient, OllamaEmbedError, _parse_embedding_vector
from app.vectors.constants import EMBEDDING_DIM


def test_parse_embeddings_array_shape() -> None:
    vec = [0.25] * EMBEDDING_DIM
    out = _parse_embedding_vector({"embeddings": [vec]})
    assert out == vec


def test_parse_legacy_embedding_key() -> None:
    vec = [0.1] * EMBEDDING_DIM
    out = _parse_embedding_vector({"embedding": vec})
    assert out == vec


def test_parse_rejects_missing_vectors() -> None:
    with pytest.raises(OllamaEmbedError, match="no embeddings or embedding"):
        _parse_embedding_vector({"model": "x"})


def test_embed_text_uses_mock_transport() -> None:
    vec = [0.0] * EMBEDDING_DIM
    vec[0] = 3.14

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        body = json.loads(request.content.decode())
        assert body["model"] == "nomic-embed-text"
        assert body["input"] == "hello"
        return httpx.Response(200, json={"embeddings": [vec]})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    embedder = OllamaEmbedClient(base_url="http://ollama.test", http_client=client)
    try:
        got = embedder.embed_text("hello")
    finally:
        embedder.close()
    assert got == vec
    assert len(got) == EMBEDDING_DIM
