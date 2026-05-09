"""Integration tests for read-only article APIs (pagination, date filter, FTS)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import text

from app.articles import routes as articles_routes
from app.articles import service as articles_service
from app.persistence import SQL_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase


def _insert_article(
    app: Flask,
    *,
    external_id: str,
    title: str,
    release_date: str,
    markdown: str = "# body",
) -> None:
    db = app.extensions[SQL_DATABASE_EXTENSION_KEY]
    assert isinstance(db, SqlDatabase)
    with db.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO articles (external_id, title, release_date, markdown_original) "
                "VALUES (:external_id, :title, :release_date, :markdown)",
            ),
            {
                "external_id": external_id,
                "title": title,
                "release_date": release_date,
                "markdown": markdown,
            },
        )


@pytest.fixture()
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> date:
    d = date(2026, 5, 9)
    monkeypatch.setattr(articles_service, "default_list_filter_date", lambda: d)
    return d


def test_list_pagination_with_cursor(client: FlaskClient, app: Flask, fixed_today: date) -> None:
    day = fixed_today.isoformat()
    for i in range(5):
        _insert_article(
            app,
            external_id=f"ext-{i}",
            title=f"Titel {i}",
            release_date=day,
        )

    first = client.get("/api/articles?limit=2")
    assert first.status_code == 200
    body = first.get_json()
    assert isinstance(body, dict)
    assert len(body["items"]) == 2
    assert body["next_cursor"] is not None
    assert "markdown_original" not in body["items"][0]

    second = client.get(f"/api/articles?limit=2&cursor={body['next_cursor']}")
    assert second.status_code == 200
    b2 = second.get_json()
    assert isinstance(b2, dict)
    assert len(b2["items"]) == 2
    assert b2["next_cursor"] is not None

    third = client.get(f"/api/articles?limit=2&cursor={b2['next_cursor']}")
    assert third.status_code == 200
    b3 = third.get_json()
    assert isinstance(b3, dict)
    assert len(b3["items"]) == 1
    assert b3["next_cursor"] is None


def test_list_date_filter_and_empty_result(client: FlaskClient, app: Flask) -> None:
    _insert_article(
        app,
        external_id="a1",
        title="A",
        release_date="2026-05-08",
    )
    _insert_article(
        app,
        external_id="a2",
        title="B",
        release_date="2026-05-09",
    )

    only_may8 = client.get("/api/articles?date=2026-05-08")
    assert only_may8.status_code == 200
    data = only_may8.get_json()
    assert isinstance(data, dict)
    assert len(data["items"]) == 1
    assert data["items"][0]["external_id"] == "a1"

    empty = client.get("/api/articles?date=2026-01-01")
    assert empty.status_code == 200
    empty_body = empty.get_json()
    assert isinstance(empty_body, dict)
    assert empty_body["items"] == []
    assert empty_body["next_cursor"] is None


def test_search_no_hits_and_umlaut_prefix(
    client: FlaskClient, app: Flask, fixed_today: date
) -> None:
    day = fixed_today.isoformat()
    _insert_article(
        app,
        external_id="u1",
        title="Müller: Bericht aus Zürich",
        release_date=day,
    )
    _insert_article(
        app,
        external_id="u2",
        title="Andere Schlagzeile",
        release_date=day,
    )

    no_hits = client.get("/api/articles?q=zzzznomatchterm")
    assert no_hits.status_code == 200
    nh = no_hits.get_json()
    assert isinstance(nh, dict)
    assert nh["items"] == []

    hits = client.get("/api/articles?q=muller")
    assert hits.status_code == 200
    hs = hits.get_json()
    assert isinstance(hs, dict)
    assert len(hs["items"]) == 1
    assert hs["items"][0]["external_id"] == "u1"


def test_get_article_by_id_returns_markdown(client: FlaskClient, app: Flask) -> None:
    _insert_article(
        app,
        external_id="one",
        title="Eins",
        release_date="2026-05-09",
        markdown="## Inhalt\n\nHallo.",
    )
    res = client.get("/api/articles/1")
    assert res.status_code == 200
    row = res.get_json()
    assert isinstance(row, dict)
    assert row["markdown_original"] == "## Inhalt\n\nHallo."
    assert row["title"] == "Eins"


def test_get_article_missing_returns_404(client: FlaskClient) -> None:
    res = client.get("/api/articles/999")
    assert res.status_code == 404


def test_invalid_date_and_cursor_return_400(client: FlaskClient) -> None:
    bad_date = client.get("/api/articles?date=not-a-date")
    assert bad_date.status_code == 400

    bad_cursor = client.get("/api/articles?cursor=not-valid-base64!!!")
    assert bad_cursor.status_code == 400


def test_article_routes_do_not_reference_srg_api() -> None:
    src = Path(articles_routes.__file__).read_text(encoding="utf-8")
    assert "srgssr" not in src.lower()
