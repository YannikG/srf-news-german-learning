-- Include `language` column in updated_at trigger (P8-I07).

DROP TRIGGER IF EXISTS trg_articles_updated_at;
CREATE TRIGGER trg_articles_updated_at
AFTER UPDATE OF external_id, publisher, provenance, title, lead, markdown_original, release_date, modification_date, cefr_level, news_provider, language ON articles
FOR EACH ROW
BEGIN
    UPDATE articles SET updated_at = datetime('now') WHERE id = NEW.id;
END;
