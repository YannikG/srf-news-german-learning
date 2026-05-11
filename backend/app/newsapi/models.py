"""Pydantic models for NewsAPI.org ``/v2/everything`` and ``/v2/top-headlines`` responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

_MODEL_CFG = ConfigDict(extra="ignore", populate_by_name=True)


class NewsApiSource(BaseModel):
    """``source`` object embedded in each article."""

    model_config = _MODEL_CFG

    id: str | None = None
    name: str = ""


class NewsApiArticle(BaseModel):
    """Single article returned in the ``articles`` array."""

    model_config = _MODEL_CFG

    source: NewsApiSource = Field(default_factory=NewsApiSource)
    author: str | None = None
    title: str | None = None
    description: str | None = None
    url: str | None = None
    url_to_image: str | None = Field(default=None, alias="urlToImage")
    published_at: str | None = Field(default=None, alias="publishedAt")
    content: str | None = None


class NewsApiResponse(BaseModel):
    """Top-level response from ``/v2/everything`` or ``/v2/top-headlines``."""

    model_config = _MODEL_CFG

    status: str = ""
    total_results: int = Field(default=0, alias="totalResults")
    articles: list[NewsApiArticle] = Field(default_factory=list)
