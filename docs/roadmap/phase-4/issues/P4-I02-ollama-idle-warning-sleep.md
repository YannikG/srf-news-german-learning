# [P4-I02] Ollama Idle Warnung Sleep und Cancel

## Meta

- **Phase:** 4
- **Issue ID:** P4-I02

## Dependencies

- [P4-I01](./P4-I01-sidecar-ollama-docker.md)

## Goal

Nach letztem Ollama-Request Idle-Timer (Default 600 s); **60 s** vor Stopp logisch auslösbar für Warn-Event (konfigurierbar `OLLAMA_SHUTDOWN_WARNING_SECONDS`); `POST /api/ollama/cancel-idle-shutdown` setzt Timer zurück; `POST /api/ollama/go-to-sleep` stoppt sofort.

## Testable acceptance criteria

- [ ] `pytest` mit gefälschter Zeit: Warn-Event-Zeitpunkt, Cancel vor Stopp, kein Stop nach Cancel.
- [ ] `go-to-sleep` während laufendem Request: Verhalten dokumentiert (Queue oder harter Stopp) und getestet.
- [ ] Referenzzähler oder gleichwertig bei parallelen LLM-Anfragen verhindert vorzeitiges Herunterfahren.

## Dev lifecycle

1. Timer-Logik in dediziertem Service.
2. Tests mit freezegun.
3. PR.

## Out of scope

- SSE-Versand (P4-I03 verbindet Events).
