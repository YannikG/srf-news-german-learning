"""Tests for the app.db schema, indexes, and idempotent migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import MIGRATION_IDS, init_database

EXPECTED_TABLES = frozenset(
    {
        "_migrations",
        "article_simplification_suggested_words",
        "article_simplification_used_words",
        "article_simplifications",
        "article_words",
        "articles",
        "articles_fts",
        "articles_fts_config",
        "articles_fts_data",
        "articles_fts_docsize",
        "articles_fts_idx",
        "settings",
        "srg_sync_metadata",
        "words",
    },
)

EXPECTED_INDEXES = frozenset(
    {
        "idx_article_simplifications_article_id",
        "idx_article_simplification_suggested_words_word_id",
        "idx_article_simplification_used_words_word_id",
        "idx_articles_publisher",
        "idx_articles_release_date",
        "idx_articles_title",
        "idx_article_words_word_id",
        "idx_srg_sync_metadata_updated_at",
        "idx_words_category",
        "idx_words_difficulty",
        "idx_words_german_label",
    },
)

EXPECTED_TRIGGERS = frozenset(
    {
        "trg_article_simplifications_updated_at",
        "trg_articles_ad_fts",
        "trg_articles_ai_fts",
        "trg_articles_au_fts",
        "trg_articles_updated_at",
        "trg_srg_sync_metadata_updated_at",
        "trg_words_updated_at",
    },
)


def _table_columns(conn: sqlite3.Connection, table: str) -> dict[str, str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1]: row[2] for row in cur.fetchall()}  # name -> type


def _index_names(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'",
    )
    return {row[0] for row in cur.fetchall()}


def _trigger_names(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")
    return {row[0] for row in cur.fetchall()}


def test_init_database_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "app.db"
    first = init_database(db_path)
    second = init_database(db_path)
    assert first == list(MIGRATION_IDS)
    assert second == []

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT migration_id FROM _migrations ORDER BY id",
        ).fetchall()
        assert [row[0] for row in rows] == list(MIGRATION_IDS)
    finally:
        conn.close()


def test_migrations_table_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    init_database(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cols = _table_columns(conn, "_migrations")
        assert set(cols) == {"id", "migration_id", "applied_at"}
    finally:
        conn.close()


def test_all_tables_and_indexes_exist(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    init_database(db_path)

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'",
        )
        tables = {row[0] for row in cur.fetchall()}
        assert tables == EXPECTED_TABLES

        assert _index_names(conn) == EXPECTED_INDEXES

        assert _trigger_names(conn) == EXPECTED_TRIGGERS

        articles = _table_columns(conn, "articles")
        assert "cefr_level" in articles
        assert "news_provider" in articles

        words = _table_columns(conn, "words")
        assert "cefr_level" in words
        assert "difficulty" in words

        settings = _table_columns(conn, "settings")
        assert "default_cefr" in settings
        assert "translation_language" in settings
        assert "retrieval_top_k" in settings
        assert "retrieval_context_max_chars" in settings

        row = conn.execute("SELECT id, default_cefr, translation_language FROM settings").fetchone()
        assert row == (1, "B1", "en")
    finally:
        conn.close()


def test_article_word_foreign_keys_enforced(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    init_database(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO articles (external_id, title) VALUES ('ext-1', 'Titel')",
        )
        conn.execute(
            "INSERT INTO words (german_label, difficulty) VALUES ('das Haus', 'Leicht')",
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO article_words (article_id, word_id) VALUES (1, 999)",
            )
    finally:
        conn.close()
