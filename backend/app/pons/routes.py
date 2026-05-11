"""REST handler for ``GET /api/external/pons/dictionary`` (on-demand proxy)."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify, request

from .client import (
    ALLOWED_DICTIONARIES,
    PonsDictionaryClient,
    PonsDictionaryError,
)

pons_bp = Blueprint("pons", __name__)


def _pons_secret() -> str:
    raw = current_app.config.get("PONS_API_SECRET")
    return str(raw).strip() if raw else ""


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
        l_param = "deen"

    if l_param not in ALLOWED_DICTIONARIES:
        allowed = ", ".join(sorted(ALLOWED_DICTIONARIES))
        return jsonify(error=f"dictionary 'l' must be one of: {allowed}"), 400

    client = PonsDictionaryClient(api_secret=secret)
    try:
        result = client.lookup(q, l_param)
    except PonsDictionaryError as exc:
        return jsonify(error=exc.message), exc.status_code
    finally:
        client.close()

    return jsonify(hits=result.hits), 200
