"""Register SQLAlchemy engines and first-run SQLite bootstrap for ``app.db`` / ``vectors.db``."""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from ..db import init_database
from ..persistence import (
    SQL_DATABASE_EXTENSION_KEY,
    VECTORS_DATABASE_EXTENSION_KEY,
    SqlDatabase,
    VectorsDatabase,
)
from ..vectors import init_vectors_database


def register_database_extensions(app: Flask) -> None:
    """Attach ``SqlDatabase`` and ``VectorsDatabase`` when paths are configured."""
    db_path_str = app.config.get("DATABASE_PATH")
    if db_path_str:
        db_path = Path(db_path_str).expanduser().resolve()
        app.extensions[SQL_DATABASE_EXTENSION_KEY] = SqlDatabase(str(db_path))
        if not db_path.is_file():
            # First boot only: create the file and apply all migrations. For schema
            # updates on an existing file, run `flask init-db` (not every app start).
            init_database(db_path)
        # ``vectors.db`` next to ``app.db`` (Compose: both under ``/data``).
        app.config.setdefault("VECTORS_DATABASE_PATH", str(db_path.parent / "vectors.db"))

    vectors_path_str = app.config.get("VECTORS_DATABASE_PATH")
    if vectors_path_str:
        vectors_path = Path(vectors_path_str).expanduser().resolve()
        if not vectors_path.is_file():
            init_vectors_database(vectors_path)
        app.extensions[VECTORS_DATABASE_EXTENSION_KEY] = VectorsDatabase(str(vectors_path))
