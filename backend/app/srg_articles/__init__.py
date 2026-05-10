"""SRGSSR Articles API v2: response shapes, mapping toward ``app.db`` columns, sanitizing."""

from __future__ import annotations

from .client import SrgArticlesApiClient, SrgArticlesApiError
from .mapping import map_article_to_app_db_fields
from .models import ArticleListPage, ArticleRecord
from .sanitize import strip_markdown_images
from .settings import SrgArticlesApiSettings

__all__ = [
    "ArticleListPage",
    "ArticleRecord",
    "SrgArticlesApiClient",
    "SrgArticlesApiError",
    "SrgArticlesApiSettings",
    "map_article_to_app_db_fields",
    "strip_markdown_images",
]
