"""Tests for NewsApiSettings validation (startup guards)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.newsapi.settings import NewsApiSettings


def test_everything_without_search_condition_raises() -> None:
    with pytest.raises(ValueError, match="at least one of"):
        NewsApiSettings(
            api_key="test-key",
            endpoint="everything",
            default_query="",
            default_domains="",
            default_sources="",
        )


def test_everything_with_query_passes() -> None:
    s = NewsApiSettings(
        api_key="test-key",
        endpoint="everything",
        default_query="Schweiz",
    )
    assert s.default_query == "Schweiz"
    assert s.endpoint == "everything"


def test_everything_with_domains_passes() -> None:
    s = NewsApiSettings(
        api_key="test-key",
        endpoint="everything",
        default_domains="srf.ch,nzz.ch",
    )
    assert s.default_domains == "srf.ch,nzz.ch"


def test_everything_with_sources_passes() -> None:
    s = NewsApiSettings(
        api_key="test-key",
        endpoint="everything",
        default_sources="spiegel-online",
    )
    assert s.default_sources == "spiegel-online"


def test_top_headlines_without_query_passes() -> None:
    s = NewsApiSettings(
        api_key="test-key",
        endpoint="top-headlines",
        default_query="",
        default_domains="",
        default_sources="",
    )
    assert s.endpoint == "top-headlines"


def test_invalid_endpoint_raises() -> None:
    with pytest.raises(ValueError, match="endpoint must be one of"):
        NewsApiSettings(api_key="test-key", endpoint="invalid")


def test_invalid_sort_by_raises() -> None:
    with pytest.raises(ValueError, match="sortBy must be one of"):
        NewsApiSettings(
            api_key="test-key",
            endpoint="top-headlines",
            default_sort_by="invalid",
        )


def test_page_size_bounds() -> None:
    with pytest.raises(ValueError, match="page_size must be between"):
        NewsApiSettings(
            api_key="test-key",
            endpoint="top-headlines",
            page_size=0,
        )
    with pytest.raises(ValueError, match="page_size must be between"):
        NewsApiSettings(
            api_key="test-key",
            endpoint="top-headlines",
            page_size=101,
        )


def test_whitespace_stripped() -> None:
    s = NewsApiSettings(
        api_key="  test-key  ",
        endpoint="  everything  ",
        default_query="  news  ",
    )
    assert s.api_key == "test-key"
    assert s.endpoint == "everything"
    assert s.default_query == "news"


def test_missing_api_key_raises() -> None:
    with pytest.raises((ValueError, ValidationError)):
        NewsApiSettings(endpoint="top-headlines")
