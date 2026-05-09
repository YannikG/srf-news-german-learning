"""Health endpoint blueprint.

Exposes ``GET /api/health`` for smoke tests and container health checks.
"""

from __future__ import annotations

from flask import Blueprint, Response, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health() -> tuple[Response, int]:
    return jsonify(ok=True), 200
