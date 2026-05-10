"""Tests for the /api/health endpoint."""

from __future__ import annotations

from flask.testing import FlaskClient


def test_health_returns_ok(client: FlaskClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert payload["ok"] is True
    assert "sidecar" not in payload
