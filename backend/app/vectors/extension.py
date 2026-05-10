"""Load the sqlite-vec extension into a SQLite connection when available."""

from __future__ import annotations

import importlib
import importlib.util
import sqlite3
from contextlib import suppress


def try_load_sqlite_vec(dbapi_connection: sqlite3.Connection) -> bool:
    """Load sqlite-vec into ``dbapi_connection``. Returns ``True`` if loaded.

    Returns ``False`` when the build disables loadable extensions, the
    ``sqlite-vec`` package or native library is unavailable, or ``load()``
    fails. Bootstrap code treats ``False`` as a hard error (no alternate schema).
    """
    if not hasattr(dbapi_connection, "enable_load_extension"):
        return False
    if importlib.util.find_spec("sqlite_vec") is None:
        return False
    try:
        sqlite_vec = importlib.import_module("sqlite_vec")
    except ImportError:
        return False
    try:
        dbapi_connection.enable_load_extension(True)
        sqlite_vec.load(dbapi_connection)
        return True
    except (AttributeError, OSError, sqlite3.OperationalError, sqlite3.DatabaseError):
        return False
    finally:
        with suppress(AttributeError):
            dbapi_connection.enable_load_extension(False)
