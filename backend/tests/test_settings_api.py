"""Integration tests for ``/api/settings``."""

from __future__ import annotations

import json
from pathlib import Path

from flask.testing import FlaskClient

from app import create_app
from app.persistence import SQL_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase


def _patch_json(client: FlaskClient, payload: dict) -> tuple[dict, int]:
    res = client.patch(
        "/api/settings",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = res.get_json(silent=True)
    assert isinstance(data, dict)
    return data, res.status_code


def test_get_settings_defaults(client: FlaskClient) -> None:
    res = client.get("/api/settings")
    assert res.status_code == 200
    body = res.get_json()
    assert body == {
        "default_cefr": "B1",
        "translation_language": "en",
        "retrieval_top_k": None,
    }


def test_patch_get_round_trip_and_survives_new_app(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    app1 = create_app({"TESTING": True, "DATABASE_PATH": str(db_path)})
    try:
        c1 = app1.test_client()
        body, code = _patch_json(
            c1,
            {
                "default_cefr": "A2",
                "translation_language": "uk",
                "retrieval_top_k": 12,
            },
        )
        assert code == 200
        assert body["default_cefr"] == "A2"
        assert body["translation_language"] == "uk"
        assert body["retrieval_top_k"] == 12
    finally:
        ext = app1.extensions.get(SQL_DATABASE_EXTENSION_KEY)
        if isinstance(ext, SqlDatabase):
            ext.dispose()

    app2 = create_app({"TESTING": True, "DATABASE_PATH": str(db_path)})
    try:
        c2 = app2.test_client()
        res = c2.get("/api/settings")
        assert res.status_code == 200
        assert res.get_json() == {
            "default_cefr": "A2",
            "translation_language": "uk",
            "retrieval_top_k": 12,
        }
    finally:
        ext2 = app2.extensions.get(SQL_DATABASE_EXTENSION_KEY)
        if isinstance(ext2, SqlDatabase):
            ext2.dispose()


def test_patch_invalid_translation_language(client: FlaskClient) -> None:
    data, code = _patch_json(client, {"translation_language": "de"})
    assert code == 400
    assert data.get("error")


def test_patch_invalid_cefr(client: FlaskClient) -> None:
    data, code = _patch_json(client, {"default_cefr": "X9"})
    assert code == 400
    assert data.get("error")


def test_patch_clear_retrieval_top_k(client: FlaskClient) -> None:
    _patch_json(client, {"retrieval_top_k": 5})
    data, code = _patch_json(client, {"retrieval_top_k": None})
    assert code == 200
    assert data["retrieval_top_k"] is None


def test_patch_non_object_body(client: FlaskClient) -> None:
    res = client.patch(
        "/api/settings",
        data=json.dumps([]),
        content_type="application/json",
    )
    assert res.status_code == 400
