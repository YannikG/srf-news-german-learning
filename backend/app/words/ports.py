"""Contracts between the service layer and persistence (framework-free)."""

from __future__ import annotations

from typing import Any, Protocol


class WordsRepositoryPort(Protocol):
    """Word persistence; concrete implementation e.g. SQLite."""

    def list(self, *, category: str | None = None) -> list[dict[str, Any]]: ...

    def get(self, word_id: int) -> dict[str, Any] | None: ...

    def create(
        self,
        *,
        german_label: str,
        category: str,
        difficulty: str,
        translation: str,
        cefr_level: str | None,
    ) -> dict[str, Any]: ...

    def update(self, word_id: int, fields: dict[str, Any]) -> dict[str, Any] | None: ...

    def delete(self, word_id: int) -> bool: ...
