"""REST routes for Ollama idle lifecycle (Phase 4)."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify

from ..events.constants import EVENTS_SSE_HUB_KEY
from ..events.hub import SseHub
from ..sidecar.client import post_ollama_start
from .constants import OLLAMA_IDLE_SERVICE_KEY
from .inspect_watcher import (
    bump_ollama_inspect_watcher_generation,
    spawn_ollama_container_inspect_watcher,
)
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
    hub_raw = current_app.extensions.get(EVENTS_SSE_HUB_KEY)
    hub = hub_raw if isinstance(hub_raw, SseHub) else None
    if hub is not None:
        hub.publish("shutdown_cancelled", {})
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
    bump_ollama_inspect_watcher_generation()
    ok, err = svc.go_to_sleep()
    if not ok:
        return jsonify(ok=False, detail=err or "stop_failed"), 502
    return jsonify(ok=True), 200


@ollama_bp.post("/ollama/start")
def start_ollama() -> tuple[Response, int]:
    """Ask the sidecar to start the Ollama container (wake after go-to-sleep or cold stop)."""
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
                detail="SIDECAR_BASE_URL is not set; cannot start Ollama",
            ),
            503,
        )
    base = str(current_app.config.get("SIDECAR_BASE_URL") or "").strip()
    secret_raw = current_app.config.get("SIDECAR_SHARED_SECRET")
    secret = secret_raw if isinstance(secret_raw, str) else ""
    ok, err = post_ollama_start(base, secret or None)
    if not ok:
        return jsonify(ok=False, detail=err or "start_failed"), 502
    hub_raw = current_app.extensions.get(EVENTS_SSE_HUB_KEY)
    hub = hub_raw if isinstance(hub_raw, SseHub) else None
    if hub is not None:
        hub.publish("ollama_state", svc.sse_public_state())
    spawn_ollama_container_inspect_watcher(current_app._get_current_object(), base, secret)
    return jsonify(ok=True), 200
