"""REST handlers for ``/api/settings`` (singleton configuration row)."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request

from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from .factory import build_settings_service
from .service import SettingsService, SettingsServiceError

settings_bp = Blueprint("settings", __name__)


@settings_bp.errorhandler(SettingsServiceError)
def _settings_service_error(e: SettingsServiceError) -> tuple[Response, int]:
    return jsonify(error=e.message), e.status_code


def _settings_service() -> SettingsService:
    db = current_app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(db, SqlDatabase):
        raise RuntimeError(
            "sql_database extension missing or wrong type; "
            "ensure DATABASE_PATH is set in create_app.",
        )
    return build_settings_service(db)


def _with_active_ingest_provider(row: dict[str, Any]) -> dict[str, Any]:
    """Merge read-only config derived fields (not stored in ``settings`` table)."""
    return {
        **row,
        "active_ingest_provider": str(current_app.config.get("NEWS_ACTIVE_PROVIDER") or "srgssr"),
    }


@settings_bp.get("/settings")
def get_settings() -> tuple[Response, int]:
    row = _settings_service().get_settings()
    return jsonify(_with_active_ingest_provider(row)), 200


@settings_bp.patch("/settings")
def patch_settings() -> tuple[Response, int]:
    body: Any = request.get_json(silent=True)
    row = _settings_service().patch_settings(body)
    return jsonify(_with_active_ingest_provider(row)), 200
