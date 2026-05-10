"""Call the sidecar HTTP API from the Flask app (e.g. health probe)."""

from __future__ import annotations

import logging
import threading

import httpx

logger = logging.getLogger(__name__)

SIDECAR_TOKEN_HEADER = "X-Sidecar-Token"

_lock = threading.Lock()
_shared_sidecar_http: httpx.Client | None = None


def _sidecar_http() -> httpx.Client:
    """Return a process-wide shared ``httpx.Client`` for sidecar calls (timeouts per request)."""
    global _shared_sidecar_http
    with _lock:
        if _shared_sidecar_http is None:
            _shared_sidecar_http = httpx.Client(
                limits=httpx.Limits(max_keepalive_connections=8, max_connections=16),
            )
        return _shared_sidecar_http


def reset_shared_sidecar_http_client() -> None:
    """Close and drop the shared sidecar HTTP client (used by tests between cases)."""
    global _shared_sidecar_http
    with _lock:
        if _shared_sidecar_http is not None:
            _shared_sidecar_http.close()
            _shared_sidecar_http = None


def probe_sidecar_inspect(base_url: str, shared_secret: str | None) -> tuple[bool, str | None]:
    """GET /ollama/inspect on the sidecar. Returns (success, error_detail)."""
    url = f"{base_url.rstrip('/')}/ollama/inspect"
    headers: dict[str, str] = {}
    secret = (shared_secret or "").strip()
    if secret:
        headers[SIDECAR_TOKEN_HEADER] = secret
    try:
        response = _sidecar_http().get(url, headers=headers, timeout=3.0)
    except httpx.RequestError as exc:
        logger.debug("Sidecar probe failed: %s", exc)
        return False, str(exc)

    if response.status_code == 200:
        return True, None
    detail = response.text[:200] if response.text else f"HTTP {response.status_code}"
    return False, detail


def post_ollama_start(base_url: str, shared_secret: str | None) -> tuple[bool, str | None]:
    """POST /ollama/start on the sidecar. Returns (success, error_detail)."""
    url = f"{base_url.rstrip('/')}/ollama/start"
    headers: dict[str, str] = {}
    secret = (shared_secret or "").strip()
    if secret:
        headers[SIDECAR_TOKEN_HEADER] = secret
    try:
        response = _sidecar_http().post(url, headers=headers, timeout=120.0)
    except httpx.RequestError as exc:
        logger.debug("Sidecar start failed: %s", exc)
        return False, str(exc)

    if response.status_code == 200:
        return True, None
    detail = response.text[:200] if response.text else f"HTTP {response.status_code}"
    return False, detail


def post_ollama_stop(base_url: str, shared_secret: str | None) -> tuple[bool, str | None]:
    """POST /ollama/stop on the sidecar. Returns (success, error_detail)."""
    url = f"{base_url.rstrip('/')}/ollama/stop"
    headers: dict[str, str] = {}
    secret = (shared_secret or "").strip()
    if secret:
        headers[SIDECAR_TOKEN_HEADER] = secret
    try:
        response = _sidecar_http().post(url, headers=headers, timeout=60.0)
    except httpx.RequestError as exc:
        logger.debug("Sidecar stop failed: %s", exc)
        return False, str(exc)

    if response.status_code == 200:
        return True, None
    detail = response.text[:200] if response.text else f"HTTP {response.status_code}"
    return False, detail
