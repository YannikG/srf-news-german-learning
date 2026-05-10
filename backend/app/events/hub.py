"""Thread-safe pub/sub for Server-Sent Events (one hub per process)."""

from __future__ import annotations

import contextlib
import json
import queue
import threading
from collections.abc import Iterator


def format_sse(event: str, data: dict[str, object]) -> str:
    """Return one SSE message block (event + JSON data, no secrets in *data*)."""
    payload = json.dumps(data, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


class SseHub:
    """Broadcasts typed events to all subscribers; each subscriber has a queue."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queues: list[queue.Queue[tuple[str, dict[str, object]]]] = []

    def subscribe(self) -> queue.Queue[tuple[str, dict[str, object]]]:
        q: queue.Queue[tuple[str, dict[str, object]]] = queue.Queue(maxsize=256)
        with self._lock:
            self._queues.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[tuple[str, dict[str, object]]]) -> None:
        with self._lock, contextlib.suppress(ValueError):
            self._queues.remove(q)

    def publish(self, event: str, data: dict[str, object]) -> None:
        with self._lock:
            targets = list(self._queues)
        for target in targets:
            try:
                target.put_nowait((event, data))
            except queue.Full:
                continue

    def stream_events(
        self,
        *,
        initial_events: list[tuple[str, dict[str, object]]],
        ping_interval_s: float = 25.0,
    ) -> Iterator[str]:
        """Yield SSE chunks for one client; *initial_events* are sent first."""
        q = self.subscribe()
        try:
            for ev, payload in initial_events:
                yield format_sse(ev, payload)
            while True:
                try:
                    ev, payload = q.get(timeout=ping_interval_s)
                    yield format_sse(ev, payload)
                except queue.Empty:
                    yield ": ping\n\n"
        finally:
            self.unsubscribe(q)
