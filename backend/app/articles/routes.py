"""REST handlers for ``/api/articles`` (read-only, DB-backed)."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, Response, current_app, jsonify, request

from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from .factory import build_articles_service
from .service import ArticleServiceError, ArticlesService
from .simplify_factory import build_article_simplify_service
from .simplify_service import ArticleSimplifyServiceError

articles_bp = Blueprint("articles", __name__)


@articles_bp.errorhandler(ArticleServiceError)
def _article_service_error(e: ArticleServiceError) -> tuple[Response, int]:
    return jsonify(error=e.message), e.status_code


@articles_bp.errorhandler(ArticleSimplifyServiceError)
def _article_simplify_service_error(e: ArticleSimplifyServiceError) -> tuple[Response, int]:
    return jsonify(error=e.message), e.status_code


def _articles_service() -> ArticlesService:
    db = current_app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(db, SqlDatabase):
        raise RuntimeError(
            "sql_database extension missing or wrong type; "
            "ensure DATABASE_PATH is set in create_app.",
        )
    return build_articles_service(db)


def _parse_iso_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise ArticleServiceError("date must be YYYY-MM-DD", 400) from exc


def _parse_limit(raw: str | None, *, default: int = 20, cap: int = 100) -> int:
    if raw is None or raw == "":
        return default
    try:
        n = int(raw)
    except ValueError as exc:
        raise ArticleServiceError("limit must be an integer", 400) from exc
    if n < 1 or n > cap:
        raise ArticleServiceError(f"limit must be between 1 and {cap}", 400)
    return n


@articles_bp.get("/articles")
def list_articles() -> tuple[Response, int]:
    filter_date: date | None = None
    if "date" in request.args and request.args.get("date", "") != "":
        filter_date = _parse_iso_date(request.args["date"])
    limit = _parse_limit(request.args.get("limit"))
    cursor_token = request.args.get("cursor")
    raw_q = request.args.get("q")
    if raw_q is None:
        search_query = None
    else:
        stripped = raw_q.strip()
        search_query = stripped if stripped else None
    payload = _articles_service().list_articles(
        filter_date=filter_date,
        limit=limit,
        cursor_token=cursor_token,
        search_query=search_query,
    )
    return jsonify(payload), 200


@articles_bp.get("/articles/<int:article_id>")
def get_article(article_id: int) -> tuple[Response, int]:
    row = _articles_service().get_article(article_id)
    return jsonify(row), 200


@articles_bp.post("/articles/<int:article_id>/simplify")
def post_simplify_article(article_id: int) -> tuple[Response, int]:
    """Run LLM simplify with streaming SSE events (``llm_chunk``, ``llm_done``)."""
    body = request.get_json(silent=True) or {}
    raw_cefr = body.get("cefr_level")
    if not isinstance(raw_cefr, str) or not raw_cefr.strip():
        return jsonify(error="cefr_level is required as a non-empty string"), 400
    svc = build_article_simplify_service(current_app)
    payload = svc.simplify_article(article_id, raw_cefr)
    return jsonify(payload), 200
