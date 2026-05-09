# [P2-I02] Wörterbuch REST API

## Meta

- **Phase:** 2
- **Issue ID:** P2-I02

## Dependencies

- [P2-I01](./P2-I01-app-db-schema.md)

## Goal

CRUD für Wörter über REST: Deutschbezeichnung, Kategorie, Schwierigkeit (`Neu`, `Schwer`, `Mittel`, `Leicht`), nutzergestützte Übersetzung; Filter nach Kategorie optional.

## Testable acceptance criteria

- [ ] `GET/POST/PATCH/DELETE` Endpunkte gemäss API-Konvention im Plan; alle Felder editierbar wie spezifiziert.
- [ ] `pytest` deckt anlegen, ändern, löschen, ungültige Schwierigkeit, leere Strings ab (Edge Cases).
- [ ] Keine Abhängigkeit von Ollama oder SRG.

## Dev lifecycle

1. Service- und Repository-Schicht; Routes dünn halten.
2. Tests.
3. PR.

## Out of scope

- Externe Wortarten-API.
- Vektor-Embeddings für Wörter (Phase 5).
- **PONS** (oder andere Online-Wörterbücher): optional in [P6-I06](../../phase-6/issues/P6-I06-optional-pons-on-demand.md); Kurzreferenz [`docs/pons-dictionary-api.md`](../../../pons-dictionary-api.md).
