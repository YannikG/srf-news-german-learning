# [P5-I01] sqlite-vec und vectors.db

## Meta

- **Phase:** 5
- **Issue ID:** P5-I01

## Dependencies

- [P2-I01](../../phase-2/issues/P2-I01-app-db-schema.md)
- [P1-I01](../../phase-1/issues/P1-I01-monorepo-docker-compose.md)

## Goal

Persistente **`vectors.db`** nur für Vektordaten; **sqlite-vec** im Web-Container laden (linux/arm64 berücksichtigen, siehe Backend-Dockerfile und README); Schema für Wort-Embeddings (768 Dimensionen, Anschluss an `nomic-embed-text` in P5-I02) und Abfrage-Helfer; **kein** Anwendungs-Fallback ohne Extension (Start schlägt fehl, wenn sqlite-vec nicht geladen werden kann).

## Testable acceptance criteria

- [x] Insert und KNN-Abfrage in `pytest` mit temporärer `vectors.db`.
- [x] Dockerfile-Dokumentation für sqlite-vec (Basis-Image glibc, PyPI-Wheel, amd64/arm64).
- [x] Klarer Fehlerpfad bei fehlender Extension (Runtime) und Test für abgelehnte Legacy-Migration (ehemaliger Entwicklungs-Fallback).

## Dev lifecycle

1. Extension einbinden; Repository für Vektoren.
2. Tests.
3. PR.

## Out of scope

- Ollama-Aufruf (P5-I02).
