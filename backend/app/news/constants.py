"""Constants for the news refresh feature (per-provider cooldown)."""

from __future__ import annotations

# Cooldown after a successful upstream articles fetch (seconds).
REFRESH_COOLDOWN_SECONDS = 900

# Page size for one refresh upstream list call (SRG Articles API allows 1-10).
DEFAULT_REFRESH_ARTICLES_LIMIT = 10

# Per-provider metadata key pattern: "last_successful_articles_fetch_at:<slug>"
_LAST_FETCH_KEY_PREFIX = "last_successful_articles_fetch_at"


def metadata_key_for_provider(provider_slug: str) -> str:
    """Return the provider-scoped cooldown metadata key."""
    if not provider_slug:
        raise ValueError("provider_slug must be a non-empty string")
    if ":" in provider_slug:
        raise ValueError(f"provider_slug must not contain ':', got {provider_slug!r}")
    return f"{_LAST_FETCH_KEY_PREFIX}:{provider_slug}"
