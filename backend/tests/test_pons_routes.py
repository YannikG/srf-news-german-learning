"""Tests for ``GET /api/external/pons/dictionary`` route."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app
from app.persistence import SQL_DATABASE_EXTENSION_KEY, VECTORS_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase
from app.persistence.vectors_db import VectorsDatabase
from app.pons.client import PonsDictionaryError, PonsLookupResult


@pytest.fixture()
def pons_app(tmp_path_factory: pytest.TempPathFactory) -> Generator[Flask, None, None]:
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(db_path),
            "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
            "NEWS_ACTIVE_PROVIDER": "srgssr",
            "PONS_API_SECRET": "test-pons-secret",
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
def pons_client(pons_app: Flask) -> FlaskClient:
    return pons_app.test_client()


class TestSecretMissing:
    def test_returns_503_without_secret(self, client: FlaskClient) -> None:
        resp = client.get("/api/external/pons/dictionary?q=Haus&l=deen")
        assert resp.status_code == 503
        data = resp.get_json()
        assert "not configured" in data["error"]


class TestMissingQuery:
    def test_returns_400_without_q(self, pons_client: FlaskClient) -> None:
        resp = pons_client.get("/api/external/pons/dictionary?l=deen")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "'q'" in data["error"]


class TestInvalidDictionary:
    def test_returns_400_for_bad_l(self, pons_client: FlaskClient) -> None:
        resp = pons_client.get("/api/external/pons/dictionary?q=Haus&l=zzzz")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "must be one of" in data["error"]


class TestSuccessProxy:
    @patch("app.pons.routes.PonsDictionaryClient")
    def test_proxies_hits(self, mock_cls: object, pons_client: FlaskClient) -> None:
        hits = [{"type": "entry", "roms": []}]
        instance = mock_cls.return_value  # type: ignore[union-attr]
        instance.lookup.return_value = PonsLookupResult(hits=hits)

        resp = pons_client.get("/api/external/pons/dictionary?q=Haus&l=deen")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["hits"] == hits


class TestErrorProxy:
    @patch("app.pons.routes.PonsDictionaryClient")
    def test_maps_pons_error(self, mock_cls: object, pons_client: FlaskClient) -> None:
        instance = mock_cls.return_value  # type: ignore[union-attr]
        instance.lookup.side_effect = PonsDictionaryError("Tageslimit erreicht", 503)

        resp = pons_client.get("/api/external/pons/dictionary?q=Haus&l=deen")

        assert resp.status_code == 503
        data = resp.get_json()
        assert "Tageslimit" in data["error"]


class TestDefaultDictFromSettings:
    @patch("app.pons.routes.PonsDictionaryClient")
    def test_uses_translation_language_uk(
        self, mock_cls: object, pons_app: Flask, pons_client: FlaskClient
    ) -> None:
        """When ``l`` is omitted and ``translation_language`` is ``uk``, route uses ``deuk``."""
        with pons_app.app_context():
            tc = pons_client
            tc.patch(
                "/api/settings",
                json={"translation_language": "uk"},
                content_type="application/json",
            )

        instance = mock_cls.return_value  # type: ignore[union-attr]
        instance.lookup.return_value = PonsLookupResult(hits=[])

        resp = pons_client.get("/api/external/pons/dictionary?q=Haus")
        assert resp.status_code == 200
        instance.lookup.assert_called_once_with("Haus", "deuk")


class TestHealthPonsFlag:
    def test_health_pons_available_true(self, pons_client: FlaskClient) -> None:
        resp = pons_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pons"]["available"] is True

    def test_health_pons_available_false(self, client: FlaskClient) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["pons"]["available"] is False
