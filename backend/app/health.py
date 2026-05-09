"""Health endpoint blueprint.

Mounted by ``create_app`` under the ``/api`` prefix, so the route surface is
``GET /api/health``. The blueprint itself stays prefix-agnostic so the factory
controls routing layout.
"""

from __future__ import annotations

from flask import Blueprint, Response, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health() -> tuple[Response, int]:
    return jsonify(ok=True), 200
