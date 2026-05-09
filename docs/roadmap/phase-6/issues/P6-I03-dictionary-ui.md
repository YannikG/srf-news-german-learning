# [P6-I03] Wörterbuch UI

## Meta

- **Phase:** 6
- **Issue ID:** P6-I03

## Dependencies

- [P6-I01](./P6-I01-vue-tooling-shell.md)
- [P2-I02](../../phase-2/issues/P2-I02-words-api.md)

## Goal

Tabelle mit allen Feldern editierbar; Kategorie und Schwierigkeit; Übersetzungsspalte; CRUD mit PrimeVue DataTable/Dialog; Mobile nutzbar.

## Testable acceptance criteria

- [ ] Vitest für mindestens einen CRUD-Flow mit Mock-API.
- [ ] Manuelle Prüfung: Validierung bei leerem Pflichtfeld.
- [ ] Filter nach Kategorie falls API unterstützt.

## Dev lifecycle

1. UI und Store.
2. Tests.
3. PR.

## Out of scope

- Externe Wortarten-API.
- PONS und „Übersetzung anzeigen“ auf Knopfdruck: optionales Follow-up [P6-I06](./P6-I06-optional-pons-on-demand.md).
