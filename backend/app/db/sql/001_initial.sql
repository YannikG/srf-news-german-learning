CREATE TABLE IF NOT EXISTS _migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_id TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL UNIQUE,
    publisher TEXT,
    provenance TEXT,
    title TEXT NOT NULL,
    lead TEXT,
    markdown_original TEXT NOT NULL DEFAULT '',
    release_date TEXT,
    modification_date TEXT,
    cefr_level TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_articles_release_date ON articles(release_date);
CREATE INDEX IF NOT EXISTS idx_articles_publisher ON articles(publisher);
CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    german_label TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    difficulty TEXT NOT NULL DEFAULT 'Neu'
        CHECK (difficulty IN ('Neu', 'Schwer', 'Mittel', 'Leicht')),
    translation TEXT NOT NULL DEFAULT '',
    cefr_level TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_words_category ON words(category);
CREATE INDEX IF NOT EXISTS idx_words_german_label ON words(german_label);
CREATE INDEX IF NOT EXISTS idx_words_difficulty ON words(difficulty);

CREATE TABLE IF NOT EXISTS article_words (
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, word_id)
);

CREATE INDEX IF NOT EXISTS idx_article_words_word_id ON article_words(word_id);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    default_cefr TEXT NOT NULL DEFAULT 'B1',
    translation_language TEXT NOT NULL DEFAULT 'en'
        CHECK (translation_language IN ('en', 'uk')),
    retrieval_top_k INTEGER
);

INSERT OR IGNORE INTO settings (id, default_cefr, translation_language, retrieval_top_k)
VALUES (1, 'B1', 'en', NULL);

CREATE TABLE IF NOT EXISTS srg_sync_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_srg_sync_metadata_updated_at ON srg_sync_metadata(updated_at);
