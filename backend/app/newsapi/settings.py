"""Environment-backed settings for the NewsAPI.org HTTP client."""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_BASE_URL = "https://newsapi.org"
DEFAULT_ENDPOINT = "everything"
DEFAULT_LANGUAGE = "de"
DEFAULT_COUNTRY = "de"
DEFAULT_SORT_BY = "publishedAt"
DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100

_ALLOWED_ENDPOINTS = frozenset({"everything", "top-headlines"})
_ALLOWED_SORT_BY = frozenset({"relevancy", "popularity", "publishedAt"})


class NewsApiSettings(BaseSettings):
    """API key, endpoint selection, and query defaults for NewsAPI.org calls."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    api_key: str = Field(validation_alias="NEWSAPI_API_KEY")

    base_url: str = Field(
        default=DEFAULT_BASE_URL,
        validation_alias="NEWSAPI_BASE_URL",
    )
    endpoint: str = Field(
        default=DEFAULT_ENDPOINT,
        validation_alias="NEWSAPI_ENDPOINT",
    )

    default_query: str = Field(
        default="",
        validation_alias="NEWSAPI_DEFAULT_QUERY",
    )
    default_domains: str = Field(
        default="",
        validation_alias="NEWSAPI_DOMAINS",
    )
    default_sources: str = Field(
        default="",
        validation_alias="NEWSAPI_SOURCES",
    )

    default_language: str = Field(
        default=DEFAULT_LANGUAGE,
        validation_alias="NEWSAPI_DEFAULT_LANGUAGE",
    )
    default_country: str = Field(
        default=DEFAULT_COUNTRY,
        validation_alias="NEWSAPI_DEFAULT_COUNTRY",
    )
    default_sort_by: str = Field(
        default=DEFAULT_SORT_BY,
        validation_alias="NEWSAPI_SORT_BY",
    )
    page_size: int = Field(
        default=DEFAULT_PAGE_SIZE,
        validation_alias="NEWSAPI_PAGE_SIZE",
    )

    @field_validator(
        "base_url",
        "endpoint",
        "default_query",
        "default_domains",
        "default_sources",
        "default_language",
        "default_country",
        "default_sort_by",
        "api_key",
        mode="before",
    )
    @classmethod
    def _strip_outer_ws(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("endpoint")
    @classmethod
    def _validate_endpoint(cls, v: str) -> str:
        lower = v.lower()
        if lower not in _ALLOWED_ENDPOINTS:
            allowed = ", ".join(sorted(_ALLOWED_ENDPOINTS))
            raise ValueError(f"endpoint must be one of: {allowed}. Got {v!r}.")
        return lower

    @field_validator("default_sort_by")
    @classmethod
    def _validate_sort_by(cls, v: str) -> str:
        if v not in _ALLOWED_SORT_BY:
            allowed = ", ".join(sorted(_ALLOWED_SORT_BY))
            raise ValueError(f"sortBy must be one of: {allowed}. Got {v!r}.")
        return v

    @field_validator("page_size")
    @classmethod
    def _validate_page_size(cls, v: int) -> int:
        if v < 1 or v > _MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {_MAX_PAGE_SIZE}. Got {v}.")
        return v

    @model_validator(mode="after")
    def _validate_everything_requires_search_condition(self) -> NewsApiSettings:
        if self.endpoint != "everything":
            return self
        q = self.default_query.strip()
        domains = self.default_domains.strip()
        sources = self.default_sources.strip()
        if not q and not domains and not sources:
            raise ValueError(
                "Endpoint 'everything' requires at least one of "
                "NEWSAPI_DEFAULT_QUERY, NEWSAPI_DOMAINS, or NEWSAPI_SOURCES "
                "to be set (non-empty). Without it, NewsAPI returns HTTP 400."
            )
        return self
