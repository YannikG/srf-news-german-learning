"""Tests for Ollama idle shutdown, warning hook, cancel, and go-to-sleep."""

from __future__ import annotations

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
    ("path", "payload_key"),
    [
        ("/api/ollama/cancel-idle-shutdown", "ok"),
        ("/api/ollama/go-to-sleep", "ok"),
    ],
)
def test_ollama_routes_need_sidecar_for_go_to_sleep_only(
    tmp_path_factory: pytest.TempPathFactory,
    path: str,
    payload_key: str,
) -> None:
    app = _db_app(tmp_path_factory)
    client = app.test_client()
    response = client.post(path)
    if path.endswith("go-to-sleep"):
        assert response.status_code == 503
        data = response.get_json()
        assert data is not None
        assert data.get("error") == "sidecar_not_configured"
    else:
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert data.get(payload_key) is True


def test_go_to_sleep_calls_sidecar_when_configured(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str | None]] = []

    def fake_stop(base: str, secret: str | None) -> tuple[bool, str | None]:
        calls.append((base, secret))
        return True, None

    import app as app_root

    monkeypatch.setattr(app_root, "post_ollama_stop", fake_stop)

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

    import app as app_root

    monkeypatch.setattr(app_root, "post_ollama_stop", fake_stop)

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


def test_app_registers_idle_service(tmp_path_factory: pytest.TempPathFactory) -> None:
    app = _db_app(tmp_path_factory)
    ext = app.extensions.get(OLLAMA_IDLE_SERVICE_KEY)
    assert isinstance(ext, OllamaIdleService)
    db = app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    assert isinstance(db, SqlDatabase)
    db.dispose()
