"""Tests for :class:`app.retrieval.service.LexiconRetrievalService` (P5-I02)."""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from app.db import init_database
from app.ollama.embeddings import OllamaEmbedClient
from app.ollama.service import OllamaIdleService
from app.persistence.sqlite_db import SqlDatabase
from app.persistence.vectors_db import VectorsDatabase
from app.retrieval.errors import RetrievalServiceError
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


def _idle_noop_stop() -> OllamaIdleService:
    return OllamaIdleService(
        idle_shutdown_seconds=120,
        warning_seconds=0,
        stop_fn=lambda: (True, None),
        idle_enabled=False,
    )


@pytest.fixture()
def sql_and_vectors(tmp_path: Path) -> Generator[tuple[SqlDatabase, VectorsDatabase], None, None]:
    app_db = tmp_path / "app.db"
    vec_db = tmp_path / "vectors.db"
    init_database(app_db)
    init_vectors_database(vec_db)
    sdb = SqlDatabase(app_db)
    vdb = VectorsDatabase(vec_db)
    yield sdb, vdb
    sdb.dispose()
    vdb.dispose()


def _settings(k: int | None = 2, max_chars: int | None = 10_000) -> dict:
    return {"retrieval_top_k": k, "retrieval_context_max_chars": max_chars}


def test_top_word_ids_empty_lexicon_returns_empty_without_sidecar(
    sql_and_vectors: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = sql_and_vectors
    words = SqliteWordsRepository(sdb)
    vectors = WordEmbeddingsRepository(vdb)
    starts: list[int] = []

    def track_start(_base: str, _secret: str | None) -> tuple[bool, str | None]:
        starts.append(1)
        return True, None

    svc = LexiconRetrievalService(
        words_repo=words,
        vectors_repo=vectors,
        embed_client=_embed_client_returning(_axis(1.0)),
        settings_row=lambda: _settings(),
        idle_service=_idle_noop_stop(),
        sidecar_base_url="",
        sidecar_shared_secret="",
        start_ollama_fn=track_start,
    )
    assert svc.top_word_ids_for_context("any text") == []
    assert starts == []


def test_top_word_ids_knn_order_respects_lexicon(
    sql_and_vectors: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = sql_and_vectors
    with sdb.begin() as conn:
        for wid, label in [(1, "eins"), (2, "zwei"), (10, "zehn")]:
            conn.execute(
                text(
                    "INSERT INTO words (id, german_label, category, difficulty, translation) "
                    "VALUES (:id, :gl, '', 'Neu', '')",
                ),
                {"id": wid, "gl": label},
            )

    words = SqliteWordsRepository(sdb)
    vectors = WordEmbeddingsRepository(vdb)
    vectors.insert(1, _axis(1.0))
    vectors.insert(2, _axis(2.0))
    vectors.insert(10, _axis(10.0))

    starts: list[int] = []

    def track_start(_base: str, _secret: str | None) -> tuple[bool, str | None]:
        starts.append(1)
        return True, None

    query_vec = _axis(2.1)
    svc = LexiconRetrievalService(
        words_repo=words,
        vectors_repo=vectors,
        embed_client=_embed_client_returning(query_vec),
        settings_row=lambda: _settings(k=2, max_chars=10_000),
        idle_service=_idle_noop_stop(),
        sidecar_base_url="http://sidecar:8090",
        sidecar_shared_secret="tok",
        start_ollama_fn=track_start,
    )

    ranked = svc.top_word_ids_for_context("article body")
    assert ranked == [2, 1]
    assert len(starts) == 1


def test_top_word_ids_invalid_settings_values_use_defaults(
    sql_and_vectors: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = sql_and_vectors
    with sdb.begin() as conn:
        for wid, label in [(1, "eins"), (2, "zwei"), (10, "zehn")]:
            conn.execute(
                text(
                    "INSERT INTO words (id, german_label, category, difficulty, translation) "
                    "VALUES (:id, :gl, '', 'Neu', '')",
                ),
                {"id": wid, "gl": label},
            )

    words = SqliteWordsRepository(sdb)
    vectors = WordEmbeddingsRepository(vdb)
    vectors.insert(1, _axis(1.0))
    vectors.insert(2, _axis(2.0))
    vectors.insert(10, _axis(10.0))

    query_vec = _axis(2.1)
    svc = LexiconRetrievalService(
        words_repo=words,
        vectors_repo=vectors,
        embed_client=_embed_client_returning(query_vec),
        settings_row=lambda: {"retrieval_top_k": "nope", "retrieval_context_max_chars": -1},
        idle_service=_idle_noop_stop(),
        sidecar_base_url="",
        sidecar_shared_secret="",
    )

    ranked = svc.top_word_ids_for_context("body")
    assert ranked[:2] == [2, 1]


def test_sidecar_start_failure_is_clean_error(
    sql_and_vectors: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = sql_and_vectors
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO words (id, german_label, category, difficulty, translation) "
                "VALUES (1, 'a', '', 'Neu', '')",
            ),
        )

    words = SqliteWordsRepository(sdb)
    vectors = WordEmbeddingsRepository(vdb)
    vectors.insert(1, _axis(1.0))
    idle = _idle_noop_stop()

    def fail_start(_base: str, _secret: str | None) -> tuple[bool, str | None]:
        return False, "sidecar down"

    svc = LexiconRetrievalService(
        words_repo=words,
        vectors_repo=vectors,
        embed_client=_embed_client_returning(_axis(1.0)),
        settings_row=lambda: _settings(),
        idle_service=idle,
        sidecar_base_url="http://sidecar:8090",
        sidecar_shared_secret="",
        start_ollama_fn=fail_start,
    )

    with pytest.raises(RetrievalServiceError, match="Sidecar Ollama start failed"):
        svc.top_word_ids_for_context("x")

    assert idle.sse_public_state()["refcount"] == 0


def test_ollama_http_error_still_decrements_idle_refcount(
    sql_and_vectors: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = sql_and_vectors
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO words (id, german_label, category, difficulty, translation) "
                "VALUES (1, 'a', '', 'Neu', '')",
            ),
        )

    words = SqliteWordsRepository(sdb)
    vectors = WordEmbeddingsRepository(vdb)
    vectors.insert(1, _axis(1.0))
    idle = _idle_noop_stop()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    bad_client = OllamaEmbedClient(base_url="http://ollama.test", http_client=http)

    svc = LexiconRetrievalService(
        words_repo=words,
        vectors_repo=vectors,
        embed_client=bad_client,
        settings_row=lambda: _settings(),
        idle_service=idle,
        sidecar_base_url="",
        sidecar_shared_secret="",
    )

    with pytest.raises(RetrievalServiceError, match="Ollama embed HTTP 500"):
        svc.top_word_ids_for_context("x")

    assert idle.sse_public_state()["refcount"] == 0
    bad_client.close()


def test_embed_and_store_word_round_trip(
    sql_and_vectors: tuple[SqlDatabase, VectorsDatabase],
) -> None:
    sdb, vdb = sql_and_vectors
    with sdb.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO words (id, german_label, category, difficulty, translation) "
                "VALUES (7, 'sieben', '', 'Neu', '')",
            ),
        )

    words = SqliteWordsRepository(sdb)
    vectors = WordEmbeddingsRepository(vdb)
    fixed = _axis(4.2)

    def capture(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        assert payload["input"] == "sieben"
        return httpx.Response(200, json={"embeddings": [fixed]})

    transport = httpx.MockTransport(capture)
    http = httpx.Client(transport=transport)
    embedder = OllamaEmbedClient(base_url="http://ollama.test", http_client=http)

    svc = LexiconRetrievalService(
        words_repo=words,
        vectors_repo=vectors,
        embed_client=embedder,
        settings_row=lambda: _settings(),
        idle_service=_idle_noop_stop(),
        sidecar_base_url="",
        sidecar_shared_secret="",
    )

    try:
        svc.embed_and_store_word(7)
    finally:
        embedder.close()

    ranked = vectors.knn_by_vector(fixed, k=1)
    assert ranked[0][0] == 7


def test_build_lexicon_retrieval_service_wires_from_app(app) -> None:
    from app.retrieval.factory import build_lexicon_retrieval_service

    svc = build_lexicon_retrieval_service(app)
    assert isinstance(svc, LexiconRetrievalService)


def test_build_lexicon_retrieval_service_is_singleton_per_app(app) -> None:
    from app.retrieval.factory import build_lexicon_retrieval_service

    first = build_lexicon_retrieval_service(app)
    second = build_lexicon_retrieval_service(app)
    assert first is second


def test_build_lexicon_retrieval_service_requires_ollama_base_url(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    from app import create_app
    from app.persistence import SQL_DATABASE_EXTENSION_KEY, VECTORS_DATABASE_EXTENSION_KEY
    from app.persistence.sqlite_db import SqlDatabase
    from app.persistence.vectors_db import VectorsDatabase
    from app.retrieval.factory import build_lexicon_retrieval_service

    db_path = tmp_path_factory.mktemp("db") / "app.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
            "OLLAMA_BASE_URL": "   ",
        },
    )
    try:
        with pytest.raises(RuntimeError, match="OLLAMA_BASE_URL is not set"):
            build_lexicon_retrieval_service(app)
    finally:
        ext = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
        if isinstance(ext, SqlDatabase):
            ext.dispose()
        v_ext = app.extensions.get(VECTORS_DATABASE_EXTENSION_KEY)
        if isinstance(v_ext, VectorsDatabase):
            v_ext.dispose()
