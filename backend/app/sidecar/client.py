"""Call the sidecar HTTP API from the Flask app (e.g. health probe)."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

SIDECAR_TOKEN_HEADER = "X-Sidecar-Token"


def probe_sidecar_inspect(base_url: str, shared_secret: str | None) -> tuple[bool, str | None]:
    """GET /ollama/inspect on the sidecar. Returns (success, error_detail)."""
    url = f"{base_url.rstrip('/')}/ollama/inspect"
    headers: dict[str, str] = {}
    secret = (shared_secret or "").strip()
    if secret:
        headers[SIDECAR_TOKEN_HEADER] = secret
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(url, headers=headers)
    except httpx.RequestError as exc:
        logger.debug("Sidecar probe failed: %s", exc)
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
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers)
    except httpx.RequestError as exc:
        logger.debug("Sidecar stop failed: %s", exc)
        return False, str(exc)

    if response.status_code == 200:
        return True, None
    detail = response.text[:200] if response.text else f"HTTP {response.status_code}"
    return False, detail
