"""Map NewsAPI article JSON into SQLite ``articles``-compatible field dicts."""

from __future__ import annotations

from ..srg_articles.sanitize import strip_markdown_images
from .models import NewsApiArticle


def _build_markdown_original(*, title: str, lead: str, body: str) -> str:
    """Assemble markdown for storage (no images)."""
    chunks: list[str] = []
    if title:
        chunks.append(f"# {title}")
    if lead:
        chunks.append(lead)
    if body:
        chunks.append(body)
    raw = "\n\n".join(chunks)
    return strip_markdown_images(raw)


def map_newsapi_article_to_app_db_fields(
    article: NewsApiArticle,
    *,
    language: str | None = None,
) -> dict[str, str | None]:
    """Map one NewsAPI article to columns of ``articles`` (types as stored in SQLite).

    ``title`` and ``markdown_original`` are always non-empty strings (DB NOT NULL).
    ``external_id`` uses the article URL as stable unique identifier.
    """
    raw_title = (article.title or "").strip()
    display_title = raw_title if raw_title else "Ohne Titel"

    lead = (article.description or "").strip() or None
    body = (article.content or "").strip()

    markdown_original = _build_markdown_original(
        title=display_title,
        lead=lead or "",
        body=body,
    )

    return {
        "external_id": article.url or "",
        "publisher": article.source.name or "",
        "provenance": article.url or "",
        "title": display_title,
        "lead": lead,
        "markdown_original": markdown_original,
        "release_date": article.published_at,
        "modification_date": None,
        "language": language,
    }
