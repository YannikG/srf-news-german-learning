"""NewsAPI.org HTTP client, Pydantic models, and article mapping."""

from __future__ import annotations

from .client import NewsApiClient, NewsApiClientError
from .mapping import map_newsapi_article_to_app_db_fields
from .models import NewsApiArticle, NewsApiResponse, NewsApiSource
from .settings import NewsApiSettings

__all__ = [
    "NewsApiArticle",
    "NewsApiClient",
    "NewsApiClientError",
    "NewsApiResponse",
    "NewsApiSettings",
    "NewsApiSource",
    "map_newsapi_article_to_app_db_fields",
]
