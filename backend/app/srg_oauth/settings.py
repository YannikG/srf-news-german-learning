"""Environment-backed credentials for the SRG SSR OAuth token endpoint."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .defaults import DEFAULT_TOKEN_URL, DEFAULT_USER_AGENT


class SrgSsrOAuthSettings(BaseSettings):
    """SRG SSR OAuth settings from the environment (credentials plus optional overrides)."""

    model_config = SettingsConfigDict(extra="ignore")

    consumer_key: str = Field(validation_alias="SRGSSR_CONSUMER_KEY")
    consumer_secret: str = Field(validation_alias="SRGSSR_CONSUMER_SECRET")
    token_url: str = Field(default=DEFAULT_TOKEN_URL, validation_alias="SRGSSR_TOKEN_URL")
    user_agent: str = Field(default=DEFAULT_USER_AGENT, validation_alias="SRGSSR_USER_AGENT")
