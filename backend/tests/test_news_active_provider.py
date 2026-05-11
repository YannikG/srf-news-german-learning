"""Tests for ``NEWS_ACTIVE_PROVIDER`` resolution at app bootstrap."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import create_app
from app.news.active_provider import news_active_provider_raw_for_resolve
from app.persistence import SQL_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase


def test_news_active_provider_raw_stringifies_non_str_config() -> None:
    assert news_active_provider_raw_for_resolve(123, None) == "123"


def test_invalid_news_active_provider_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("NEWS_ACTIVE_PROVIDER", "unknown_vendor")
    db_path = tmp_path / "app.db"
    with pytest.raises(ValueError, match="NEWS_ACTIVE_PROVIDER must be one of"):
        create_app({"TESTING": True, "DATABASE_PATH": str(db_path)})


def test_non_string_news_active_provider_in_test_config_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with pytest.raises(ValueError, match="NEWS_ACTIVE_PROVIDER must be one of"):
        create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": str(db_path),
                "NEWS_ACTIVE_PROVIDER": 123,
            },
        )


def test_newsapi_provider_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("NEWS_ACTIVE_PROVIDER", "newsapi")
    monkeypatch.setenv("NEWSAPI_API_KEY", "test-key")
    monkeypatch.setenv("NEWSAPI_DEFAULT_QUERY", "Schweiz")
    db_path = tmp_path / "app.db"
    app = create_app({"TESTING": True, "DATABASE_PATH": str(db_path)})
    try:
        assert app.config["NEWS_ACTIVE_PROVIDER"] == "newsapi"
    finally:
        ext = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
        if isinstance(ext, SqlDatabase):
            ext.dispose()


def test_test_config_overrides_env_provider(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("NEWS_ACTIVE_PROVIDER", "newsapi")
    db_path = tmp_path / "app.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
            "NEWS_ACTIVE_PROVIDER": "srgssr",
        },
    )
    try:
        assert app.config["NEWS_ACTIVE_PROVIDER"] == "srgssr"
    finally:
        ext = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
        if isinstance(ext, SqlDatabase):
            ext.dispose()
