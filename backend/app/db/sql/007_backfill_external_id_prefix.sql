-- Prefix existing external_id values with their news_provider slug.
-- Convention: '{news_provider}:{raw_upstream_id}' (see P8-I05).
-- Only touches rows that are not already prefixed.

UPDATE articles
SET external_id = news_provider || ':' || external_id
WHERE INSTR(external_id, news_provider || ':') != 1;
