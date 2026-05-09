# [P2-I03] Artikel lesen und Titelsuche FTS

## Meta

- **Phase:** 2
- **Issue ID:** P2-I03

## Dependencies

- [P2-I01](./P2-I01-app-db-schema.md)

## Goal

`GET /api/articles` mit Filtern Datum, Cursor-Paging, heute-Default; Volltextsuche über Titel (FTS5); `GET /api/articles/{id}` liefert gespeicherten Inhalt aus `app.db` ohne Netzwerk.

## Testable acceptance criteria

- [ ] FTS5 Virtual Table oder gleichwertig; Suche findet Titel mit Umlaut-Varianten gemäss gewählter Strategie (Prefix oder Normalisierung dokumentiert).
- [ ] `pytest` mit eingefügten Dummy-Artikeln: Pagination, Datumsfilter, leeres Resultat, Suche ohne Treffer.
- [ ] Kein Aufruf zu `api.srgssr.ch` in diesen GET-Routen (Test mit Mock oder Assertion auf fehlende Client-Nutzung).

## Dev lifecycle

1. Repositories und Services; Routes.
2. FTS und Tests.
3. PR.

## Out of scope

- `POST /api/news/refresh` (Phase 3).
- Markdown-Vereinfachung (Phase 5).
