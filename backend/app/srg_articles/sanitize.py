"""Sanitizing text destined for ``articles.markdown_original``."""

from __future__ import annotations

import re

# Product rule (v1): keine Bilder in ausgeliefertem Markdown. API liefert Fliesstext ohne
# HTML laut Spec; falls dennoch Bild-Markdown vorkommt (z. B. nach Konvertierung), entfernen.
_MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")

# Reference-style ![alt][id] — optional hardening
_MARKDOWN_IMAGE_REF = re.compile(r"!\[[^\]]*\]\[[^\]]*\]")


def strip_markdown_images(text: str) -> str:
    """Remove markdown image syntax from ``text``."""
    out = _MARKDOWN_IMAGE.sub("", text)
    out = _MARKDOWN_IMAGE_REF.sub("", out)
    # Collapse excessive blank lines after removals
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
