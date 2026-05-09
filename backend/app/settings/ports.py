"""Persistence contract for the singleton ``settings`` row (``id = 1``)."""

from __future__ import annotations

from typing import Any, Protocol


class SettingsRepositoryPort(Protocol):
    def get_row(self) -> dict[str, Any] | None:
        """Return the single settings row, or ``None`` if missing."""

    def update_row(self, fields: dict[str, Any]) -> dict[str, Any] | None:
        """Apply partial column updates for ``id = 1``; return row or ``None`` if missing."""
