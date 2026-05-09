# [P3-I03] News Refresh und Ingest

## Meta

- **Phase:** 3
- **Issue ID:** P3-I03

## Dependencies

- [P3-I01](./P3-I01-srg-oauth-client.md)
- [P3-I02](./P3-I02-articles-api-mapping.md)
- [P2-I03](../../phase-2/issues/P2-I03-articles-read-fts.md)

## Goal

`POST /api/news/refresh` löst bei erlaubtem Zeitfenster einen SRG-Abruf aus, schreibt/aktualisiert Artikel in `app.db`; innerhalb von 900 s seit letztem erfolgreichen Abruf **kein** Upstream-Call, Response mit `next_allowed_fetch_at` oder gleichwertig.

## Testable acceptance criteria

- [ ] `pytest` mit gefälschter Zeit (`freezegun`): erster Refresh ok, zweiter innerhalb 15 min ohne HTTP zu SRG.
- [ ] Grenze exakt bei 900 s dokumentiert und getestet.
- [ ] `GET /api/articles` ruft SRG nicht auf (Regressionstest).
- [ ] Duplikate anhand SRG-ID idempotent behandeln.

## Dev lifecycle

1. Service zusammenbauen; Fehler 429/401 nutzerfreundlich mappen.
2. Tests.
3. PR.

## Out of scope

- Hintergrund-Cron (explizit verboten laut Plan).
