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

_DEFAULT_OLLAMA_BASE = "http://ollama:11434"


def build_lexicon_retrieval_service(app: Flask) -> LexiconRetrievalService:
    """Wire retrieval from Flask config and extensions (no HTTP routes).

    Uses ``OLLAMA_BASE_URL`` when set; if empty after stripping, falls back to
    ``http://ollama:11434`` so the embed client always has an absolute base URL.
    """
    raw_sql = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(raw_sql, SqlDatabase):
        raise RuntimeError("sql_database extension missing for LexiconRetrievalService")
    raw_vec = app.extensions.get(VECTORS_DATABASE_EXTENSION_KEY)
    if not isinstance(raw_vec, VectorsDatabase):
        raise RuntimeError("vectors_database extension missing for LexiconRetrievalService")

    settings_service = build_settings_service(raw_sql)

    base = str(app.config.get("OLLAMA_BASE_URL") or "").strip() or _DEFAULT_OLLAMA_BASE
    embed_client = OllamaEmbedClient(base_url=base)

    idle_raw = app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    idle_svc = idle_raw if isinstance(idle_raw, OllamaIdleService) else None

    sidecar_base = str(app.config.get("SIDECAR_BASE_URL") or "").strip()
    secret_raw = app.config.get("SIDECAR_SHARED_SECRET")
    sidecar_secret = secret_raw if isinstance(secret_raw, str) else ""

    return LexiconRetrievalService(
        words_repo=SqliteWordsRepository(raw_sql),
        vectors_repo=build_word_embeddings_repository(raw_vec),
        embed_client=embed_client,
        settings_row=lambda: settings_service.get_settings(),
        idle_service=idle_svc,
        sidecar_base_url=sidecar_base,
        sidecar_shared_secret=sidecar_secret,
    )
