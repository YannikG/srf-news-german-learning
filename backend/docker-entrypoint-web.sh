#!/bin/sh
set -e
# Named volume mounts (e.g. Compose ``app_data:/data``) are often root-owned; ensure
# the app user can create SQLite files under ``/data``.
mkdir -p /data
chown -R appuser:appuser /data
exec gosu appuser "$@"
