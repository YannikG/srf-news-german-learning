"""SRGSSR Articles API v2: response shapes, mapping toward ``app.db`` columns, sanitizing."""

from __future__ import annotations

from .mapping import map_article_to_app_db_fields
from .models import ArticleListPage, ArticleRecord
from .sanitize import strip_markdown_images

__all__ = [
    "ArticleListPage",
    "ArticleRecord",
    "map_article_to_app_db_fields",
    "strip_markdown_images",
]
