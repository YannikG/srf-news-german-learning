"""REST routes for Ollama idle lifecycle (Phase 4)."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify

from .constants import OLLAMA_IDLE_SERVICE_KEY
from .service import OllamaIdleService

ollama_bp = Blueprint("ollama", __name__)


def _service() -> OllamaIdleService | None:
    raw = current_app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    return raw if isinstance(raw, OllamaIdleService) else None


@ollama_bp.post("/ollama/cancel-idle-shutdown")
def cancel_idle_shutdown() -> tuple[Response, int]:
    svc = _service()
    if svc is None:
        return (
            jsonify(
                error="service_unavailable",
                detail="Ollama idle service not initialized",
            ),
            503,
        )
    svc.cancel_idle_shutdown()
    return jsonify(ok=True), 200


@ollama_bp.post("/ollama/go-to-sleep")
def go_to_sleep() -> tuple[Response, int]:
    svc = _service()
    if svc is None:
        return (
            jsonify(
                error="service_unavailable",
                detail="Ollama idle service not initialized",
            ),
            503,
        )
    if not svc.idle_enabled:
        return (
            jsonify(
                error="sidecar_not_configured",
                detail="SIDECAR_BASE_URL is not set; cannot stop Ollama",
            ),
            503,
        )
    ok, err = svc.go_to_sleep()
    if not ok:
        return jsonify(ok=False, detail=err or "stop_failed"), 502
    return jsonify(ok=True), 200
