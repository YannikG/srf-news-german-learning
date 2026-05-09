"""Composition root for settings service + SQLite repository."""

from __future__ import annotations

from ..persistence import SqlDatabase
from .repository import SqliteSettingsRepository
from .service import SettingsService


def build_settings_service(db: SqlDatabase) -> SettingsService:
    """Return ``SettingsService`` backed by ``SqliteSettingsRepository``."""
    return SettingsService(SqliteSettingsRepository(db))
