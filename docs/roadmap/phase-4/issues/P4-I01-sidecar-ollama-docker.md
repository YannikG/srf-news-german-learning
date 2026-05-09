# [P4-I01] Docker Sidecar für Ollama Steuerung

## Meta

- **Phase:** 4
- **Issue ID:** P4-I01

## Dependencies

- [P1-I01](../../phase-1/issues/P1-I01-monorepo-docker-compose.md)

## Goal

Sidecar-Container mit minimaler HTTP-API: `start`, `stop`, `inspect` für den Ollama-Service; Docker-Socket **nur** im Sidecar; Web-Container ohne Socket.

## Testable acceptance criteria

- [ ] Compose startet `web`, `ollama`, `sidecar`; Ollama standardmässig gestoppt oder startfähig laut Spec.
- [ ] Web kann über konfigurierte URL Sidecar aufrufen (Smoke-Test manuell oder mit Testcontainer optional).
- [ ] Dokumentation der Sidecar-API (Pfade, Auth-Header falls Shared Secret).

## Dev lifecycle

1. Sidecar-Implementierung (kleines Framework nach Wahl).
2. Compose-Verdrahtung.
3. PR.

## Out of scope

- SSE (P4-I03).
- Idle-Logik (P4-I02).
