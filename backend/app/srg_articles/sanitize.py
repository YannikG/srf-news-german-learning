"""Sanitizing text destined for ``articles.markdown_original``."""

from __future__ import annotations

import re

# Product rule (v1): keine Bilder in ausgeliefertem Markdown. API liefert Fliesstext ohne
# HTML laut Spec; falls dennoch Bild-Markdown vorkommt (z. B. nach Konvertierung), entfernen.

# Reference-style ![alt][id]
_MARKDOWN_IMAGE_REF = re.compile(r"!\[[^\]]*\]\[[^\]]*\]")


def _strip_inline_markdown_images(text: str) -> str:
    """Remove ``![alt](url)`` spans; URL may contain balanced parentheses."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        start = text.find("![", i)
        if start == -1:
            out.append(text[i:])
            break
        out.append(text[i:start])
        mid = text.find("](", start + 2)
        if mid == -1:
            out.append(text[start])
            i = start + 1
            continue
        open_paren = mid + 1
        if open_paren >= n or text[open_paren] != "(":
            out.append(text[start])
            i = start + 1
            continue
        depth = 1
        k = open_paren + 1
        while k < n and depth > 0:
            c = text[k]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            k += 1
        if depth == 0:
            i = k
        else:
            # Kein passendes ``)`` (z. B. abgeschnitten): Rest wörtlich behalten, linear in ``n``.
            out.append(text[start:])
            break
    return "".join(out)


def strip_markdown_images(text: str) -> str:
    """Remove markdown image syntax from ``text``."""
    out = _strip_inline_markdown_images(text)
    out = _MARKDOWN_IMAGE_REF.sub("", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
