"""Tests for Ollama idle shutdown, warning hook, cancel, and go-to-sleep."""

from __future__ import annotations

import threading
from datetime import timedelta

import pytest
from freezegun import freeze_time

from app import create_app
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
    }
    cfg.update(extra_config)
    application = create_app(cfg)
    return application


def test_parallel_requests_prevent_idle_shutdown() -> None:
    stops: list[int] = []

    def stop() -> tuple[bool, str | None]:
        stops.append(1)
        return True, None

    svc = OllamaIdleService(
        idle_shutdown_seconds=600,
        warning_seconds=60,
        stop_fn=stop,
        idle_enabled=True,
    )
    with freeze_time("2020-01-01 00:00:00") as frozen:
        svc.begin_request()
        svc.begin_request()
        svc.end_request()
        frozen.tick(timedelta(seconds=700))
        svc.poll()
        assert stops == []
        svc.end_request()
        frozen.tick(timedelta(seconds=700))
        svc.poll()
    assert stops == [1]


def test_warning_then_shutdown_with_freezegun() -> None:
    warnings: list[int] = []
    stops: list[int] = []

    def stop() -> tuple[bool, str | None]:
        stops.append(1)
        return True, None

    svc = OllamaIdleService(
        idle_shutdown_seconds=600,
        warning_seconds=60,
        stop_fn=stop,
        idle_enabled=True,
    )
    svc.add_warning_listener(lambda: warnings.append(1))

    with freeze_time("2020-01-01 00:00:00") as frozen:
        svc.begin_request()
        svc.end_request()
        frozen.tick(timedelta(seconds=539))
        svc.poll()
        assert warnings == []
        frozen.tick(timedelta(seconds=1))
        svc.poll()
        assert warnings == [1]
        frozen.tick(timedelta(seconds=59))
        svc.poll()
        assert stops == []
        frozen.tick(timedelta(seconds=1))
        svc.poll()
        assert stops == [1]


def test_cancel_prevents_shutdown() -> None:
    stops: list[int] = []

    def stop() -> tuple[bool, str | None]:
        stops.append(1)
        return True, None

    svc = OllamaIdleService(
        idle_shutdown_seconds=600,
        warning_seconds=60,
        stop_fn=stop,
        idle_enabled=True,
    )
    with freeze_time("2020-01-01 00:00:00") as frozen:
        svc.begin_request()
        svc.end_request()
        frozen.tick(timedelta(seconds=540))
        svc.poll()
        svc.cancel_idle_shutdown()
        frozen.tick(timedelta(seconds=200))
        svc.poll()
    assert stops == []


def test_negative_warning_seconds_rejected() -> None:
    def stop() -> tuple[bool, str | None]:
        return True, None

    with pytest.raises(ValueError, match="warning_seconds"):
        OllamaIdleService(
            idle_shutdown_seconds=10,
            warning_seconds=-1,
            stop_fn=stop,
            idle_enabled=True,
        )


def test_begin_blocks_until_slow_idle_stop_finishes() -> None:
    """Idle ``poll`` holds the service lock across ``stop_fn``; ``begin_request`` waits."""
    import time

    entered = threading.Event()
    release_stop = threading.Event()
    stops: list[int] = []

    def stop() -> tuple[bool, str | None]:
        entered.set()
        assert release_stop.wait(timeout=5)
        stops.append(1)
        return True, None

    svc = OllamaIdleService(
        idle_shutdown_seconds=0.15,
        warning_seconds=0.0,
        stop_fn=stop,
        idle_enabled=True,
    )
    svc.begin_request()
    svc.end_request()
    time.sleep(0.2)
    poller = threading.Thread(target=svc.poll)
    poller.start()
    assert entered.wait(timeout=5)
    waiter = threading.Thread(target=svc.begin_request)
    waiter.start()
    time.sleep(0.02)
    release_stop.set()
    poller.join(timeout=5)
    waiter.join(timeout=5)
    assert stops == [1]


def test_go_to_sleep_hard_stop_while_refcount_positive() -> None:
    stops: list[int] = []

    def stop() -> tuple[bool, str | None]:
        stops.append(1)
        return True, None

    svc = OllamaIdleService(
        idle_shutdown_seconds=600,
        warning_seconds=60,
        stop_fn=stop,
        idle_enabled=True,
    )
    svc.begin_request()
    ok, err = svc.go_to_sleep()
    assert ok is True
    assert err is None
    assert stops == [1]


@pytest.mark.parametrize(
    ("path", "expect_ok_without_sidecar"),
    [
        ("/api/ollama/cancel-idle-shutdown", True),
        ("/api/ollama/go-to-sleep", False),
        ("/api/ollama/start", False),
    ],
)
def test_ollama_routes_sidecar_requirements_without_sidecar_url(
    tmp_path_factory: pytest.TempPathFactory,
    path: str,
    expect_ok_without_sidecar: bool,
) -> None:
    app = _db_app(tmp_path_factory)
    client = app.test_client()
    response = client.post(path)
    if expect_ok_without_sidecar:
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert data.get("ok") is True
    else:
        assert response.status_code == 503
        data = response.get_json()
        assert data is not None
        assert data.get("error") == "sidecar_not_configured"


def test_start_ollama_calls_sidecar_when_configured(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_start(base: str, secret: str | None) -> tuple[bool, str | None]:
        calls.append((base, secret))
        return True, None

    monkeypatch.setattr("app.ollama.routes.post_ollama_start", fake_start)

    app = _db_app(
        tmp_path_factory,
        SIDECAR_BASE_URL="http://sidecar:8090",
        SIDECAR_SHARED_SECRET="secret",
    )
    client = app.test_client()
    response = client.post("/api/ollama/start")
    assert response.status_code == 200
    assert calls == [("http://sidecar:8090", "secret")]


def test_start_ollama_propagates_start_failure(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_start(_base: str, _secret: str | None) -> tuple[bool, str | None]:
        return False, "no docker"

    monkeypatch.setattr("app.ollama.routes.post_ollama_start", fake_start)

    app = _db_app(
        tmp_path_factory,
        SIDECAR_BASE_URL="http://sidecar:8090",
        SIDECAR_SHARED_SECRET="x",
    )
    client = app.test_client()
    response = client.post("/api/ollama/start")
    assert response.status_code == 502
    data = response.get_json()
    assert data is not None
    assert data.get("detail") == "no docker"


def test_go_to_sleep_calls_sidecar_when_configured(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_stop(base: str, secret: str | None) -> tuple[bool, str | None]:
        calls.append((base, secret))
        return True, None

    monkeypatch.setattr("app.bootstrap.ollama_events.post_ollama_stop", fake_stop)

    app = _db_app(
        tmp_path_factory,
        SIDECAR_BASE_URL="http://sidecar:8090",
        SIDECAR_SHARED_SECRET="secret",
    )
    client = app.test_client()
    response = client.post("/api/ollama/go-to-sleep")
    assert response.status_code == 200
    assert calls == [("http://sidecar:8090", "secret")]


def test_go_to_sleep_propagates_stop_failure(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_stop(_base: str, _secret: str | None) -> tuple[bool, str | None]:
        return False, "boom"

    monkeypatch.setattr("app.bootstrap.ollama_events.post_ollama_stop", fake_stop)

    app = _db_app(
        tmp_path_factory,
        SIDECAR_BASE_URL="http://sidecar:8090",
        SIDECAR_SHARED_SECRET="x",
    )
    client = app.test_client()
    response = client.post("/api/ollama/go-to-sleep")
    assert response.status_code == 502
    data = response.get_json()
    assert data is not None
    assert data.get("detail") == "boom"


def test_normalize_idle_clamps_warn_to_idle(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    app = _db_app(
        tmp_path_factory,
        OLLAMA_IDLE_SHUTDOWN_SECONDS=40,
        OLLAMA_SHUTDOWN_WARNING_SECONDS=999,
    )
    assert app.config["OLLAMA_IDLE_SHUTDOWN_SECONDS"] == 40
    assert app.config["OLLAMA_SHUTDOWN_WARNING_SECONDS"] == 40


def test_normalize_ollama_idle_invalid_strings_use_defaults(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    app = _db_app(
        tmp_path_factory,
        OLLAMA_IDLE_SHUTDOWN_SECONDS="nope",
        OLLAMA_SHUTDOWN_WARNING_SECONDS="x",
    )
    assert app.config["OLLAMA_IDLE_SHUTDOWN_SECONDS"] == 600
    assert app.config["OLLAMA_SHUTDOWN_WARNING_SECONDS"] == 60


def test_normalize_zero_idle_becomes_one(tmp_path_factory: pytest.TempPathFactory) -> None:
    app = _db_app(tmp_path_factory, OLLAMA_IDLE_SHUTDOWN_SECONDS=0)
    assert app.config["OLLAMA_IDLE_SHUTDOWN_SECONDS"] == 1


def test_app_registers_idle_service(tmp_path_factory: pytest.TempPathFactory) -> None:
    app = _db_app(tmp_path_factory)
    ext = app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    assert isinstance(ext, OllamaIdleService)
    db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    assert isinstance(db, SqlDatabase)
    db.dispose()
