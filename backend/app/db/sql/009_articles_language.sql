-- Add per-article language column (synergy with P8-I07 translation).
ALTER TABLE articles ADD COLUMN language TEXT DEFAULT NULL;
