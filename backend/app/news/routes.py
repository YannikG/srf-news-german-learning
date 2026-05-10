"""REST handler for ``POST /api/news/refresh``."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, jsonify
from pydantic import ValidationError

from .factory import build_default_news_refresh_service
from .service import NewsRefreshError, NewsRefreshService

NEWS_REFRESH_SERVICE_CONFIG_KEY = "NEWS_REFRESH_SERVICE"
NEWS_REFRESH_SERVICE_EXT_KEY = "news_refresh_service"

news_bp = Blueprint("news", __name__)


def _news_refresh_service() -> NewsRefreshService:
    override = current_app.config.get(NEWS_REFRESH_SERVICE_CONFIG_KEY)
    if override is not None:
        return override  # type: ignore[no-any-return]
    cached = current_app.extensions.get(NEWS_REFRESH_SERVICE_EXT_KEY)
    if cached is None:
        try:
            cached = build_default_news_refresh_service(current_app)
        except ValidationError as exc:
            raise NewsRefreshError(
                "SRG OAuth is not configured: set SRGSSR_CONSUMER_KEY and "
                "SRGSSR_CONSUMER_SECRET in the environment.",
                503,
                code="oauth_not_configured",
            ) from exc
        current_app.extensions[NEWS_REFRESH_SERVICE_EXT_KEY] = cached
    return cached  # type: ignore[no-any-return]


@news_bp.post("/news/refresh")
def post_news_refresh() -> tuple[Response, int]:
    """Trigger an SRG articles fetch when outside the post-success cooldown window."""
    try:
        payload = _news_refresh_service().refresh()
    except NewsRefreshError as exc:
        body: dict[str, object] = {"error": exc.message}
        if exc.code:
            body["code"] = exc.code
        return jsonify(body), exc.status_code
    return jsonify(payload), 200
