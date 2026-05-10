"""Integration tests for ``vectors.db`` and ``WordEmbeddingsRepository`` (P5-I01)."""

from __future__ import annotations

import sqlite3
import struct
from pathlib import Path

import pytest
from flask import Flask

from app.persistence import VECTORS_DATABASE_EXTENSION_KEY
from app.persistence.vectors_db import VectorsDatabase
from app.vectors import init_vectors_database
from app.vectors.constants import EMBEDDING_DIM
from app.vectors.factory import build_word_embeddings_repository
from app.vectors.repository import WordEmbeddingsRepository
from app.vectors.serialize import pack_float32


def _axis_embedding(scale: float) -> list[float]:
    v = [0.0] * EMBEDDING_DIM
    v[0] = scale
    return v


def test_pack_float32_layout() -> None:
    vec = [0.25, -0.5, 0.125]
    blob = pack_float32(vec)
    assert struct.unpack(f"{len(vec)}f", blob) == tuple(vec)


def test_init_rejects_legacy_numpy_migration(tmp_path: Path) -> None:
    db_path = tmp_path / "vectors.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_id TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        INSERT INTO _migrations (migration_id) VALUES ('001_word_embeddings_numpy');
        """,
    )
    conn.close()
    with pytest.raises(RuntimeError, match="legacy"):
        init_vectors_database(db_path)


def test_insert_rejects_wrong_length(tmp_path: Path) -> None:
    db_path = tmp_path / "vectors.db"
    init_vectors_database(db_path)
    vdb = VectorsDatabase(db_path)
    try:
        repo = WordEmbeddingsRepository(vdb)
        with pytest.raises(ValueError, match="expected 768"):
            repo.insert(1, [0.1, 0.2])
    finally:
        vdb.dispose()


def test_knn_returns_expected_nearest_word(tmp_path: Path) -> None:
    db_path = tmp_path / "vectors.db"
    init_vectors_database(db_path)
    vdb = VectorsDatabase(db_path)
    try:
        repo = WordEmbeddingsRepository(vdb)
        repo.insert(1, _axis_embedding(1.0))
        repo.insert(2, _axis_embedding(2.0))
        repo.insert(10, _axis_embedding(10.0))
        ranked = repo.knn_by_vector(_axis_embedding(2.1), k=2)
        assert ranked[0][0] == 2
        assert ranked[1][0] in (1, 10)
    finally:
        vdb.dispose()


def test_create_app_registers_vectors_database(app: Flask) -> None:
    ext = app.extensions.get(VECTORS_DATABASE_EXTENSION_KEY)
    assert isinstance(ext, VectorsDatabase)


def test_factory_builds_repository(app: Flask) -> None:
    vdb = app.extensions.get(VECTORS_DATABASE_EXTENSION_KEY)
    assert isinstance(vdb, VectorsDatabase)
    repo = build_word_embeddings_repository(vdb)
    assert isinstance(repo, WordEmbeddingsRepository)
