"""Minimal HTTP API to start, stop, and inspect the Ollama Compose service container."""

from __future__ import annotations

import logging
import os
import socket
from typing import Any

import docker
from docker.errors import DockerException, NotFound
from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)

SIDECAR_TOKEN_HEADER = "X-Sidecar-Token"
OLLAMA_SERVICE_LABEL = "com.docker.compose.service"
OLLAMA_SERVICE_VALUE = "ollama"

_docker_client_singleton: docker.DockerClient | None = None


def _require_auth() -> tuple[Any, int] | None:
    secret = (os.environ.get("SIDECAR_SHARED_SECRET") or "").strip()
    if not secret:
        return None
    token = request.headers.get(SIDECAR_TOKEN_HEADER, "")
    if token != secret:
        return (
            jsonify(error="unauthorized", detail="Missing or invalid X-Sidecar-Token"),
            401,
        )
    return None


def _docker_client() -> docker.DockerClient:
    """Return a process-wide Docker client (one connection pool per gunicorn worker)."""
    global _docker_client_singleton
    if _docker_client_singleton is None:
        _docker_client_singleton = docker.from_env()
    return _docker_client_singleton


def _self_container(client: docker.DockerClient) -> docker.models.containers.Container | None:
    hostname = socket.gethostname()
    try:
        return client.containers.get(hostname)
    except NotFound:
        return None
    except DockerException:
        logger.exception("Failed to resolve self container by hostname")
        return None


def _find_ollama_container(client: docker.DockerClient) -> docker.models.containers.Container | None:
    """Pick the Ollama container that shares a Compose network with this sidecar."""
    self_c = _self_container(client)
    self_net_ids: set[str] = set()
    if self_c is not None:
        self_c.reload()
        nets = self_c.attrs.get("NetworkSettings", {}).get("Networks") or {}
        self_net_ids = set(nets.keys())

    label_filter = f"{OLLAMA_SERVICE_LABEL}={OLLAMA_SERVICE_VALUE}"
    candidates = client.containers.list(all=True, filters={"label": [label_filter]})

    if not candidates:
        return None

    if self_net_ids:
        for c in candidates:
            c.reload()
            nets = c.attrs.get("NetworkSettings", {}).get("Networks") or {}
            if self_net_ids.intersection(nets.keys()):
                return c

    project = (os.environ.get("DOCKER_COMPOSE_PROJECT") or "").strip()
    if project:
        for c in candidates:
            labels = c.labels or {}
            if labels.get("com.docker.compose.project") == project:
                return c

    if len(candidates) == 1:
        return candidates[0]

    return None


def _container_summary(c: docker.models.containers.Container) -> dict[str, Any]:
    c.reload()
    state = c.status or "unknown"
    return {
        "id": c.id,
        "name": c.name,
        "state": state,
        "labels": {
            "com.docker.compose.project": (c.labels or {}).get("com.docker.compose.project"),
            "com.docker.compose.service": (c.labels or {}).get("com.docker.compose.service"),
        },
    }


def _get_ollama_or_error(
    *,
    log_context: str,
) -> tuple[docker.models.containers.Container | None, tuple[Any, int] | None]:
    """Resolve the Ollama container or return (None, (json_body, status_code))."""
    try:
        client = _docker_client()
    except DockerException as e:
        return None, (jsonify(error="docker_unavailable", detail=str(e)), 503)

    try:
        c = _find_ollama_container(client)
    except DockerException as e:
        logger.exception("Docker API error during %s", log_context)
        return None, (jsonify(error="docker_error", detail=str(e)), 502)

    if c is None:
        return None, (jsonify(error="not_found", detail="No matching Ollama container found"), 404)

    return c, None


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health() -> tuple[Any, int]:
        return jsonify(ok=True), 200

    @app.before_request
    def _auth() -> tuple[Any, int] | None:
        if request.path == "/health":
            return None
        return _require_auth()

    @app.get("/ollama/inspect")
    def inspect_ollama() -> tuple[Any, int]:
        c, err = _get_ollama_or_error(log_context="inspect")
        if err is not None:
            return err
        assert c is not None
        return jsonify(ollama=_container_summary(c)), 200

    @app.post("/ollama/start")
    def start_ollama() -> tuple[Any, int]:
        """Start the Ollama container if it is not already running.

        Idempotent: duplicate ``POST`` while ``running`` returns 200 with ``noop: true``.
        """
        c, err = _get_ollama_or_error(log_context="start")
        if err is not None:
            return err
        assert c is not None

        try:
            c.reload()
            if c.status == "running":
                return jsonify(ok=True, ollama=_container_summary(c), noop=True), 200
            c.start()
            c.reload()
        except DockerException as e:
            logger.exception("Failed to start Ollama container")
            return jsonify(error="start_failed", detail=str(e)), 502

        return jsonify(ok=True, ollama=_container_summary(c)), 200

    @app.post("/ollama/stop")
    def stop_ollama() -> tuple[Any, int]:
        """Stop the Ollama container if it is running or paused.

        Idempotent: duplicate ``POST`` while already stopped returns 200 with ``noop: true``.
        """
        c, err = _get_ollama_or_error(log_context="stop")
        if err is not None:
            return err
        assert c is not None

        try:
            c.reload()
            if c.status not in ("running", "paused", "restarting"):
                return jsonify(ok=True, ollama=_container_summary(c), noop=True), 200
            c.stop(timeout=30)
            c.reload()
        except DockerException as e:
            logger.exception("Failed to stop Ollama container")
            return jsonify(error="stop_failed", detail=str(e)), 502

        return jsonify(ok=True, ollama=_container_summary(c)), 200

    return app


app = create_app()
