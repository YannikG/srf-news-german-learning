# [P2-I01] app.db Schema und Migrationen

## Meta

- **Phase:** 2
- **Issue ID:** P2-I01

## Dependencies

- [P1-I02](../../phase-1/issues/P1-I02-flask-venv-health.md)

## Goal

SQLite-Datenbank **`app.db`** mit Tabellen für Artikel, Wörter, Artikel-Wort-Verknüpfungen, Einstellungen und SRG-Sync-Metadaten gemäss Produktplan; reproduzierbare Initialisierung (Migrationen oder Idempotentes Setup-Skript).

## Testable acceptance criteria

- [ ] Frische `app.db` lässt sich per dokumentiertem Befehl oder App-Start mit leerem Volume erzeugen.
- [ ] Alle Tabellen und Indizes aus der Architekturspec existieren (inkl. CEFR-Level-Feld, Schwierigkeit Wörter, Übersetzungssprache in Settings).
- [ ] `pytest` prüft, dass Migration/Init zweimal idempotent ist oder Migrationsversion konsistent bleibt.

## Dev lifecycle

1. Schema entwerfen; Migration oder Init implementieren.
2. Tests hinzufügen.
3. PR mit Link auf diese Spec.

## Out of scope

- SRG-Fetch (Phase 3).
- sqlite-vec (Phase 5).
