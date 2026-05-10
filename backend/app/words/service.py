"""Validation and orchestration for dictionary (word) operations."""

from __future__ import annotations

from typing import Any

from .constants import ALLOWED_CEFR_LEVELS, QUERY_CEFR_NONE
from .ports import WordsRepositoryPort

ALLOWED_DIFFICULTIES = frozenset({"Neu", "Schwer", "Mittel", "Leicht"})


class WordServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class WordsService:
    def __init__(self, repo: WordsRepositoryPort) -> None:
        self._repo = repo

    def list_words(
        self,
        *,
        category: str | None = None,
        cefr_level: str | None = None,
    ) -> list[dict[str, Any]]:
        if cefr_level is not None:
            allowed_filter = cefr_level in ALLOWED_CEFR_LEVELS or cefr_level == QUERY_CEFR_NONE
            if not allowed_filter:
                raise WordServiceError(
                    "cefr_level filter must be one of: A1, A2, B1, B2, C1, C2, or __none__",
                    400,
                )
        return self._repo.list(category=category, cefr_level=cefr_level)

    def get_word(self, word_id: int) -> dict[str, Any]:
        row = self._repo.get(word_id)
        if row is None:
            raise WordServiceError("Word not found", 404)
        return row

    def create_word(self, body: Any) -> dict[str, Any]:
        data = _require_object(body)
        german_label = _non_empty_str(data, "german_label")
        category = _optional_str_field(data, "category", default="")
        translation = _optional_str_field(data, "translation", default="")
        difficulty = _parse_difficulty(data.get("difficulty", "Neu"))
        cefr_level = _parse_cefr_level(data.get("cefr_level"))
        return self._repo.create(
            german_label=german_label,
            category=category,
            difficulty=difficulty,
            translation=translation,
            cefr_level=cefr_level,
        )

    def patch_word(self, word_id: int, body: Any) -> dict[str, Any]:
        data = _require_object(body)
        updates: dict[str, Any] = {}
        if "german_label" in data:
            updates["german_label"] = _non_empty_str(data, "german_label")
        if "category" in data:
            updates["category"] = _plain_str(data, "category")
        if "translation" in data:
            updates["translation"] = _plain_str(data, "translation")
        if "difficulty" in data:
            updates["difficulty"] = _parse_difficulty(data["difficulty"])
        if "cefr_level" in data:
            updates["cefr_level"] = _parse_cefr_level(data["cefr_level"])
        updated = self._repo.update(word_id, updates)
        if updated is None:
            raise WordServiceError("Word not found", 404)
        return updated

    def delete_word(self, word_id: int) -> None:
        if not self._repo.delete(word_id):
            raise WordServiceError("Word not found", 404)


def _require_object(body: Any) -> dict[str, Any]:
    if body is None or not isinstance(body, dict):
        raise WordServiceError("JSON object body required", 400)
    return body


def _plain_str(data: dict[str, Any], field: str) -> str:
    val = data[field]
    if not isinstance(val, str):
        raise WordServiceError(f"{field} must be a string", 400)
    return val.strip()


def _optional_str_field(data: dict[str, Any], field: str, *, default: str) -> str:
    if field not in data:
        return default
    return _plain_str(data, field)


def _non_empty_str(data: dict[str, Any], field: str) -> str:
    if field not in data or data[field] is None:
        raise WordServiceError(f"{field} is required", 400)
    val = data[field]
    if not isinstance(val, str):
        raise WordServiceError(f"{field} must be a string", 400)
    stripped = val.strip()
    if not stripped:
        raise WordServiceError(f"{field} must not be empty", 400)
    return stripped


def _parse_difficulty(raw: Any) -> str:
    if not isinstance(raw, str):
        raise WordServiceError("difficulty must be a string", 400)
    if raw not in ALLOWED_DIFFICULTIES:
        raise WordServiceError(
            "difficulty must be one of: Neu, Schwer, Mittel, Leicht",
            400,
        )
    return raw


def _parse_cefr_level(raw: Any) -> str | None:
    """JSON ``null`` or empty string clears the level; otherwise must be a known CEFR code."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise WordServiceError("cefr_level must be a string or null", 400)
    s = raw.strip()
    if not s:
        return None
    if s not in ALLOWED_CEFR_LEVELS:
        raise WordServiceError(
            "cefr_level must be one of: A1, A2, B1, B2, C1, C2 or null/empty",
            400,
        )
    return s
