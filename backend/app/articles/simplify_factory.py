"""Composition root for :class:`ArticleSimplifyService` (P5-I03)."""

from __future__ import annotations

from flask import Flask

from ..events import EVENTS_SSE_HUB_KEY
from ..events.hub import SseHub
from ..ollama import OLLAMA_IDLE_SERVICE_KEY
from ..ollama.chat_stream import OllamaChatStreamClient
from ..ollama.service import OllamaIdleService
from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from ..retrieval.factory import build_lexicon_retrieval_service
from ..words.repository import SqliteWordsRepository
from .repository import SqliteArticlesRepository
from .simplify_repository import SqliteArticleSimplifyRepository
from .simplify_service import ArticleSimplifyService

ARTICLE_SIMPLIFY_SERVICE_KEY = "article_simplify_service"
OLLAMA_SIMPLIFY_CHAT_CLIENT_KEY = "ollama_simplify_chat_client"


def build_article_simplify_service(app: Flask) -> ArticleSimplifyService:
    """Wire simplify service; requires ``OLLAMA_BASE_URL`` and SSE hub."""
    cached = app.extensions.get(ARTICLE_SIMPLIFY_SERVICE_KEY)
    if isinstance(cached, ArticleSimplifyService):
        return cached

    raw_sql = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(raw_sql, SqlDatabase):
        raise RuntimeError("sql_database extension missing for ArticleSimplifyService")

    hub_raw = app.extensions.get(EVENTS_SSE_HUB_KEY)
    if not isinstance(hub_raw, SseHub):
        raise RuntimeError("events SSE hub extension missing for ArticleSimplifyService")

    base = str(app.config.get("OLLAMA_BASE_URL") or "").strip()
    if not base:
        raise RuntimeError(
            "OLLAMA_BASE_URL is not set (required for simplify chat streaming).",
        )

    model = str(app.config.get("OLLAMA_SIMPLIFY_MODEL") or "gemma4:e2b").strip()
    if not model:
        model = "gemma4:e2b"

    chat_raw = app.extensions.get(OLLAMA_SIMPLIFY_CHAT_CLIENT_KEY)
    if isinstance(chat_raw, OllamaChatStreamClient):
        chat_client = chat_raw
    else:
        chat_client = OllamaChatStreamClient(base_url=base, model=model)
        app.extensions[OLLAMA_SIMPLIFY_CHAT_CLIENT_KEY] = chat_client

    idle_raw = app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    idle_svc = idle_raw if isinstance(idle_raw, OllamaIdleService) else None

    articles_repo = SqliteArticlesRepository(raw_sql)
    words_repo = SqliteWordsRepository(raw_sql)
    simplify_repo = SqliteArticleSimplifyRepository(raw_sql)
    retrieval = build_lexicon_retrieval_service(app)

    svc = ArticleSimplifyService(
        articles_repo=articles_repo,
        words_repo=words_repo,
        simplify_repo=simplify_repo,
        retrieval=retrieval,
        chat_client=chat_client,
        sse_hub=hub_raw,
        idle_service=idle_svc,
    )
    app.extensions[ARTICLE_SIMPLIFY_SERVICE_KEY] = svc
    return svc
