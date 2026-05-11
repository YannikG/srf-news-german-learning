"""Tests for namespace_external_id helper and cross-provider DB uniqueness."""

from __future__ import annotations

import pytest
from freezegun import freeze_time
from sqlalchemy import text

from app import create_app
from app.news.external_id import namespace_external_id
from app.news.service import NewsRefreshService
from app.news.upstream_port import NewsIngestUpstreamPort, NormalizedArticlePage
from app.persistence import SQL_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase

# -- Pure unit tests for namespace_external_id --


class TestNamespaceExternalId:
    def test_basic_prefix(self) -> None:
        assert namespace_external_id("srgssr", "abc") == "srgssr:abc"

    def test_urn_with_colons_preserved(self) -> None:
        raw = "urn:pdp:faro_srf:article:001"
        assert namespace_external_id("srgssr", raw) == f"srgssr:{raw}"

    def test_already_prefixed_is_idempotent(self) -> None:
        assert namespace_external_id("srgssr", "srgssr:abc") == "srgssr:abc"

    def test_different_provider_prefix_not_stripped(self) -> None:
        result = namespace_external_id("newsapi", "srgssr:abc")
        assert result == "newsapi:srgssr:abc"

    def test_empty_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            namespace_external_id("", "id")

    def test_empty_raw_id_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            namespace_external_id("srgssr", "")

    def test_provider_with_colon_raises(self) -> None:
        with pytest.raises(ValueError, match="must not contain"):
            namespace_external_id("bad:slug", "id")


# -- Integration: cross-provider rows stay unique --


class _FakeUpstream(NewsIngestUpstreamPort):
    """Minimal adapter returning pre-built rows for testing."""

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def fetch_normalized_page(
        self, *, limit: int, cursor: str | None = None
    ) -> NormalizedArticlePage:
        return NormalizedArticlePage(rows=list(self._rows), next_cursor=None)


def _make_app_and_db(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
            "NEWS_ACTIVE_PROVIDER": "srgssr",
        },
    )
    db = application.extensions[SQL_DATABASE_EXTENSION_KEY]
    assert isinstance(db, SqlDatabase)
    return application, db


def test_same_raw_id_different_providers_creates_two_rows(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    raw_id = "shared-upstream-id-123"
    row_a = {
        "external_id": raw_id,
        "publisher": "SRF",
        "provenance": None,
        "title": "Titel A",
        "lead": None,
        "markdown_original": "# Titel A",
        "release_date": "2025-01-01",
        "modification_date": None,
        "news_provider": "srgssr",
    }
    row_b = {
        **row_a,
        "title": "Title B",
        "markdown_original": "# Title B",
        "news_provider": "newsapi",
    }

    _app, db = _make_app_and_db(tmp_path_factory)
    upstream_a = _FakeUpstream([row_a])
    upstream_b = _FakeUpstream([row_b])
    svc_a = NewsRefreshService(db, upstream_a, provider_slug="srgssr")
    svc_b = NewsRefreshService(db, upstream_b, provider_slug="newsapi")

    with freeze_time("2025-06-01T10:00:00+00:00"):
        res_a = svc_a.refresh()
        assert res_a["articles_upserted"] == 1
        res_b = svc_b.refresh()
        assert res_b["articles_upserted"] == 1

    with db.begin() as conn:
        rows = conn.execute(
            text("SELECT external_id, news_provider FROM articles ORDER BY external_id"),
        ).fetchall()
    assert len(rows) == 2
    stored_ids = {r[0] for r in rows}
    assert f"newsapi:{raw_id}" in stored_ids
    assert f"srgssr:{raw_id}" in stored_ids


def test_already_prefixed_external_id_stays_unchanged(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """An external_id that already carries the provider prefix is stored verbatim."""
    _app, db = _make_app_and_db(tmp_path_factory)
    with db.begin() as conn:
        conn.execute(
            text("INSERT INTO articles (external_id, title, news_provider) VALUES (:eid, :t, :np)"),
            {"eid": "srgssr:already-prefixed", "t": "A", "np": "srgssr"},
        )
    with db.begin() as conn:
        row = conn.execute(
            text("SELECT external_id FROM articles WHERE title = 'A'"),
        ).scalar_one()
    assert row == "srgssr:already-prefixed"
