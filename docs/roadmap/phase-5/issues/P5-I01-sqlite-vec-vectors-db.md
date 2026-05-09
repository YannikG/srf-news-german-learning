# [P5-I01] sqlite-vec und vectors.db

## Meta

- **Phase:** 5
- **Issue ID:** P5-I01

## Dependencies

- [P2-I01](../../phase-2/issues/P2-I01-app-db-schema.md)
- [P1-I01](../../phase-1/issues/P1-I01-monorepo-docker-compose.md)

## Goal

Persistente **`vectors.db`** nur für Vektordaten; **sqlite-vec** im Web-Container laden (linux/arm64 berücksichtigen); Schema für Wort-Embeddings und Abfrage-Helfer; dokumentierter **NumPy-Fallback** falls Extension fehlschlägt.

## Testable acceptance criteria

- [ ] Insert und KNN-Abfrage in `pytest` mit temporärer `vectors.db` (oder In-Memory falls unterstützt).
- [ ] Dockerfile-Dokumentation oder Multi-Stage-Build für sqlite-vec `.so`.
- [ ] Fallback-Pfad durch einen Test oder explizit übersprungen mit Issue-Kommentar und einem Minimaltest für Cosinus.

## Dev lifecycle

1. Extension einbinden; Repository für Vektoren.
2. Tests.
3. PR.

## Out of scope

- Ollama-Aufruf (P5-I02).
