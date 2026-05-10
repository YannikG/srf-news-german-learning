# [P8-I01] Env, aktiver Ingest-Provider, Artikel-`news_provider` für UI

## Meta

- **Phase:** 8
- **Issue ID:** P8-I01

## Dependencies

- [P2-I03](../../phase-2/issues/P2-I03-articles-read-fts.md) (Artikel-API und DB)
- [P3-I03](../../phase-3/issues/P3-I03-news-refresh-ingest.md) (Refresh schreibt Artikel; Erweiterung um Provider-Slug beim Upsert)

## Goal

- **Konfiguration:** Zentrale Auswahl des **aktiven Ingest-Providers** über Umgebungsvariable (Vorschlag `NEWS_ACTIVE_PROVIDER`), Werte z. B. `srgssr`, `newsapi`. Validierung beim App-Start: unbekannter Wert → klare Fehlermeldung; für den gewählten Provider fehlende Pflicht-Credentials → klare Fehlermeldung.
- **Dokumentation:** `backend/.env.example`, Root-`compose.yaml` und README-Abschnitt aktualisieren.
- **Pro Artikel:** Persistierter, stabiler Slug **`news_provider`** (oder einheitlich in API exponierter Name), gesetzt bei jedem Upsert aus dem jeweiligen Adapter (z. B. `srgssr`, `newsapi`).
- **API:** `GET /api/articles` (Liste und Cursor) und Artikel-Detail liefern `news_provider` im JSON.
- **Frontend:** TypeScript-Typen, in **Liste und Detailansicht** sichtbare Kennzeichnung (Badge oder Zeile), damit klar ist, dass Inhalt **nicht** pauschal „von SRG“ stammen muss.
- **Optional im selben Issue:** Read-only Feld **aktiver Ingest-Provider** (ohne Secrets), z. B. in `GET /api/settings` zusammengeführt, für Shell-UI und Toasts.

## Testable acceptance criteria

- [ ] Ohne gesetzten aktiven Provider oder mit ungültigem Wert startet die App mit verständlicher Fehlermeldung (oder dokumentiertes Default-Verhalten, falls explizit gewünscht).
- [ ] Nach Refresh haben neue Artikel gesetztes `news_provider`; bestehende SRGSSR-Artikel erhalten den Slug per Migration oder einmaligem Backfill (siehe [P8-I05](./P8-I05-external-id-and-uniqueness.md) falls koordiniert).
- [ ] API-Contract-Tests oder pytest: Response enthält `news_provider` wo spezifiziert.
- [ ] Frontend zeigt Herkunft (manueller Smoke-Test oder Vitest falls sinnvoll).

## Dev lifecycle

1. Schema-Spalte `news_provider` (oder Name laut Architekturentscheid) und Migration; Repository-Mapping.
2. Refresh-Upsert setzt Slug; Articles-Read-API serialisiert Feld.
3. Frontend-Typen und UI-Badge.
4. `.env.example`, Compose, README.
5. PR.

## Out of scope

- NewsAPI-HTTP-Client (siehe [P8-I04](./P8-I04-newsapi-org-client-and-mapping.md)).
- Port-Abstraktion (siehe [P8-I02](./P8-I02-news-refresh-upstream-port-adapter.md)).
