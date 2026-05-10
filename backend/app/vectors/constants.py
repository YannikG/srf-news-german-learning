"""Shared constants for the vectors database (Phase 5, P5-I01)."""

from __future__ import annotations

from pathlib import Path

# Matches Ollama ``nomic-embed-text`` output size (P5-I02).
EMBEDDING_DIM: int = 768

# Default path alongside ``app.db`` on the Compose volume mount.
VECTORS_DB_PATH = Path("/data/vectors.db")
