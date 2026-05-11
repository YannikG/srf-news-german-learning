"""Provider-aware external_id namespacing for multi-provider uniqueness."""

from __future__ import annotations

_SEPARATOR = ":"


def namespace_external_id(news_provider: str, raw_id: str) -> str:
    """Return ``'{news_provider}:{raw_id}'``, skipping if already prefixed.

    The raw upstream id may itself contain colons (e.g. URN strings), so only
    the first segment before the separator is checked against *news_provider*.
    """
    if not news_provider:
        raise ValueError("news_provider must be a non-empty string")
    if not raw_id:
        raise ValueError("raw_id must be a non-empty string")
    if _SEPARATOR in news_provider:
        raise ValueError(f"news_provider must not contain '{_SEPARATOR}', got {news_provider!r}")
    prefix = f"{news_provider}{_SEPARATOR}"
    if raw_id.lower().startswith(prefix.lower()):
        return raw_id
    return f"{prefix}{raw_id}"
