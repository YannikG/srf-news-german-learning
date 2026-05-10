"""Background polling for :class:`OllamaIdleService`."""

from __future__ import annotations

import atexit
import logging
import threading

from flask import Flask

from .constants import OLLAMA_IDLE_POLL_STOP_KEY, OLLAMA_IDLE_SERVICE_KEY
from .service import OllamaIdleService

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 1.0


def _poll_loop(service: OllamaIdleService, stop: threading.Event) -> None:
    while not stop.wait(POLL_INTERVAL_SEC):
        try:
            service.poll()
        except Exception:
            logger.exception("Ollama idle poll failed")


def start_idle_poll_thread(app: Flask) -> None:
    """Start a daemon thread that calls ``service.poll()`` periodically."""
    if app.extensions.get(OLLAMA_IDLE_POLL_STOP_KEY) is not None:
        return
    raw = app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    if not isinstance(raw, OllamaIdleService):
        return
    service = raw
    if not service.idle_enabled:
        return

    stop = threading.Event()
    app.extensions[OLLAMA_IDLE_POLL_STOP_KEY] = stop
    thread = threading.Thread(
        target=_poll_loop,
        args=(service, stop),
        name="ollama-idle-poll",
        daemon=True,
    )
    thread.start()

    def _shutdown() -> None:
        stop.set()

    atexit.register(_shutdown)
