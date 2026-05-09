# [P5-I02] Embeddings und Retrieval

## Meta

- **Phase:** 5
- **Issue ID:** P5-I02

## Dependencies

- [P5-I01](./P5-I01-sqlite-vec-vectors-db.md)
- [P4-I01](../../phase-4/issues/P4-I01-sidecar-ollama-docker.md)
- [P4-I02](../../phase-4/issues/P4-I02-ollama-idle-warning-sleep.md) (Ollama muss zuverlässig startbar sein; Unit-Tests weiterhin mit gemocktem HTTP)
- [P2-I02](../../phase-2/issues/P2-I02-words-api.md)

## Goal

Embeddings via Ollama `nomic-embed-text`; Schreiben in `vectors.db`; Funktion **Top-K** aus Artikel-Kontext (Query-Text) mit Filter auf Lexikon in `app.db`; konfigurierbares K und Token-Budget.

## Testable acceptance criteria

- [ ] `pytest` mit gemocktem Ollama-HTTP: Embedding-Shape konsistent; Retrieval liefert erwartete `word_id`-Reihenfolge bei synthetischen Vektoren.
- [ ] Leeres Wörterbuch: definiertes Verhalten (leere Liste, kein Crash).
- [ ] Ollama-Start wird vor Embedding ausgelöst oder Fehler sauber gemeldet (gemäss Lifecycle).

## Dev lifecycle

1. Service kapseln; keine Logik in Routes.
2. Tests mit Mocks.
3. PR.

## Out of scope

- Vollständiger `simplify`-Prompt (P5-I03).
