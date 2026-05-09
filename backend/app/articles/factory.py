"""Wires the articles service and its repository."""

from __future__ import annotations

from ..persistence import SqlDatabase
from .repository import SqliteArticlesRepository
from .service import ArticlesService


def build_articles_service(db: SqlDatabase) -> ArticlesService:
    """Return an ``ArticlesService`` backed by SQLite for the given database."""
    return ArticlesService(SqliteArticlesRepository(db))
