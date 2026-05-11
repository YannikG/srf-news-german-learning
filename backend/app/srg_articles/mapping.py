"""Map SRG ``Article`` JSON into SQLite ``articles``-compatible field dicts (no persistence)."""

from __future__ import annotations

from collections.abc import Sequence

from .models import ArticleContentBlock, ArticleRecord, TextBlock
from .sanitize import strip_markdown_images


def pick_localized_text(
    blocks: Sequence[TextBlock] | None,
    *,
    preferred_languages: tuple[str, ...] = ("de", "gsw", "fr", "it", "en"),
) -> str:
    """Pick one ``Text`` string: first match for ``preferred_languages``, else first block."""
    if not blocks:
        return ""
    prefs = tuple(p.lower() for p in preferred_languages)
    for lang in prefs:
        for block in blocks:
            bl = (block.language or "").lower()
            if bl == lang:
                return block.content.strip()
    for block in blocks:
        if not block.language or block.language == "Unknown":
            return block.content.strip()
    return blocks[0].content.strip()


def flatten_article_body(content: ArticleContentBlock | None) -> str:
    """Join ``content.text`` paragraphs with blank lines (OpenAPI: plain strings, no HTML)."""
    if content is None:
        return ""
    parts = [p.strip() for p in content.text if p.strip()]
    return "\n\n".join(parts)


def build_markdown_original(*, title: str, lead: str, body: str) -> str:
    """
    Assemble markdown for storage.

    Regel: keine Bilder — ``body``/``lead`` werden durch ``strip_markdown_images`` gefiltert;
    ``resources`` (Picture/Document URLs) werden nie eingemischt.
    """
    chunks: list[str] = []
    if title:
        chunks.append(f"# {title}")
    if lead:
        chunks.append(lead)
    if body:
        chunks.append(body)
    raw = "\n\n".join(chunks)
    return strip_markdown_images(raw)


def map_article_to_app_db_fields(
    article: ArticleRecord,
    *,
    preferred_languages: tuple[str, ...] = ("de", "gsw", "fr", "it", "en"),
) -> dict[str, str | None]:
    """
    Map one API article to columns of ``articles`` (types as stored in SQLite).

    ``title`` and ``markdown_original`` are always non-empty strings (DB NOT NULL). Falls
    weder Titelzeile noch ``article.id`` Text liefern, wird ``Ohne Titel`` gesetzt.
    """
    title = pick_localized_text(article.title, preferred_languages=preferred_languages)
    lead = pick_localized_text(article.lead, preferred_languages=preferred_languages)
    body = flatten_article_body(article.content)
    display_title = title if title else article.id
    if not display_title:
        display_title = "Ohne Titel"
    markdown_original = build_markdown_original(title=display_title, lead=lead, body=body)
    lead_out = lead if lead else None
    return {
        "external_id": article.id,
        "publisher": article.publisher,
        "provenance": article.provenance,
        "title": display_title,
        "lead": lead_out,
        "markdown_original": markdown_original,
        "release_date": article.release_date,
        "modification_date": article.modification_date,
        "language": "de",
    }
