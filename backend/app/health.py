"""Health endpoint blueprint.

Mounted by ``create_app`` under the ``/api`` prefix, so the route surface is
``GET /api/health``. The blueprint itself stays prefix-agnostic so the factory
controls routing layout.
"""

from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify

from .sidecar.client import probe_sidecar_inspect

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health() -> tuple[Response, int]:
    payload: dict = {"ok": True}
    raw_base = current_app.config.get("SIDECAR_BASE_URL")
    base = str(raw_base or "").strip()
    if base:
        secret = current_app.config.get("SIDECAR_SHARED_SECRET")
        secret_str = secret if isinstance(secret, str) else ""
        ok, err, ollama_public = probe_sidecar_inspect(base, secret_str or None)
        if ok:
            sc: dict = {"status": "ok"}
            if ollama_public:
                sc["ollama"] = ollama_public
            payload["sidecar"] = sc
        else:
            payload["sidecar"] = {"status": "error", "detail": err}
    return jsonify(payload), 200
