"""Shared vocabulary for CEFR levels and list-query sentinels."""

from __future__ import annotations

CEFR_LEVELS_ORDERED: tuple[str, ...] = ("A1", "A2", "B1", "B2", "C1", "C2")

ALLOWED_CEFR_LEVELS: frozenset[str] = frozenset(CEFR_LEVELS_ORDERED)

# ``GET /api/words?cefr_level=__none__`` matches rows where ``cefr_level`` IS NULL.
QUERY_CEFR_NONE = "__none__"
