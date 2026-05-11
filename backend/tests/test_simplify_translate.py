"""Tests for P8-I07: non-German article translation + CEFR simplification."""

from __future__ import annotations

import json
from collections.abc import Generator, Iterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from app.articles.repository import SqliteArticlesRepository
from app.articles.simplify_repository import SqliteArticleSimplifyRepository
from app.articles.simplify_service import ArticleSimplifyService
from app.db import init_database
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
        self.last_system: str | None = None
        self.last_user: str | None = None

    def stream_assistant_text(self, *, system: str, user: str) -> Iterator[str]:
        self.last_system = system
        self.last_user = user
        yield from self._chunks


@pytest.fixture()
def dbs(tmp_path: Path) -> Generator[tuple[SqlDatabase, VectorsDatabase], None, None]:
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


def _llm_payload() -> dict:
    return {
        "markdown": "Vereinfachter deutscher Text.",
        "used_word_ids": [],
        "suggestions": [
            {"german_label": "Nachrichten", "translation": "news", "category": "noun"},
            {"german_label": "Wirtschaft", "translation": "economy", "category": "noun"},
            {"german_label": "steigen", "translation": "to rise", "category": "verb"},
        ],
    }


def _build_service(
    sdb: SqlDatabase,
    vdb: VectorsDatabase,
    chat: _FakeChat,
) -> ArticleSimplifyService:
    retrieval = LexiconRetrievalService(
        words_repo=SqliteWordsRepository(sdb),
        vectors_repo=WordEmbeddingsRepository(vdb),
        embed_client=_embed_client_returning(_axis(1.0)),
        settings_row=lambda: {"retrieval_top_k": 5, "retrieval_context_max_chars": 10_000},
        idle_service=_idle_disabled(),
        sidecar_base_url="",
        sidecar_shared_secret="",
    )
    return ArticleSimplifyService(
        articles_repo=SqliteArticlesRepository(sdb),
        words_repo=SqliteWordsRepository(sdb),
        simplify_repo=SqliteArticleSimplifyRepository(sdb),
        retrieval=retrieval,
        chat_client=chat,
        sse_hub=_RecordingHub(),
        idle_service=None,
    )


def test_foreign_article_skips_retrieval_uses_translate_prompt(
    dbs: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    """English article triggers translate prompt and skips lexicon retrieval."""
    sdb, vdb = dbs
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO articles (external_id, title, markdown_original, language) "
                "VALUES ('newsapi:en1', 'Economy booms', 'The economy is growing fast.', 'en')"
            ),
        )

    chat = _FakeChat([json.dumps(_llm_payload())])
    svc = _build_service(sdb, vdb, chat)
    out = svc.simplify_article(1, "B1")

    assert out["simplification_id"] >= 1
    assert out["markdown_simplified"] == "Vereinfachter deutscher Text."
    assert out["used_word_ids"] == []
    assert len(out["suggested_word_ids"]) == 3

    assert chat.last_system is not None
    assert "written in en" in chat.last_system
    assert "Translate it into German" in chat.last_system
    assert "used_word_ids must be an empty array" in chat.last_system

    user_payload = json.loads(chat.last_user or "")
    assert "lexicon_words" not in user_payload
    assert user_payload["article_markdown"] == "The economy is growing fast."


def test_german_article_uses_standard_prompt(
    dbs: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    """German article (language='de') takes the existing retrieval + simplify path."""
    sdb, vdb = dbs
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO articles (external_id, title, markdown_original, language) "
                "VALUES ('srgssr:de1', 'Wirtschaft wächst', 'Die Wirtschaft wächst stark.', 'de')"
            ),
        )

    chat = _FakeChat([json.dumps(_llm_payload())])
    svc = _build_service(sdb, vdb, chat)
    out = svc.simplify_article(1, "B1")

    assert out["simplification_id"] >= 1
    assert chat.last_system is not None
    assert "Swiss German news articles" in chat.last_system
    assert "Translate" not in chat.last_system

    user_payload = json.loads(chat.last_user or "")
    assert "lexicon_words" in user_payload


def test_regional_german_tag_uses_standard_prompt(
    dbs: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    """Regional tags like 'de-CH' are treated as German (lexicon retrieval path)."""
    sdb, vdb = dbs
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO articles (external_id, title, markdown_original, language) "
                "VALUES ('srgssr:ch1', 'Schweizer News', 'Bericht aus der Schweiz.', 'de-CH')"
            ),
        )

    chat = _FakeChat([json.dumps(_llm_payload())])
    svc = _build_service(sdb, vdb, chat)
    out = svc.simplify_article(1, "B1")

    assert out["simplification_id"] >= 1
    assert chat.last_system is not None
    assert "Swiss German news articles" in chat.last_system
    assert "Translate" not in chat.last_system


def test_null_language_treated_as_german(
    dbs: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    """NULL language (legacy rows) takes the standard German path."""
    sdb, vdb = dbs
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO articles (external_id, title, markdown_original) "
                "VALUES ('srgssr:old', 'Alter Artikel', 'Alter Text ohne Sprache.')"
            ),
        )

    chat = _FakeChat([json.dumps(_llm_payload())])
    svc = _build_service(sdb, vdb, chat)
    out = svc.simplify_article(1, "B1")

    assert out["simplification_id"] >= 1
    assert chat.last_system is not None
    assert "Swiss German news articles" in chat.last_system
    assert "Translate" not in chat.last_system
