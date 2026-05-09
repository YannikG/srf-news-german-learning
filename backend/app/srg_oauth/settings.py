"""Environment-backed credentials for the SRG SSR OAuth token endpoint."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SrgSsrOAuthSettings(BaseSettings):
    """Reads ``SRGSSR_CONSUMER_KEY`` and ``SRGSSR_CONSUMER_SECRET`` from the environment."""

    model_config = SettingsConfigDict(extra="ignore")

    consumer_key: str = Field(validation_alias="SRGSSR_CONSUMER_KEY")
    consumer_secret: str = Field(validation_alias="SRGSSR_CONSUMER_SECRET")
