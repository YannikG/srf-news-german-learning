"""Wires the dictionary service and its repository (single composition root for the feature)."""

from __future__ import annotations

from ..persistence import SqlDatabase
from .repository import SqliteWordsRepository
from .service import WordsService


def build_words_service(db: SqlDatabase) -> WordsService:
    """Return a ``WordsService`` backed by a SQLite repository for the given database."""
    return WordsService(SqliteWordsRepository(db))
