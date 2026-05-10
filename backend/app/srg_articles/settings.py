"""Environment-backed settings for the SRGSSR Articles API v2 HTTP client."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ARTICLES_BASE_URL = "https://api.srgssr.ch/srgssr-articles/v2"
DEFAULT_ARTICLES_USER_AGENT = "srf-news-german-learning"


class SrgArticlesApiSettings(BaseSettings):
    """Base URL and User-Agent for authenticated ``GET …/articles`` calls."""

    model_config = SettingsConfigDict(extra="ignore")

    base_url: str = Field(
        default=DEFAULT_ARTICLES_BASE_URL,
        validation_alias="SRGSSR_ARTICLES_BASE_URL",
    )
    user_agent: str = Field(
        default=DEFAULT_ARTICLES_USER_AGENT,
        validation_alias="SRGSSR_ARTICLES_USER_AGENT",
    )
