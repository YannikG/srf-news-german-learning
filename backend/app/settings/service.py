"""Validation and orchestration for application settings (singleton row)."""

from __future__ import annotations

from typing import Any

from .ports import SettingsRepositoryPort

ALLOWED_CEFR = frozenset({"A1", "A2", "B1", "B2", "C1", "C2"})
ALLOWED_TRANSLATION_LANGUAGES = frozenset({"en", "uk"})
RETRIEVAL_TOP_K_MAX = 500


class SettingsServiceError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SettingsService:
    def __init__(self, repo: SettingsRepositoryPort) -> None:
        self._repo = repo

    def get_settings(self) -> dict[str, Any]:
        row = self._repo.get_row()
        if row is None:
            raise SettingsServiceError("Settings row missing", 500)
        return _public_row(row)

    def patch_settings(self, body: Any) -> dict[str, Any]:
        data = _require_object(body)
        updates: dict[str, Any] = {}
        if "default_cefr" in data:
            updates["default_cefr"] = _parse_cefr(data["default_cefr"])
        if "translation_language" in data:
            updates["translation_language"] = _parse_translation_language(
                data["translation_language"],
            )
        if "retrieval_top_k" in data:
            updates["retrieval_top_k"] = _parse_retrieval_top_k(data["retrieval_top_k"])
        row = self._repo.update_row(updates)
        if row is None:
            raise SettingsServiceError("Settings row missing", 500)
        return _public_row(row)


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "default_cefr": row["default_cefr"],
        "translation_language": row["translation_language"],
        "retrieval_top_k": row["retrieval_top_k"],
    }


def _require_object(body: Any) -> dict[str, Any]:
    if body is None or not isinstance(body, dict):
        raise SettingsServiceError("JSON object body required", 400)
    return body


def _parse_cefr(raw: Any) -> str:
    if not isinstance(raw, str):
        raise SettingsServiceError("default_cefr must be a string", 400)
    val = raw.strip()
    if val not in ALLOWED_CEFR:
        allowed = ", ".join(sorted(ALLOWED_CEFR))
        raise SettingsServiceError(
            f"default_cefr must be one of: {allowed}",
            400,
        )
    return val


def _parse_translation_language(raw: Any) -> str:
    if not isinstance(raw, str):
        raise SettingsServiceError("translation_language must be a string", 400)
    val = raw.strip()
    if val not in ALLOWED_TRANSLATION_LANGUAGES:
        allowed = ", ".join(sorted(ALLOWED_TRANSLATION_LANGUAGES))
        raise SettingsServiceError(
            f"translation_language must be one of: {allowed}",
            400,
        )
    return val


def _parse_retrieval_top_k(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise SettingsServiceError("retrieval_top_k must be an integer or null", 400)
    if isinstance(raw, float):
        if not raw.is_integer():
            raise SettingsServiceError("retrieval_top_k must be a whole number", 400)
        raw = int(raw)
    if not isinstance(raw, int):
        raise SettingsServiceError("retrieval_top_k must be an integer or null", 400)
    if raw < 1:
        raise SettingsServiceError("retrieval_top_k must be at least 1", 400)
    if raw > RETRIEVAL_TOP_K_MAX:
        raise SettingsServiceError(
            f"retrieval_top_k must be at most {RETRIEVAL_TOP_K_MAX}",
            400,
        )
    return raw
