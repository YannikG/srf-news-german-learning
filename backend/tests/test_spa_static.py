"""Tests for optional Vite SPA static serving."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.persistence import SQL_DATABASE_EXTENSION_KEY, VECTORS_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase
from app.persistence.vectors_db import VectorsDatabase


def _dispose_app_databases(application: Flask) -> None:
    ext = application.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if isinstance(ext, SqlDatabase):
        ext.dispose()
    v_ext = application.extensions.get(VECTORS_DATABASE_EXTENSION_KEY)
    if isinstance(v_ext, VectorsDatabase):
        v_ext.dispose()


def test_root_404_when_spa_dist_missing(client: FlaskClient) -> None:
    """Default test app has no ``index.html`` under ``STATIC_SPA_DIR``."""
    response = client.get("/")
    assert response.status_code == 404


def test_api_health_not_shadowed_when_spa_present(tmp_path_factory: pytest.TempPathFactory) -> None:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    spa = tmp_path_factory.mktemp("spa")
    html = "<!DOCTYPE html><html><body>spa</body></html>"
    (spa / "index.html").write_text(html, encoding="utf-8")

    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
            "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
            "STATIC_SPA_DIR": str(spa),
        },
    )
    try:
        tc = application.test_client()
        health = tc.get("/api/health")
        assert health.status_code == 200
        assert health.get_json() == {"ok": True}

        root = tc.get("/")
        assert root.status_code == 200
        assert b"spa" in root.data

        unknown = tc.get("/any/vue/route")
        assert unknown.status_code == 200
        assert b"spa" in unknown.data
    finally:
        _dispose_app_databases(application)
