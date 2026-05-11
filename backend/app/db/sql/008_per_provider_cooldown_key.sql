-- Migrate the global cooldown metadata key to the per-provider key scheme (P8-I03).
-- Existing deployments have "last_successful_articles_fetch_at" from SRGSSR ingest;
-- rename it to "last_successful_articles_fetch_at:srgssr" so switching providers
-- does not inherit the old cooldown.  Idempotent: WHERE clause only matches the
-- un-suffixed key.
UPDATE srg_sync_metadata
SET key = 'last_successful_articles_fetch_at:srgssr'
WHERE key = 'last_successful_articles_fetch_at';
