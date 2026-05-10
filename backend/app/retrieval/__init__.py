"""Lexicon-scoped vector retrieval over ``vectors.db`` (Phase 5, P5-I02)."""

from __future__ import annotations

from .errors import RetrievalServiceError
from .factory import build_lexicon_retrieval_service
from .service import LexiconRetrievalService

__all__ = [
    "LexiconRetrievalService",
    "RetrievalServiceError",
    "build_lexicon_retrieval_service",
]
