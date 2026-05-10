# [P8-I05] `external_id` und technische Eindeutigkeit

## Meta

- **Phase:** 8
- **Issue ID:** P8-I05

## Dependencies

- [P8-I01](./P8-I01-env-active-provider-and-article-news-provider.md) (`news_provider` in DB und API)

## Goal

SQLite erzwingt `UNIQUE` auf `articles.external_id` (`001_initial.sql`). Mit mehreren Providern gilt:

- **Konvention festlegen:** Entweder stabiles **Präfix** pro Provider (`srgssr:…`, `newsapi:…`) oder **zusammengesetzter Unique** über neue Spalten (`news_provider` + Roh-ID), inkl. Migration bestehender SRGSSR-Zeilen (Backfill `news_provider`, ggf. `external_id`-Anpassung nur wenn nötig und dokumentiert risikoarm).

**Synergie:** `news_provider` aus [P8-I01](./P8-I01-env-active-provider-and-article-news-provider.md) muss mit Upsert und `ON CONFLICT` konsistent sein.

## Testable acceptance criteria

- [ ] Keine Kollision zwischen zwei Providern für dieselbe logische URL bzw. ID in der gewählten Strategie.
- [ ] Idempotenter Re-Ingest: gleicher Upstream-Artikel aktualisiert Zeile, dupliziert nicht.
- [ ] pytest deckt Konflikt- und Migrationsfall ab (temporäre DB).

## Dev lifecycle

1. Architekturentscheid Präfix vs. zusammengesetzter Index dokumentieren.
2. Migration + Upsert-SQL anpassen falls nötig.
3. Tests.
4. PR.

## Out of scope

- NewsAPI-HTTP-Details (siehe [P8-I04](./P8-I04-newsapi-org-client-and-mapping.md)).
