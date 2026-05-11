"""REST handler for ``GET /api/external/pons/dictionary`` (on-demand proxy)."""

from __future__ import annotations

import logging

from flask import Blueprint, Response, current_app, jsonify, request

from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from ..settings.factory import build_settings_service
from .client import (
    ALLOWED_DICTIONARIES,
    PonsDictionaryClient,
    PonsDictionaryError,
    _shared_pons_http,
)

logger = logging.getLogger(__name__)

TRANSLATION_LANGUAGE_TO_DICT: dict[str, str] = {
    "en": "deen",
    "uk": "deuk",
}

pons_bp = Blueprint("pons", __name__)


def _pons_secret() -> str:
    raw = current_app.config.get("PONS_API_SECRET")
    return str(raw).strip() if raw else ""


def _default_dictionary() -> str:
    """Derive the PONS dictionary key from the persisted ``translation_language`` setting."""
    db = current_app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if isinstance(db, SqlDatabase):
        try:
            row = build_settings_service(db).get_settings()
            lang = row.get("translation_language", "")
            if lang and lang in TRANSLATION_LANGUAGE_TO_DICT:
                return TRANSLATION_LANGUAGE_TO_DICT[lang]
        except Exception:
            logger.debug("Failed to read translation_language from settings", exc_info=True)
    return "deen"


@pons_bp.get("/external/pons/dictionary")
def pons_dictionary_lookup() -> tuple[Response, int]:
    secret = _pons_secret()
    if not secret:
        return jsonify(error="PONS integration not configured"), 503

    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify(error="query parameter 'q' is required"), 400

    l_param = (request.args.get("l") or "").strip().lower()

    if not l_param:
        l_param = _default_dictionary()

    if l_param not in ALLOWED_DICTIONARIES:
        allowed = ", ".join(sorted(ALLOWED_DICTIONARIES))
        return jsonify(error=f"dictionary 'l' must be one of: {allowed}"), 400

    client = PonsDictionaryClient(api_secret=secret, http_client=_shared_pons_http())
    try:
        result = client.lookup(q, l_param)
    except PonsDictionaryError as exc:
        return jsonify(error=exc.message), exc.status_code

    return jsonify(hits=result.hits), 200
