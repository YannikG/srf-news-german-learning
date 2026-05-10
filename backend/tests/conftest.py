"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.persistence import SQL_DATABASE_EXTENSION_KEY, VECTORS_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase
from app.persistence.vectors_db import VectorsDatabase


@pytest.fixture(autouse=True)
def _reset_sidecar_http_client_after_test() -> Generator[None, None, None]:
    """Avoid cross-test pollution from the process-wide sidecar ``httpx`` client."""
    yield
    from app.sidecar.client import reset_shared_sidecar_http_client

    reset_shared_sidecar_http_client()


@pytest.fixture()
def app(tmp_path_factory: pytest.TempPathFactory) -> Generator[Flask, None, None]:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
            # Tests mock Ollama HTTP; host is arbitrary but must be non-empty for embed client.
            "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
            # Isolate from developer env (e.g. NEWS_ACTIVE_PROVIDER=newsapi would fail bootstrap).
            "NEWS_ACTIVE_PROVIDER": "srgssr",
        },
    )
    yield application
    ext = application.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if isinstance(ext, SqlDatabase):
        ext.dispose()
    v_ext = application.extensions.get(VECTORS_DATABASE_EXTENSION_KEY)
    if isinstance(v_ext, VectorsDatabase):
        v_ext.dispose()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
