"""Composition root for :class:`LexiconRetrievalService`."""

from __future__ import annotations

from flask import Flask

from ..ollama import OLLAMA_IDLE_SERVICE_KEY
from ..ollama.embeddings import OllamaEmbedClient
from ..ollama.service import OllamaIdleService
from ..persistence import SQL_DATABASE_EXTENSION_KEY, VECTORS_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from ..persistence.vectors_db import VectorsDatabase
from ..settings.factory import build_settings_service
from ..vectors.factory import build_word_embeddings_repository
from ..words.repository import SqliteWordsRepository
from .service import LexiconRetrievalService

LEXICON_RETRIEVAL_SERVICE_KEY = "lexicon_retrieval_service"


def build_lexicon_retrieval_service(app: Flask) -> LexiconRetrievalService:
    """Wire retrieval from Flask config and extensions (no HTTP routes).

    Requires a non-empty ``OLLAMA_BASE_URL`` (set via environment and/or Compose
    for the service hostname on the container network, e.g. ``http://ollama:11434``).

    Returns a singleton per ``app`` (cached in ``app.extensions``) so the
    underlying ``httpx`` client in :class:`~app.ollama.embeddings.OllamaEmbedClient`
    is reused across calls.
    """
    cached = app.extensions.get(LEXICON_RETRIEVAL_SERVICE_KEY)
    if isinstance(cached, LexiconRetrievalService):
        return cached

    raw_sql = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(raw_sql, SqlDatabase):
        raise RuntimeError("sql_database extension missing for LexiconRetrievalService")
    raw_vec = app.extensions.get(VECTORS_DATABASE_EXTENSION_KEY)
    if not isinstance(raw_vec, VectorsDatabase):
        raise RuntimeError("vectors_database extension missing for LexiconRetrievalService")

    settings_service = build_settings_service(raw_sql)

    base = str(app.config.get("OLLAMA_BASE_URL") or "").strip()
    if not base:
        raise RuntimeError(
            "OLLAMA_BASE_URL is not set. Set it in the environment for your runtime "
            "(for Docker Compose, add OLLAMA_BASE_URL on the web service to the Ollama "
            "HTTP origin reachable on the stack network, typically http://ollama:11434).",
        )
    embed_client = OllamaEmbedClient(base_url=base)

    idle_raw = app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    idle_svc = idle_raw if isinstance(idle_raw, OllamaIdleService) else None

    sidecar_base = str(app.config.get("SIDECAR_BASE_URL") or "").strip()
    secret_raw = app.config.get("SIDECAR_SHARED_SECRET")
    sidecar_secret = secret_raw if isinstance(secret_raw, str) else ""

    svc = LexiconRetrievalService(
        words_repo=SqliteWordsRepository(raw_sql),
        vectors_repo=build_word_embeddings_repository(raw_vec),
        embed_client=embed_client,
        settings_row=lambda: settings_service.get_settings(),
        idle_service=idle_svc,
        sidecar_base_url=sidecar_base,
        sidecar_shared_secret=sidecar_secret,
    )
    app.extensions[LEXICON_RETRIEVAL_SERVICE_KEY] = svc
    return svc
