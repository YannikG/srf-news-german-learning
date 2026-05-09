"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture()
def app(tmp_path_factory: pytest.TempPathFactory) -> Flask:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    return create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
        },
    )


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()
