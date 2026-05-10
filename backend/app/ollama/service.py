"""Idle shutdown scheduling after the last tracked Ollama request ends."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

StopResult = tuple[bool, str | None]
StopFn = Callable[[], StopResult]
WarningListener = Callable[[], None]
StateListener = Callable[[], None]


class OllamaIdleService:
    """Tracks concurrent Ollama use; arms idle shutdown when refcount hits zero.

    When ``idle_enabled`` is false, deadlines are never armed and ``go_to_sleep``
    must not be invoked via routes (caller checks configuration).

    ``_idle_epoch`` is bumped on ``begin_request``, ``cancel_idle_shutdown``, and
    ``go_to_sleep`` so a pending idle shutdown can be abandoned before the sidecar
    stop runs. For the automatic idle path, ``poll`` calls ``_stop_fn`` while
    holding ``_lock`` after re-checking refcount and epoch so ``begin_request``
    cannot sneak in between the check and the stop call (callers may block until
    the HTTP stop returns).
    """

    def __init__(
        self,
        *,
        idle_shutdown_seconds: float,
        warning_seconds: float,
        stop_fn: StopFn,
        idle_enabled: bool,
    ) -> None:
        if idle_shutdown_seconds <= 0:
            raise ValueError("idle_shutdown_seconds must be positive")
        if float(warning_seconds) < 0:
            raise ValueError("warning_seconds must be non-negative")
        self._idle = float(idle_shutdown_seconds)
        self._warn = min(float(warning_seconds), self._idle)
        self._stop_fn = stop_fn
        self._idle_enabled = idle_enabled
        self._refcount = 0
        self._shutdown_deadline: float | None = None
        self._warning_fired = False
        self._idle_epoch = 0
        self._lock = threading.Lock()
        self._warning_listeners: list[WarningListener] = []
        self._state_listeners: list[StateListener] = []

    def add_warning_listener(self, fn: WarningListener) -> None:
        self._warning_listeners.append(fn)

    def add_state_listener(self, fn: StateListener) -> None:
        self._state_listeners.append(fn)

    def sse_public_state(self) -> dict[str, object]:
        """Snapshot safe for SSE clients (no secrets or sidecar URLs)."""
        with self._lock:
            return {
                "idle_enabled": self._idle_enabled,
                "refcount": self._refcount,
                "idle_shutdown_armed": self._shutdown_deadline is not None,
                "idle_warning_issued": self._warning_fired,
            }

    def _notify_state_observers(self) -> None:
        with self._lock:
            listeners = list(self._state_listeners)
        for fn in listeners:
            try:
                fn()
            except Exception:
                logger.exception("Ollama idle state listener failed")

    @property
    def idle_enabled(self) -> bool:
        return self._idle_enabled

    def begin_request(self) -> None:
        with self._lock:
            self._idle_epoch += 1
            self._refcount += 1
            self._shutdown_deadline = None
            self._warning_fired = False
        self._notify_state_observers()

    def end_request(self) -> None:
        with self._lock:
            if self._refcount == 0:
                return
            self._refcount -= 1
            if self._refcount == 0 and self._idle_enabled:
                self._arm_idle_unlocked(time.time())
        self._notify_state_observers()

    def _arm_idle_unlocked(self, now: float) -> None:
        self._shutdown_deadline = now + self._idle
        self._warning_fired = False

    def cancel_idle_shutdown(self) -> None:
        with self._lock:
            self._idle_epoch += 1
            self._shutdown_deadline = None
            self._warning_fired = False
        self._notify_state_observers()

    def go_to_sleep(self) -> StopResult:
        """Stop Ollama immediately via ``stop_fn``; clears idle deadlines.

        Does not change ``refcount``. If a request is still in flight, this is a
        hard stop: the sidecar stops the container and in-flight calls fail.
        """
        with self._lock:
            self._idle_epoch += 1
            self._shutdown_deadline = None
            self._warning_fired = False
            ok, err = self._stop_fn()
        if not ok:
            logger.warning("Ollama go-to-sleep stop failed: %s", err)
        self._notify_state_observers()
        return ok, err

    def poll(self, now: float | None = None) -> None:
        """Evaluate warning and shutdown deadlines (call from a timer thread or tests)."""
        t = time.time() if now is None else now
        warning_callbacks: list[WarningListener] = []
        should_stop = False
        epoch_snapshot: int | None = None
        with self._lock:
            if self._refcount > 0 or not self._idle_enabled:
                return
            if self._shutdown_deadline is None:
                return
            warn_at = self._shutdown_deadline - self._warn
            if t >= warn_at and not self._warning_fired:
                self._warning_fired = True
                warning_callbacks = list(self._warning_listeners)
            if t >= self._shutdown_deadline:
                epoch_snapshot = self._idle_epoch
                self._shutdown_deadline = None
                self._warning_fired = False
                should_stop = True

        for cb in warning_callbacks:
            try:
                cb()
            except Exception:
                logger.exception("Ollama idle warning listener failed")

        if should_stop:
            assert epoch_snapshot is not None
            # Hold the lock across ``_stop_fn`` so ``begin_request`` cannot bump
            # refcount/epoch between the last check and the sidecar stop (HTTP may
            # block for tens of seconds; new callers wait until stop returns).
            # Never call ``_notify_state_observers`` while holding ``_lock``: listeners
            # may call ``sse_public_state()`` which re-acquires the same non-reentrant lock.
            skip_stop = False
            ok, err = True, None
            with self._lock:
                if self._refcount > 0 or self._idle_epoch != epoch_snapshot:
                    skip_stop = True
                else:
                    ok, err = self._stop_fn()
            if skip_stop:
                self._notify_state_observers()
                return
            if not ok:
                logger.warning("Ollama idle shutdown stop failed: %s", err)
            self._notify_state_observers()
            return

        if warning_callbacks:
            self._notify_state_observers()
