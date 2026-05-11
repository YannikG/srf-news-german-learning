-- Per-article ingest source slug (e.g. srgssr, newsapi); default backfills legacy SRG rows.

ALTER TABLE articles ADD COLUMN news_provider TEXT NOT NULL DEFAULT 'srgssr';

DROP TRIGGER IF EXISTS trg_articles_updated_at;
CREATE TRIGGER trg_articles_updated_at
AFTER UPDATE OF external_id, publisher, provenance, title, lead, markdown_original, release_date, modification_date, cefr_level, news_provider ON articles
FOR EACH ROW
BEGIN
    UPDATE articles SET updated_at = datetime('now') WHERE id = NEW.id;
END;
