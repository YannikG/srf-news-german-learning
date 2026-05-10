-- Optional cap on characters sent to the embedding model for article-context retrieval (P5-I02).

ALTER TABLE settings ADD COLUMN retrieval_context_max_chars INTEGER;
