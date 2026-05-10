"""Contracts between the service layer and persistence (framework-free)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class WordsRepositoryPort(Protocol):
    """Word persistence; concrete implementation e.g. SQLite."""

    def count_words(self) -> int:
        """Return the number of rows in ``words``."""

    def ids_in_lexicon(self, ids: Sequence[int]) -> set[int]:
        """Return the subset of ``ids`` that exist as ``words.id`` (empty ``ids`` → empty set)."""

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
