# [P6-I04] Einstellungen UI

## Meta

- **Phase:** 6
- **Issue ID:** P6-I04

## Dependencies

- [P6-I01](./P6-I01-vue-tooling-shell.md)
- [P2-I04](../../phase-2/issues/P2-I04-settings-api.md)

## Goal

Auswahl Übersetzungssprache Englisch/Ukrainisch; Standard-CEFR-Level; Speichern über `PATCH` Settings; Rückmeldung per Toast.

## Testable acceptance criteria

- [ ] Vitest mit Mock: erfolgreiches Speichern und Fehlerfall.
- [ ] Werte stimmen nach Reload mit `GET` überein (manuell oder E2E).

## Dev lifecycle

1. Formular und Bindings.
2. Tests.
3. PR.

## Out of scope

- Ollama-URLs bearbeiten (kann .env bleiben v1).
