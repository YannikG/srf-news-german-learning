-- Bump updated_at on row updates. AFTER UPDATE OF excludes updated_at so the
-- inner UPDATE does not re-fire these triggers (SQLite default: recursive_triggers off).

CREATE TRIGGER IF NOT EXISTS trg_articles_updated_at
AFTER UPDATE OF external_id, publisher, provenance, title, lead, markdown_original, release_date, modification_date, cefr_level ON articles
FOR EACH ROW
BEGIN
    UPDATE articles SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_words_updated_at
AFTER UPDATE OF german_label, category, difficulty, translation, cefr_level ON words
FOR EACH ROW
BEGIN
    UPDATE words SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_srg_sync_metadata_updated_at
AFTER UPDATE OF value ON srg_sync_metadata
FOR EACH ROW
BEGIN
    UPDATE srg_sync_metadata SET updated_at = datetime('now') WHERE key = NEW.key;
END;
