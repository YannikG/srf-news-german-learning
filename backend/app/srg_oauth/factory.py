"""Factory wiring settings + HTTP client for :class:`~app.srg_oauth.client.SrgOAuthClient`."""

from __future__ import annotations

import httpx

from .client import SrgOAuthClient
from .settings import SrgSsrOAuthSettings


def build_srg_oauth_client(
    settings: SrgSsrOAuthSettings | None = None,
    *,
    http_client: httpx.Client | None = None,
    refresh_skew_seconds: int = 60,
    request_timeout_seconds: float = 30.0,
) -> SrgOAuthClient:
    """Build a client from env (default) or explicit ``SrgSsrOAuthSettings``."""
    resolved = settings if settings is not None else SrgSsrOAuthSettings()
    return SrgOAuthClient(
        resolved.consumer_key,
        resolved.consumer_secret,
        token_url=resolved.token_url,
        user_agent=resolved.user_agent,
        http_client=http_client,
        refresh_skew_seconds=refresh_skew_seconds,
        request_timeout_seconds=request_timeout_seconds,
    )
