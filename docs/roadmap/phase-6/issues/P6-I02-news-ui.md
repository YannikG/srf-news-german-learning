# [P6-I02] News UI

## Meta

- **Phase:** 6
- **Issue ID:** P6-I02

## Dependencies

- [P6-I01](./P6-I01-vue-tooling-shell.md)
- [P3-I03](../../phase-3/issues/P3-I03-news-refresh-ingest.md)

## Goal

News-Timeline aus `GET /api/articles`; Datumswahl; Fuzzy-Suche über Titel; Refresh-Button oder Pull-to-Refresh für `POST /api/news/refresh`; Anzeige Cooldown (`next_allowed_fetch_at`); Artikel-Detail mit Toggle Original/vereinfacht sobald Backend liefert.

## Testable acceptance criteria

- [ ] Vitest für Store oder Composable: Mock `fetch`, Refresh zweimal schnell hintereinander zeigt erwartetes Verhalten.
- [ ] Manuelle Checkliste in PR-Beschreibung: Mobile Breite, leere Liste, Fehler-Toast bei SRG-429.
- [ ] Keine Bilder in der Darstellung (Placeholder oder ausblenden).

## Dev lifecycle

1. Komponenten und Stores.
2. Tests und manuelle Checks.
3. PR.

## Out of scope

- SSE-Ollama-Overlay (P6-I05).
