"""Tests for ``post_ollama_start`` sidecar client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.sidecar.client import post_ollama_start


@patch("app.sidecar.client._sidecar_http")
def test_post_ollama_start_success(mock_sidecar_http: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_http = MagicMock()
    mock_http.post.return_value = mock_response
    mock_sidecar_http.return_value = mock_http

    ok, err = post_ollama_start("http://sidecar:8090", "secret")

    assert ok is True
    assert err is None
    mock_http.post.assert_called_once()
    args, kwargs = mock_http.post.call_args
    assert args[0] == "http://sidecar:8090/ollama/start"
    assert kwargs["headers"]["X-Sidecar-Token"] == "secret"


@patch("app.sidecar.client._sidecar_http")
def test_post_ollama_start_failure(mock_sidecar_http: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "busy"
    mock_http = MagicMock()
    mock_http.post.return_value = mock_response
    mock_sidecar_http.return_value = mock_http

    ok, err = post_ollama_start("http://sidecar:8090", None)

    assert ok is False
    assert err == "busy"
