# [P2-I04] Einstellungen API

## Meta

- **Phase:** 2
- **Issue ID:** P2-I04

## Dependencies

- [P2-I01](./P2-I01-app-db-schema.md)

## Goal

Persistente Einstellungen mindestens: Standard-CEFR-Level, Übersetzungssprache (`en`, `uk`), optional Top-K für Retrieval; `GET` und `PATCH` über REST.

## Testable acceptance criteria

- [ ] Werte werden in `app.db` gespeichert und nach Neustart gelesen (Test mit temp DB oder Transaction Rollback Pattern).
- [ ] `pytest` für ungültige Sprache, ungültiges CEFR-Level.
- [ ] API-Schema dokumentiert (OpenAPI optional).

## Dev lifecycle

1. Implementierung in Service-Schicht.
2. Tests.
3. PR.

## Out of scope

- UI (Phase 6).
