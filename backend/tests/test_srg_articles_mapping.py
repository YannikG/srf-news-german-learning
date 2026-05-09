"""SRG Articles API models, mapping, and no-image sanitizer."""

from __future__ import annotations

import json
from pathlib import Path

from app.srg_articles import ArticleListPage, map_article_to_app_db_fields, strip_markdown_images
from app.srg_articles.models import AccessCondition, ArticleRecord, SrgIdentifier

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "srg_article_page.json"


def test_article_page_fixture_roundtrip() -> None:
    raw = _FIXTURE.read_text(encoding="utf-8")
    page = ArticleListPage.model_validate_json(raw)
    assert page.cursor == "next-page-cursor"
    assert len(page.results) == 1
    art = page.results[0]
    assert art.id == "urn:pdp:faro_srf:article:fixture-001"
    assert art.publisher == "SRF"
    assert art.resources is not None
    assert art.resources[0].type == "Picture"


def test_map_article_to_app_db_fields_no_images_in_markdown() -> None:
    raw = _FIXTURE.read_text(encoding="utf-8")
    page = ArticleListPage.model_validate_json(raw)
    row = map_article_to_app_db_fields(page.results[0])
    assert row["external_id"] == "urn:pdp:faro_srf:article:fixture-001"
    assert row["title"] == "Bundesrat tagt"
    assert row["lead"] == "Kurzer Lead zum Thema."
    assert row["release_date"] == "2024-01-15T10:00:00Z"
    assert row["modification_date"] == "2024-01-16T08:30:00Z"
    md = row["markdown_original"]
    assert isinstance(md, str)
    assert "ilcdn.invalid" not in md
    assert "cdn.example.invalid" not in md
    assert "Erster Absatz" in md
    assert "Zweiter Absatz" in md
    assert "![](" not in md


def test_strip_markdown_images_reference_style() -> None:
    text = "A ![x][y] B"
    assert "![x][y]" not in strip_markdown_images(text)


def test_model_validate_accepts_python_dict() -> None:
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    page = ArticleListPage.model_validate(data)
    assert len(page.results) == 1


def test_map_article_fallback_title_when_id_and_texts_empty() -> None:
    art = ArticleRecord(
        id="",
        publisher="SRF",
        provenance="CMS_SRF",
        accessConditions=[AccessCondition(name="Free")],
        identifiers=[SrgIdentifier(value="", type="PdpId")],
        title=None,
        lead=None,
        content=None,
    )
    row = map_article_to_app_db_fields(art)
    assert row["title"] == "Ohne Titel"
    assert row["markdown_original"].startswith("# Ohne Titel")
