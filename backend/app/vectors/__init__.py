"""Vectors database bootstrap (Phase 5, P5-I01).

Import ``WordEmbeddingsRepository`` from ``app.vectors.repository`` to avoid a
circular import with ``app.persistence``.
"""

from __future__ import annotations

from .constants import EMBEDDING_DIM, VECTORS_DB_PATH
from .init_db import init_vectors_database

__all__ = [
    "EMBEDDING_DIM",
    "VECTORS_DB_PATH",
    "init_vectors_database",
]
