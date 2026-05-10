"""Tests for Markdown cleanup on simplified articles (P5-I03)."""

from __future__ import annotations

from app.articles.simplify_markdown import strip_images_from_markdown


def test_strip_markdown_images_removes_bang_bracket_pattern() -> None:
    raw = "Intro ![alt](https://example.com/x.png) outro"
    assert strip_images_from_markdown(raw) == "Intro  outro"


def test_strip_markdown_images_allows_whitespace_before_url_parens() -> None:
    raw = "X ![alt] (https://example.com/x.png) Y"
    out = strip_images_from_markdown(raw)
    assert "example.com" not in out
    assert out.strip() == "X  Y"


def test_strip_html_img_tags() -> None:
    raw = 'A <img src="https://x/y.jpg" /> B'
    assert strip_images_from_markdown(raw) == "A  B"
