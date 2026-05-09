"""SRG SSR OAuth2 client credentials (api.srgssr.ch token endpoint)."""

from __future__ import annotations

from .client import (
    USER_AGENT,
    SrgOAuthClient,
    SrgOAuthClientError,
    SrgOAuthHttpError,
    SrgOAuthTokenResponseError,
)
from .factory import build_srg_oauth_client
from .settings import SrgSsrOAuthSettings

__all__ = [
    "USER_AGENT",
    "SrgOAuthClient",
    "SrgOAuthClientError",
    "SrgOAuthHttpError",
    "SrgOAuthTokenResponseError",
    "SrgSsrOAuthSettings",
    "build_srg_oauth_client",
]
