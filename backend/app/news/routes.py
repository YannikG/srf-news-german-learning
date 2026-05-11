"""REST handler for ``POST /api/news/refresh``."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify
from pydantic import ValidationError

from .errors import NewsRefreshError
from .factory import build_default_news_refresh_service
from .service import NewsRefreshService

NEWS_REFRESH_SERVICE_CONFIG_KEY = "NEWS_REFRESH_SERVICE"
NEWS_REFRESH_SERVICE_EXT_KEY = "news_refresh_service"

news_bp = Blueprint("news", __name__)

_SRGSSR_CONSUMER_ENV_FIELDS = frozenset({"SRGSSR_CONSUMER_KEY", "SRGSSR_CONSUMER_SECRET"})
_NEWSAPI_REQUIRED_ENV_FIELDS = frozenset({"NEWSAPI_API_KEY"})


def _is_only_missing_env_credentials(exc: ValidationError) -> tuple[bool, str]:
    """Detect missing-credentials ``ValidationError`` and return a provider hint.

    Returns ``(True, provider_hint)`` when all errors are ``type=missing`` and
    every missing field belongs to a single known provider's required env vars.
    """
    errors = exc.errors()
    if not errors:
        return False, ""
    missing_fields: set[str] = set()
    for err in errors:
        if err.get("type") != "missing":
            return False, ""
        loc = err.get("loc") or ()
        if not loc:
            return False, ""
        missing_fields.add(str(loc[0]))
    if missing_fields <= _SRGSSR_CONSUMER_ENV_FIELDS:
        return True, "srgssr"
    if missing_fields <= _NEWSAPI_REQUIRED_ENV_FIELDS:
        return True, "newsapi"
    return False, ""


_CREDENTIALS_MESSAGES: dict[str, tuple[str, str]] = {
    "srgssr": (
        "SRG OAuth is not configured: set SRGSSR_CONSUMER_KEY and "
        "SRGSSR_CONSUMER_SECRET in the environment.",
        "oauth_not_configured",
    ),
    "newsapi": (
        "NewsAPI is not configured: set NEWSAPI_API_KEY in the environment.",
        "newsapi_not_configured",
    ),
}


def _news_refresh_service() -> NewsRefreshService:
    override = current_app.config.get(NEWS_REFRESH_SERVICE_CONFIG_KEY)
    if override is not None:
        return override  # type: ignore[no-any-return]
    cached = current_app.extensions.get(NEWS_REFRESH_SERVICE_EXT_KEY)
    if cached is None:
        try:
            cached = build_default_news_refresh_service(current_app)
        except ValidationError as exc:
            is_creds, hint = _is_only_missing_env_credentials(exc)
            if is_creds and hint in _CREDENTIALS_MESSAGES:
                msg, code = _CREDENTIALS_MESSAGES[hint]
                raise NewsRefreshError(msg, 503, code=code) from exc
            raise
        current_app.extensions[NEWS_REFRESH_SERVICE_EXT_KEY] = cached
    return cached  # type: ignore[no-any-return]


@news_bp.post("/news/refresh")
def post_news_refresh() -> tuple[Response, int]:
    """Trigger an upstream articles fetch when outside the post-success cooldown window."""
    try:
        payload = _news_refresh_service().refresh()
    except NewsRefreshError as exc:
        body: dict[str, object] = {"error": exc.message}
        if exc.code:
            body["code"] = exc.code
        return jsonify(body), exc.status_code
    return jsonify(payload), 200
