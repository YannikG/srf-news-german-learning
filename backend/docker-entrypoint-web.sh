#!/bin/sh
set -e
# Named volume mounts (e.g. Compose ``app_data:/data``) are often root-owned; ensure
# the app user can create SQLite files under ``/data``.
mkdir -p /data
chown -R appuser:appuser /data
# Existing DB files are not auto-migrated inside ``create_app`` (multi-worker safety).
# Run pending SQL migrations once before Gunicorn forks workers so Compose volumes
# pick up new columns (e.g. ``news_provider``) after an image upgrade.
gosu appuser python -m flask --app wsgi init-db
exec gosu appuser "$@"
