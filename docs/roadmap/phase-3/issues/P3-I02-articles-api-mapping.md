# [P3-I02] SRG Articles API Mapping und Felder

## Meta

- **Phase:** 3
- **Issue ID:** P3-I02

## Dependencies

- none (parallel zu [P3-I01](./P3-I01-srg-oauth-client.md) möglich)

**Blockiert:** [P3-I03](./P3-I03-news-refresh-ingest.md) darf erst umgesetzt werden, wenn diese Spec erfüllt ist (Mapping und Parser stehen fest).

## Goal

Recherche und festes Mapping: welche Endpunkte und Felder der **SRGSSR Articles API v2** für SRF-Nachrichten genutzt werden; wie Titel, Lead, Body, Publikationszeit in `markdown_original` (ohne Bilder) und Metadaten in `app.db` übergehen.

**Referenz im Repo:** OpenAPI [`docs/api/srgssr-articles-v2-openapi.yaml`](../../../api/srgssr-articles-v2-openapi.yaml), Kurzdokument [`docs/srg-articles-api.md`](../../../srg-articles-api.md).

## Testable acceptance criteria

- [x] OpenAPI-Datei unter `docs/api/srgssr-articles-v2-openapi.yaml`; Kurzdokument `docs/srg-articles-api.md` mit Endpunkt, Auth, Query-Parametern und Mapping-Hinweisen (ohne Secrets) — eingecheckt 2026-05-09.
- [ ] Pydantic-Modelle oder gleichwertige Parser für die SRG-Response definiert; mindestens ein Test mit Fixture-JSON.
- [ ] Explizite Regel „keine Bilder“ in Mapping oder Sanitizer dokumentiert und getestet.

## Dev lifecycle

1. Portal lesen; Contract dokumentieren.
2. Parser und Tests mit Fixtures.
3. PR.

## Out of scope

- Persistenz in DB (P3-I03).
