"""Ollama idle lifecycle, sidecar stop hook, and SSE hub wiring."""

from __future__ import annotations

from flask import Flask

from ..events import EVENTS_SSE_HUB_KEY, SseHub
from ..ollama import OLLAMA_IDLE_SERVICE_KEY
from ..ollama.poll import start_idle_poll_thread
from ..ollama.service import OllamaIdleService
from ..sidecar.client import post_ollama_stop
from .default_settings import normalize_ollama_idle_config


def register_ollama_idle_and_event_stream(app: Flask) -> None:
    """Create idle service and SSE hub; wire listeners and optional background poll."""
    sidecar_base = str(app.config.get("SIDECAR_BASE_URL") or "").strip()
    sidecar_secret_raw = app.config.get("SIDECAR_SHARED_SECRET")
    sidecar_secret = sidecar_secret_raw if isinstance(sidecar_secret_raw, str) else ""
    idle_sec, warn_sec = normalize_ollama_idle_config(app)

    def stop_ollama() -> tuple[bool, str | None]:
        if not sidecar_base:
            return False, "SIDECAR_BASE_URL is not set"
        return post_ollama_stop(sidecar_base, sidecar_secret or None)

    idle_svc = OllamaIdleService(
        idle_shutdown_seconds=float(idle_sec),
        warning_seconds=float(warn_sec),
        stop_fn=stop_ollama,
        idle_enabled=bool(sidecar_base),
    )
    app.extensions[OLLAMA_IDLE_SERVICE_KEY] = idle_svc

    sse_hub = SseHub()
    app.extensions[EVENTS_SSE_HUB_KEY] = sse_hub

    def publish_ollama_state() -> None:
        sse_hub.publish("ollama_state", idle_svc.sse_public_state())

    idle_svc.add_state_listener(publish_ollama_state)

    def on_idle_warning() -> None:
        sse_hub.publish("shutdown_warning", {"warning_seconds": warn_sec})

    idle_svc.add_warning_listener(on_idle_warning)

    if app.config.get("OLLAMA_IDLE_START_POLL_THREAD"):
        start_idle_poll_thread(app)
