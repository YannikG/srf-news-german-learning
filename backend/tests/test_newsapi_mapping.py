"""Tests for map_newsapi_article_to_app_db_fields."""

from __future__ import annotations

from app.newsapi.mapping import map_newsapi_article_to_app_db_fields
from app.newsapi.models import NewsApiArticle, NewsApiSource


def _make_article(**overrides) -> NewsApiArticle:
    defaults = {
        "source": NewsApiSource(id="spiegel-online", name="Spiegel Online"),
        "author": "Max Mustermann",
        "title": "Schweizer Wirtschaft wächst",
        "description": "Starkes Wachstum im Q1.",
        "url": "https://example.com/article-1",
        "publishedAt": "2026-05-10T08:30:00Z",
        "content": "Vollständiger Artikelinhalt hier.",
    }
    defaults.update(overrides)
    return NewsApiArticle.model_validate(defaults)


def test_full_mapping() -> None:
    article = _make_article()
    row = map_newsapi_article_to_app_db_fields(article, language="de")

    assert row["external_id"] == "https://example.com/article-1"
    assert row["publisher"] == "Spiegel Online"
    assert row["provenance"] == "https://example.com/article-1"
    assert row["title"] == "Schweizer Wirtschaft wächst"
    assert row["lead"] == "Starkes Wachstum im Q1."
    assert "# Schweizer Wirtschaft wächst" in row["markdown_original"]
    assert "Starkes Wachstum im Q1." in row["markdown_original"]
    assert "Vollständiger Artikelinhalt hier." in row["markdown_original"]
    assert row["release_date"] == "2026-05-10T08:30:00Z"
    assert row["modification_date"] is None
    assert row["language"] == "de"


def test_missing_optional_fields() -> None:
    article = _make_article(
        author=None,
        description=None,
        content=None,
        urlToImage=None,
    )
    row = map_newsapi_article_to_app_db_fields(article)

    assert row["title"] == "Schweizer Wirtschaft wächst"
    assert row["lead"] is None
    assert row["markdown_original"] == "# Schweizer Wirtschaft wächst"
    assert row["language"] is None


def test_title_fallback_to_ohne_titel() -> None:
    article = _make_article(title=None)
    row = map_newsapi_article_to_app_db_fields(article)

    assert row["title"] == "Ohne Titel"
    assert row["markdown_original"].startswith("# Ohne Titel")


def test_empty_title_fallback() -> None:
    article = _make_article(title="   ")
    row = map_newsapi_article_to_app_db_fields(article)

    assert row["title"] == "Ohne Titel"


def test_language_passthrough() -> None:
    article = _make_article()
    row_de = map_newsapi_article_to_app_db_fields(article, language="de")
    row_en = map_newsapi_article_to_app_db_fields(article, language="en")
    row_none = map_newsapi_article_to_app_db_fields(article)

    assert row_de["language"] == "de"
    assert row_en["language"] == "en"
    assert row_none["language"] is None


def test_markdown_images_stripped() -> None:
    article = _make_article(
        content="Text vor Bild ![alt](https://img.example.com/photo.jpg) Text nach Bild",
    )
    row = map_newsapi_article_to_app_db_fields(article)

    assert "![" not in row["markdown_original"]
    assert "Text vor Bild" in row["markdown_original"]
    assert "Text nach Bild" in row["markdown_original"]


def test_external_id_is_url() -> None:
    article = _make_article(url="https://example.com/unique-article")
    row = map_newsapi_article_to_app_db_fields(article)

    assert row["external_id"] == "https://example.com/unique-article"
