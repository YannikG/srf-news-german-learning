"""Thread-safe pub/sub for Server-Sent Events (one hub per process)."""

from __future__ import annotations

import contextlib
import json
import queue
import re
import threading
from collections.abc import Callable, Iterator

# Internal publishers only; still reject names that would break the SSE wire format.
_SSE_EVENT_NAME = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def _validate_event_name(event: str) -> None:
    if not _SSE_EVENT_NAME.fullmatch(event):
        raise ValueError(f"invalid SSE event name: {event!r}")


def format_sse(event: str, data: dict[str, object]) -> str:
    """Return one SSE message block (event + JSON data, no secrets in *data*)."""
    _validate_event_name(event)
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
        _validate_event_name(event)
        with self._lock:
            targets = list(self._queues)
        for target in targets:
            try:
                target.put_nowait((event, data))
            except queue.Full:
                # Slow consumer; drop rather than block publishers (idle events are low volume).
                continue

    def stream_events(
        self,
        *,
        initial_events_fn: Callable[[], list[tuple[str, dict[str, object]]]],
        ping_interval_s: float = 25.0,
    ) -> Iterator[str]:
        """Yield SSE chunks for one client.

        ``initial_events_fn`` runs only after this client is subscribed so publishes
        between subscription and the first snapshot are not dropped.
        """
        q = self.subscribe()
        try:
            for ev, payload in initial_events_fn():
                yield format_sse(ev, payload)
            while True:
                try:
                    ev, payload = q.get(timeout=ping_interval_s)
                    yield format_sse(ev, payload)
                except queue.Empty:
                    yield ": ping\n\n"
        finally:
            self.unsubscribe(q)
