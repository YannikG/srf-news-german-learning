"""Dünne REST-Routen für ``/api/words``."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request

from ..persistence import SQL_DATABASE_EXTENSION_KEY
from ..persistence.sqlite_db import SqlDatabase
from .factory import build_words_service
from .service import WordServiceError, WordsService

words_bp = Blueprint("words", __name__)


@words_bp.errorhandler(WordServiceError)
def _word_service_error(e: WordServiceError) -> tuple[Response, int]:
    return jsonify(error=e.message), e.status_code


def _words_service() -> WordsService:
    db = current_app.extensions.get(SQL_DATABASE_EXTENSION_KEY)
    if not isinstance(db, SqlDatabase):
        raise RuntimeError(
            "sql_database extension missing or wrong type; "
            "ensure DATABASE_PATH is set in create_app.",
        )
    return build_words_service(db)


@words_bp.get("/words")
def list_words() -> tuple[Response, int]:
    category = None if "category" not in request.args else request.args.get("category", "")
    items = _words_service().list_words(category=category)
    return jsonify(items), 200


@words_bp.post("/words")
def create_word() -> tuple[Response, int]:
    body: Any = request.get_json(silent=True)
    row = _words_service().create_word(body)
    return jsonify(row), 201


@words_bp.get("/words/<int:word_id>")
def get_word(word_id: int) -> tuple[Response, int]:
    row = _words_service().get_word(word_id)
    return jsonify(row), 200


@words_bp.patch("/words/<int:word_id>")
def patch_word(word_id: int) -> tuple[Response, int]:
    body: Any = request.get_json(silent=True)
    row = _words_service().patch_word(word_id, body)
    return jsonify(row), 200


@words_bp.delete("/words/<int:word_id>")
def delete_word(word_id: int) -> tuple[str, int]:
    _words_service().delete_word(word_id)
    return "", 204
