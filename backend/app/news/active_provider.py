"""Validate ``NEWS_ACTIVE_PROVIDER`` (env / ``app.config``) for ingest wiring."""

from __future__ import annotations

_ALLOWED_SLUGS = frozenset({"srgssr", "newsapi"})
_IMPLEMENTED_SLUGS = frozenset({"srgssr"})


def resolve_configured_news_active_provider(raw: str | None) -> str:
    """Return canonical ingest provider slug or raise ``ValueError`` with a clear message.

    Empty or unset ``raw`` defaults to ``srgssr``. Known but unimplemented slugs
    (e.g. ``newsapi``) raise until the NewsAPI path exists (roadmap P8-I04).
    """
    if raw is None:
        return "srgssr"
    text = str(raw).strip().lower()
    if not text:
        return "srgssr"
    if text not in _ALLOWED_SLUGS:
        allowed = ", ".join(sorted(_ALLOWED_SLUGS))
        raise ValueError(
            f"NEWS_ACTIVE_PROVIDER must be one of: {allowed}. Got {raw!r}.",
        )
    if text not in _IMPLEMENTED_SLUGS:
        raise ValueError(
            f'Active ingest provider "{text}" is not implemented yet (roadmap P8-I04).',
        )
    return text
