"""Run SQLite ``executescript`` bundles in a single DEFERRED transaction."""

from __future__ import annotations

import sqlite3


def execute_script_as_transaction(conn: sqlite3.Connection, script: str) -> None:
    """Run ``script`` atomically (restore prior ``isolation_level`` after)."""
    saved = conn.isolation_level
    conn.isolation_level = "DEFERRED"
    try:
        with conn:
            conn.executescript(script)
    finally:
        conn.isolation_level = saved
