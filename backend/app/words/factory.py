"""Zusammenbau von Wörterbuch-Service und Repository (explizite Wiring-Stelle)."""

from __future__ import annotations

from ..persistence import SqlDatabase
from .repository import SqliteWordsRepository
from .service import WordsService


def build_words_service(db: SqlDatabase) -> WordsService:
    """Liefert einen ``WordsService`` mit SQLite-Repository für die gegebene Datenbank."""
    return WordsService(SqliteWordsRepository(db))
