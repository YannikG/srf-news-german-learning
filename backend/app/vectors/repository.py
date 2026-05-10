"""Insert and KNN queries for ``word_embeddings`` (sqlite-vec vec0)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..persistence.vectors_db import VectorsDatabase
from .constants import EMBEDDING_DIM
from .serialize import pack_float32


class WordEmbeddingsRepository:
    """Word embedding storage and KNN search via vec0."""

    def __init__(self, db: VectorsDatabase) -> None:
        self._db = db

    def insert(self, word_id: int, vector: Sequence[float]) -> None:
        """Insert or replace the embedding for ``word_id``."""
        if len(vector) != EMBEDDING_DIM:
            msg = f"expected {EMBEDDING_DIM} floats, got {len(vector)}"
            raise ValueError(msg)
        blob = pack_float32(vector)
        stmt = text(
            "INSERT OR REPLACE INTO word_embeddings (rowid, embedding) "
            "VALUES (:word_id, :embedding)",
        )
        with self._db.begin() as conn:
            conn.execute(stmt, {"word_id": word_id, "embedding": blob})

    def knn_by_vector(self, query: Sequence[float], k: int) -> list[tuple[int, float]]:
        """Return up to ``k`` ``(word_id, distance)`` pairs, ascending by distance."""
        if len(query) != EMBEDDING_DIM:
            msg = f"expected {EMBEDDING_DIM} floats, got {len(query)}"
            raise ValueError(msg)
        if k <= 0:
            return []
        with self._db.begin() as conn:
            return self._knn_vec0(conn, query, k)

    def _knn_vec0(
        self,
        conn: Connection,
        query: Sequence[float],
        k: int,
    ) -> list[tuple[int, float]]:
        blob = pack_float32(query)
        stmt = text(
            "SELECT rowid, distance FROM word_embeddings "
            "WHERE embedding MATCH :q ORDER BY distance LIMIT :lim",
        )
        rows = conn.execute(stmt, {"q": blob, "lim": k}).fetchall()
        return [(int(r[0]), float(r[1])) for r in rows]
