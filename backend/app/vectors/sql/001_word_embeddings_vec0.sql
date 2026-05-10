-- sqlite-vec vec0 table for word embeddings (768 dimensions, nomic-embed-text).

CREATE TABLE IF NOT EXISTS _migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_id TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE IF NOT EXISTS word_embeddings USING vec0(
  embedding float[768]
);
