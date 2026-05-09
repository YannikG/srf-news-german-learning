"""SRG SSR OAuth2 client credentials (api.srgssr.ch token endpoint)."""

from __future__ import annotations

from .client import (
    TOKEN_URL,
    USER_AGENT,
    SrgOAuthClient,
    SrgOAuthClientError,
    SrgOAuthHttpError,
    SrgOAuthTokenResponseError,
)
from .defaults import DEFAULT_TOKEN_URL, DEFAULT_USER_AGENT
from .factory import build_srg_oauth_client
from .settings import SrgSsrOAuthSettings

__all__ = [
    "DEFAULT_TOKEN_URL",
    "DEFAULT_USER_AGENT",
    "TOKEN_URL",
    "USER_AGENT",
    "SrgOAuthClient",
    "SrgOAuthClientError",
    "SrgOAuthHttpError",
    "SrgOAuthTokenResponseError",
    "SrgSsrOAuthSettings",
    "build_srg_oauth_client",
]
