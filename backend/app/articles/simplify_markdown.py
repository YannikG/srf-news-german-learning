"""Markdown cleanup for persisted simplifications (P5-I03)."""

from __future__ import annotations

import re

# Allow optional whitespace before the URL parentheses (common in some Markdown / LLM output).
_MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*]\s*\([^)]*\)")
_HTML_IMG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def strip_images_from_markdown(text: str) -> str:
    """Remove Markdown image syntax and bare ``img`` tags; collapse whitespace edges."""
    without = _MARKDOWN_IMAGE.sub("", text)
    without = _HTML_IMG.sub("", without)
    return without.strip()
