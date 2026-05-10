"""Tests for article simplify service and persistence (P5-I03)."""

from __future__ import annotations

import json
from collections.abc import Generator, Iterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from app.articles.repository import SqliteArticlesRepository
from app.articles.simplify_repository import SqliteArticleSimplifyRepository
from app.articles.simplify_service import ArticleSimplifyService, ArticleSimplifyServiceError
from app.db import init_database
from app.ollama.chat_stream import OllamaChatStreamIncompleteError
from app.ollama.embeddings import OllamaEmbedClient
from app.ollama.service import OllamaIdleService
from app.persistence.sqlite_db import SqlDatabase
from app.persistence.vectors_db import VectorsDatabase
from app.retrieval.service import LexiconRetrievalService
from app.vectors import init_vectors_database
from app.vectors.constants import EMBEDDING_DIM
from app.vectors.repository import WordEmbeddingsRepository
from app.words.repository import SqliteWordsRepository


def _axis(scale: float) -> list[float]:
    v = [0.0] * EMBEDDING_DIM
    v[0] = scale
    return v


def _embed_client_returning(vec: list[float]) -> OllamaEmbedClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [vec]})

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    return OllamaEmbedClient(base_url="http://ollama.test", http_client=http)


def _idle_disabled() -> OllamaIdleService:
    return OllamaIdleService(
        idle_shutdown_seconds=120,
        warning_seconds=0,
        stop_fn=lambda: (True, None),
        idle_enabled=False,
    )


class _RecordingHub:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def publish(self, event: str, data: dict[str, object]) -> None:
        self.events.append((event, data))


class _FakeChat:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    def stream_assistant_text(self, *, system: str, user: str) -> Iterator[str]:
        yield from self._chunks


@pytest.fixture()
def simplify_dbs(
    tmp_path: Path,
) -> Generator[tuple[SqlDatabase, VectorsDatabase], None, None]:
    app_db = tmp_path / "app.db"
    vec_db = tmp_path / "vectors.db"
    init_database(app_db)
    init_vectors_database(vec_db)
    sdb = SqlDatabase(app_db)
    vdb = VectorsDatabase(vec_db)
    try:
        yield sdb, vdb
    finally:
        sdb.dispose()
        vdb.dispose()


def test_simplify_persists_rows_and_emits_llm_events(
    simplify_dbs: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = simplify_dbs
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO articles (external_id, title, markdown_original) "
                "VALUES ('e1', 'T', 'Original body text')",
            ),
        )
    hub = _RecordingHub()
    llm_payload = {
        "markdown": "Vereinfacht ![x](http://example.com/a.png) ohne Bilder.",
        "used_word_ids": [],
        "suggestions": [
            {"german_label": "Alpha", "translation": "a", "category": "test"},
            {"german_label": "Beta", "translation": "b", "category": "test"},
            {"german_label": "Gamma", "translation": "c", "category": "test"},
        ],
    }
    chat = _FakeChat([json.dumps(llm_payload)])
    retrieval = LexiconRetrievalService(
        words_repo=SqliteWordsRepository(sdb),
        vectors_repo=WordEmbeddingsRepository(vdb),
        embed_client=_embed_client_returning(_axis(1.0)),
        settings_row=lambda: {"retrieval_top_k": 5, "retrieval_context_max_chars": 10_000},
        idle_service=_idle_disabled(),
        sidecar_base_url="",
        sidecar_shared_secret="",
    )
    svc = ArticleSimplifyService(
        articles_repo=SqliteArticlesRepository(sdb),
        words_repo=SqliteWordsRepository(sdb),
        simplify_repo=SqliteArticleSimplifyRepository(sdb),
        retrieval=retrieval,
        chat_client=chat,
        sse_hub=hub,
        idle_service=None,
    )
    out = svc.simplify_article(1, "b1")
    assert out["simplification_id"] >= 1
    assert "ohne Bilder" in out["markdown_simplified"]
    assert "example.com" not in out["markdown_simplified"]
    assert "![x]" not in out["markdown_simplified"]
    assert len(out["suggested_word_ids"]) == 3

    names = [e[0] for e in hub.events]
    assert "llm_chunk" in names
    assert names[-1] == "llm_done"

    with sdb.begin() as conn:
        n_used = conn.execute(
            text("SELECT COUNT(*) FROM article_simplification_used_words"),
        ).scalar_one()
        n_sug = conn.execute(
            text("SELECT COUNT(*) FROM article_simplification_suggested_words"),
        ).scalar_one()
    assert int(n_used) == 0
    assert int(n_sug) == 3


def test_simplify_incomplete_stream_raises(
    simplify_dbs: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = simplify_dbs
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO articles (external_id, title, markdown_original) "
                "VALUES ('e2', 'T', 'Body')",
            ),
        )

    class _BrokenChat:
        def stream_assistant_text(self, *, system: str, user: str) -> Iterator[str]:
            yield "{"
            raise OllamaChatStreamIncompleteError("cut")

    retrieval = LexiconRetrievalService(
        words_repo=SqliteWordsRepository(sdb),
        vectors_repo=WordEmbeddingsRepository(vdb),
        embed_client=_embed_client_returning(_axis(1.0)),
        settings_row=lambda: {"retrieval_top_k": 2, "retrieval_context_max_chars": 10_000},
        idle_service=_idle_disabled(),
        sidecar_base_url="",
        sidecar_shared_secret="",
    )
    svc = ArticleSimplifyService(
        articles_repo=SqliteArticlesRepository(sdb),
        words_repo=SqliteWordsRepository(sdb),
        simplify_repo=SqliteArticleSimplifyRepository(sdb),
        retrieval=retrieval,
        chat_client=_BrokenChat(),
        sse_hub=_RecordingHub(),
        idle_service=None,
    )
    with pytest.raises(ArticleSimplifyServiceError, match="prematurely"):
        svc.simplify_article(1, "B1")
