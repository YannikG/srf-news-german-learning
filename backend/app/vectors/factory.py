"""Composition root for vector embedding persistence (Phase 5)."""

from __future__ import annotations

from ..persistence.vectors_db import VectorsDatabase
from .repository import WordEmbeddingsRepository


def build_word_embeddings_repository(vectors_db: VectorsDatabase) -> WordEmbeddingsRepository:
    """Return a repository for ``vectors.db`` (sqlite-vec vec0)."""
    return WordEmbeddingsRepository(vectors_db)
