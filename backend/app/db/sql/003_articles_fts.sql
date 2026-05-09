-- Title search via FTS5 (external content over ``articles``).
-- Tokenizer ``unicode61 remove_diacritics 2`` normalizes combining marks so queries
-- without umlauts can match stored titles with umlauts. Application queries append
-- ``*`` per token for prefix matching (see ``SqliteArticlesRepository``).

CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    title,
    content='articles',
    content_rowid='id',
    tokenize = 'unicode61 remove_diacritics 2'
);

INSERT INTO articles_fts(rowid, title) SELECT id, title FROM articles;

CREATE TRIGGER IF NOT EXISTS trg_articles_ai_fts
AFTER INSERT ON articles
BEGIN
    INSERT INTO articles_fts(rowid, title) VALUES (new.id, new.title);
END;

CREATE TRIGGER IF NOT EXISTS trg_articles_ad_fts
AFTER DELETE ON articles
BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title) VALUES ('delete', old.id, old.title);
END;

CREATE TRIGGER IF NOT EXISTS trg_articles_au_fts
AFTER UPDATE OF title ON articles
BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, title) VALUES ('delete', old.id, old.title);
    INSERT INTO articles_fts(rowid, title) VALUES (new.id, new.title);
END;
