"""Load optional ``backend/.env`` and ``backend/local.env`` into the process environment."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _backend_dir() -> Path:
    """Directory that contains ``app/`` and ``wsgi.py`` (``backend/`` in the repo layout)."""
    return Path(__file__).resolve().parents[2]


def load_backend_dotenv_files() -> None:
    """Populate ``os.environ`` from ``backend/.env`` then ``backend/local.env``.

    - **Lokal** (``flask`` / ``gunicorn`` aus dem Repo): Dateien liegen neben ``wsgi.py`` und
      werden hier geladen (spätere Datei überschreibt gleiche Keys).
    - **Docker**: In ``compose.yaml`` ``env_file: backend/local.env`` setzen,
      damit Variablen **vor** dem Prozessstart in ``os.environ`` stehen; diese Funktion findet im
      Image oft **keine** ``.env``-Dateien unter ``/app/`` (das ist normal).

    Skipped when ``python-dotenv`` fehlt. Nur ausserhalb von pytest ``TESTING``.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        logger.warning("python-dotenv is not installed; skipping backend/.env and local.env")
        return
    root = _backend_dir()
    for name, override in ((".env", False), ("local.env", True)):
        path = root / name
        if not path.is_file():
            continue
        load_dotenv(path, override=override)
        if os.environ.get("FLASK_DEBUG") == "1":
            logger.info("Loaded %s", path)
