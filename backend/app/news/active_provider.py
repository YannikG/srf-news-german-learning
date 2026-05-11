"""Validate ``NEWS_ACTIVE_PROVIDER`` (env / ``app.config``) for ingest wiring."""

from __future__ import annotations

DEFAULT_NEWS_ACTIVE_PROVIDER = "srgssr"

_ALLOWED_SLUGS = frozenset({"srgssr", "newsapi"})
_IMPLEMENTED_SLUGS = frozenset({"srgssr"})


def resolve_configured_news_active_provider(raw: str | None) -> str:
    """Return canonical ingest provider slug or raise ``ValueError`` with a clear message.

    Empty or unset ``raw`` defaults to ``srgssr``. Known but unimplemented slugs
    (e.g. ``newsapi``) raise until the NewsAPI path exists (roadmap P8-I04).
    """
    if raw is None:
        return DEFAULT_NEWS_ACTIVE_PROVIDER
    text = str(raw).strip().lower()
    if not text:
        return DEFAULT_NEWS_ACTIVE_PROVIDER
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


def news_active_provider_raw_for_resolve(cfg_value: object, env_value: str | None) -> str | None:
    """Pick config over env, coerce to a string for :func:`resolve_configured_news_active_provider`.

    Non-string config values (e.g. accidental ``int`` in ``test_config``) are stringified so
    validation can reject invalid slugs instead of falling back to the default silently.
    """
    merged: object = cfg_value if cfg_value is not None else env_value
    if merged is None:
        return None
    if isinstance(merged, str):
        stripped = merged.strip()
        return stripped if stripped else None
    return str(merged).strip() or None
