"""Validierung und Orchestrierung für Wörterbuch-Operationen."""

from __future__ import annotations

from typing import Any

from .repository import WordsRepository

ALLOWED_DIFFICULTIES = frozenset({"Neu", "Schwer", "Mittel", "Leicht"})


class WordServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class WordsService:
    def __init__(self, repo: WordsRepository) -> None:
        self._repo = repo

    def list_words(self, *, category: str | None = None) -> list[dict[str, Any]]:
        return self._repo.list(category=category)

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
        cefr_level = _parse_cefr_optional(data.get("cefr_level"))
        return self._repo.create(
            german_label=german_label,
            category=category,
            difficulty=difficulty,
            translation=translation,
            cefr_level=cefr_level,
        )

    def patch_word(self, word_id: int, body: Any) -> dict[str, Any]:
        data = _require_object(body)
        if self._repo.get(word_id) is None:
            raise WordServiceError("Word not found", 404)
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
            updates["cefr_level"] = _parse_cefr_patch_value(data["cefr_level"])
        updated = self._repo.update(word_id, updates)
        assert updated is not None
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
    return val


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


def _parse_cefr_optional(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise WordServiceError("cefr_level must be a string or null", 400)
    s = raw.strip()
    return s or None


def _parse_cefr_patch_value(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise WordServiceError("cefr_level must be a string or null", 400)
    s = raw.strip()
    return s or None
