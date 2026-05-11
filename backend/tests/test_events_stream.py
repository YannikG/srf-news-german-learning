"""Integration tests for GET /api/events/stream (SSE)."""

from __future__ import annotations

import threading
import time
from collections.abc import Generator

import httpx
import pytest
from werkzeug.serving import make_server

from app import create_app
from app.events.hub import SseHub
from app.ollama import OLLAMA_IDLE_SERVICE_KEY
from app.ollama.service import OllamaIdleService
from app.persistence import SQL_DATABASE_EXTENSION_KEY
from app.persistence.sqlite_db import SqlDatabase


def _db_app(tmp_path_factory: pytest.TempPathFactory, **extra_config):
    db_path = tmp_path_factory.mktemp("db") / "app.db"
    cfg = {
        "TESTING": True,
        "DATABASE_PATH": str(db_path),
        "OLLAMA_IDLE_SHUTDOWN_SECONDS": 600,
        "OLLAMA_SHUTDOWN_WARNING_SECONDS": 60,
        "OLLAMA_IDLE_START_POLL_THREAD": False,
        "NEWS_ACTIVE_PROVIDER": "srgssr",
    }
    cfg.update(extra_config)
    return create_app(cfg)


@pytest.fixture
def live_sse_app(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[tuple[str, object], None, None]:
    """HTTP server in a thread so SSE can be read concurrently with other clients."""
    # Non-empty side URL arms idle shutdown so ``poll`` can emit ``shutdown_warning``.
    app = _db_app(
        tmp_path_factory,
        SIDECAR_BASE_URL="http://127.0.0.1:59999",
    )
    httpd = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = httpd.server_address
        yield f"http://{host}:{port}", app
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
        if isinstance(db, SqlDatabase):
            db.dispose()


@pytest.fixture
def live_sse_app_short_idle(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[tuple[str, object], None, None]:
    """Like ``live_sse_app`` with short idle timing so ``poll`` hits the warning path."""
    app = _db_app(
        tmp_path_factory,
        SIDECAR_BASE_URL="http://127.0.0.1:59999",
        OLLAMA_IDLE_SHUTDOWN_SECONDS=3,
        OLLAMA_SHUTDOWN_WARNING_SECONDS=1,
    )
    httpd = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = httpd.server_address
        yield f"http://{host}:{port}", app
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
        if isinstance(db, SqlDatabase):
            db.dispose()


def test_events_stream_initial_ollama_state(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    app = _db_app(tmp_path_factory)
    client = app.test_client()
    resp = client.get("/api/events/stream", buffered=False)
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"
    first = next(iter(resp.response))
    text = first.decode() if isinstance(first, bytes) else first
    assert "event: ollama_state" in text
    assert '"idle_enabled"' in text
    db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    assert isinstance(db, SqlDatabase)
    db.dispose()


@pytest.mark.integration
def test_events_stream_receives_cancel_events(live_sse_app) -> None:
    base_url, _app = live_sse_app
    buf_holder: dict[str, bytes] = {"buf": b""}
    connected = threading.Event()
    saw_cancel = threading.Event()

    def reader() -> None:
        stop_at = time.monotonic() + 15.0
        with (
            httpx.Client(timeout=None) as client,
            client.stream("GET", f"{base_url}/api/events/stream") as resp,
        ):
            assert resp.status_code == 200
            for chunk in resp.iter_bytes():
                if time.monotonic() > stop_at:
                    break
                if not chunk:
                    continue
                buf_holder["buf"] += chunk
                connected.set()
                if b"shutdown_cancelled" in buf_holder["buf"]:
                    saw_cancel.set()
                if saw_cancel.is_set() and buf_holder["buf"].count(b"event: ollama_state") >= 2:
                    break

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    assert connected.wait(timeout=5)
    time.sleep(0.05)
    with httpx.Client(timeout=5.0) as poster:
        cancel = poster.post(f"{base_url}/api/ollama/cancel-idle-shutdown")
        assert cancel.status_code == 200
    assert saw_cancel.wait(timeout=5)
    th.join(timeout=5)
    raw = buf_holder["buf"].decode(errors="replace")
    cancel_pos = raw.find("shutdown_cancelled")
    state_after = raw.find("ollama_state", cancel_pos)
    assert cancel_pos != -1
    assert state_after != -1


@pytest.mark.integration
def test_events_stream_shutdown_warning_then_state(live_sse_app_short_idle) -> None:
    base_url, app = live_sse_app_short_idle
    svc = app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    assert isinstance(svc, OllamaIdleService)

    buf_holder: dict[str, bytes] = {"buf": b""}
    done = threading.Event()

    def reader() -> None:
        stop_at = time.monotonic() + 15.0
        with (
            httpx.Client(timeout=None) as client,
            client.stream("GET", f"{base_url}/api/events/stream") as resp,
        ):
            assert resp.status_code == 200
            for chunk in resp.iter_bytes():
                if time.monotonic() > stop_at:
                    break
                if not chunk:
                    continue
                buf_holder["buf"] += chunk
                if b"shutdown_warning" in buf_holder["buf"]:
                    done.set()
                    break

    def idle_sequence() -> None:
        time.sleep(0.2)
        svc.begin_request()
        svc.end_request()
        # warn_at = arm + (idle - warn) = arm + 2s
        time.sleep(2.1)
        svc.poll()

    th_reader = threading.Thread(target=reader, daemon=True)
    th_idle = threading.Thread(target=idle_sequence, daemon=True)
    th_reader.start()
    th_idle.start()
    assert done.wait(timeout=8)
    th_reader.join(timeout=5)
    th_idle.join(timeout=5)
    assert b"shutdown_warning" in buf_holder["buf"]
    assert b'"warning_seconds":1' in buf_holder["buf"]


def test_sse_hub_rejects_invalid_event_name() -> None:
    hub = SseHub()
    with pytest.raises(ValueError, match="invalid SSE event name"):
        hub.publish("bad\nname", {})
