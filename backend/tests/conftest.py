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


@pytest.fixture()
def app(tmp_path_factory: pytest.TempPathFactory) -> Generator[Flask, None, None]:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
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
