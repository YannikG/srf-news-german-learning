"""Background inspect loop after Ollama start; publishes ``ollama_container`` on the SSE hub."""

from __future__ import annotations

import logging
import threading
import time

from flask import Flask

from ..events.constants import EVENTS_SSE_HUB_KEY
from ..events.hub import SseHub
from ..sidecar.client import probe_sidecar_inspect

logger = logging.getLogger(__name__)

_MAX_TICKS = 90
_SLEEP_S = 2.0


def spawn_ollama_container_inspect_watcher(app: Flask, base: str, secret: str) -> None:
    """Poll sidecar inspect and broadcast ``ollama_container`` until running or cap.

    Skipped when ``app.config['TESTING']`` is true so pytest does not spawn threads.
    """
    if app.config.get("TESTING"):
        return

    hub_raw = app.extensions.get(EVENTS_SSE_HUB_KEY)
    hub = hub_raw if isinstance(hub_raw, SseHub) else None

    def run() -> None:
        with app.app_context():
            for i in range(_MAX_TICKS + 1):
                if i > 0:
                    time.sleep(_SLEEP_S)
                try:
                    ok, err, summary = probe_sidecar_inspect(base, secret or None)
                except Exception:
                    logger.exception("ollama_container watcher probe failed")
                    ok, err, summary = False, "probe_failed", None
                if hub is not None:
                    payload: dict[str, object]
                    if ok and summary:
                        payload = {k: str(v) for k, v in summary.items()}
                    elif ok:
                        payload = {"state": "unknown"}
                    else:
                        payload = {"state": "inspect_error", "detail": (err or "error")[:200]}
                    try:
                        hub.publish("ollama_container", payload)
                    except Exception:
                        logger.exception("ollama_container publish failed")
                if ok and summary and summary.get("state") == "running":
                    return

    threading.Thread(
        target=run,
        daemon=True,
        name="ollama-inspect-watcher",
    ).start()
