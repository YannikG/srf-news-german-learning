"""Constants for the news refresh feature (SRG ingest cooldown)."""

from __future__ import annotations

# Cooldown after a successful upstream articles fetch. Spec: no SRG HTTP calls within
# this many seconds since the last successful fetch (see P3-I03 roadmap issue).
REFRESH_COOLDOWN_SECONDS = 900

LAST_SUCCESSFUL_FETCH_METADATA_KEY = "last_successful_articles_fetch_at"
