"""SSE routes (Phase 4 P4-I03)."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, stream_with_context

from ..ollama import OLLAMA_IDLE_SERVICE_KEY
from ..ollama.service import OllamaIdleService
from .constants import EVENTS_SSE_HUB_KEY
from .hub import SseHub

events_bp = Blueprint("events", __name__)


def _hub() -> SseHub | None:
    raw = current_app.extensions.get(EVENTS_SSE_HUB_KEY)
    return raw if isinstance(raw, SseHub) else None


def _idle_service() -> OllamaIdleService | None:
    raw = current_app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    return raw if isinstance(raw, OllamaIdleService) else None


@events_bp.get("/events/stream")
def events_stream() -> Response:
    hub = _hub()
    if hub is None:
        return Response("events hub not configured\n", status=503, mimetype="text/plain")

    def initial_events_fn() -> list[tuple[str, dict[str, object]]]:
        svc_inner = _idle_service()
        rows: list[tuple[str, dict[str, object]]] = []
        if svc_inner is not None:
            rows.append(("ollama_state", svc_inner.sse_public_state()))
        return rows

    gen = hub.stream_events(initial_events_fn=initial_events_fn)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return Response(
        stream_with_context(gen),
        mimetype="text/event-stream",
        headers=headers,
    )
