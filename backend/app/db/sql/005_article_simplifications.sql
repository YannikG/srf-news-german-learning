-- Persisted LLM simplifications per article and CEFR level (P5-I03).

CREATE TABLE IF NOT EXISTS article_simplifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    cefr_level TEXT NOT NULL,
    markdown_simplified TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (article_id, cefr_level)
);

CREATE INDEX IF NOT EXISTS idx_article_simplifications_article_id
    ON article_simplifications(article_id);

CREATE TABLE IF NOT EXISTS article_simplification_used_words (
    simplification_id INTEGER NOT NULL REFERENCES article_simplifications(id) ON DELETE CASCADE,
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    PRIMARY KEY (simplification_id, word_id)
);

CREATE INDEX IF NOT EXISTS idx_article_simplification_used_words_word_id
    ON article_simplification_used_words(word_id);

CREATE TABLE IF NOT EXISTS article_simplification_suggested_words (
    simplification_id INTEGER NOT NULL REFERENCES article_simplifications(id) ON DELETE CASCADE,
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    PRIMARY KEY (simplification_id, word_id)
);

CREATE INDEX IF NOT EXISTS idx_article_simplification_suggested_words_word_id
    ON article_simplification_suggested_words(word_id);

CREATE TRIGGER IF NOT EXISTS trg_article_simplifications_updated_at
AFTER UPDATE OF markdown_simplified, cefr_level ON article_simplifications
FOR EACH ROW
BEGIN
    UPDATE article_simplifications SET updated_at = datetime('now') WHERE id = NEW.id;
END;
