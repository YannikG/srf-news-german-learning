"""Tests for /api/health sidecar probe when SIDECAR_BASE_URL is set."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.persistence import SQL_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase


@pytest.fixture()
def app_with_sidecar(tmp_path_factory: pytest.TempPathFactory) -> Generator[Flask, None, None]:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
            "SIDECAR_BASE_URL": "http://sidecar:8090",
            "SIDECAR_SHARED_SECRET": "test-secret",
        },
    )
    yield application
    ext = application.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if isinstance(ext, SqlDatabase):
        ext.dispose()


@pytest.fixture()
def client_sidecar(app_with_sidecar: Flask) -> FlaskClient:
    return app_with_sidecar.test_client()


@patch("app.sidecar.client._sidecar_http")
def test_health_sidecar_ok_when_inspect_succeeds(
    mock_sidecar_http: MagicMock,
    client_sidecar: FlaskClient,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.json.return_value = {
        "ollama": {"state": "running", "name": "/project-ollama-1"},
    }
    mock_http = MagicMock()
    mock_http.get.return_value = mock_response
    mock_sidecar_http.return_value = mock_http

    response = client_sidecar.get("/api/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["sidecar"] == {
        "status": "ok",
        "ollama": {"state": "running", "name": "/project-ollama-1"},
    }
    mock_http.get.assert_called_once()
    args, kwargs = mock_http.get.call_args
    assert args[0] == "http://sidecar:8090/ollama/inspect"
    assert kwargs["headers"]["X-Sidecar-Token"] == "test-secret"


@patch("app.sidecar.client._sidecar_http")
def test_health_sidecar_error_when_inspect_fails(
    mock_sidecar_http: MagicMock,
    client_sidecar: FlaskClient,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "unauthorized"
    mock_http = MagicMock()
    mock_http.get.return_value = mock_response
    mock_sidecar_http.return_value = mock_http

    response = client_sidecar.get("/api/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["sidecar"]["status"] == "error"
    assert "detail" in payload["sidecar"]
