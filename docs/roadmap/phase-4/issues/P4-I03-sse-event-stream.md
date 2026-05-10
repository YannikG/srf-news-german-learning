# [P4-I03] SSE Event Stream

## Meta

- **Phase:** 4
- **Issue ID:** P4-I03

## Dependencies

- [P4-I02](./P4-I02-ollama-idle-warning-sleep.md)

## Goal

`GET /api/events/stream` mit `text/event-stream`; Events mindestens: `ollama_state`, `shutdown_warning`, `shutdown_cancelled`, Platzhalter für spätere `llm_chunk` (Phase 5); gleiche Origin-CORS-Regeln wie REST.

## Testable acceptance criteria

- [x] `pytest` oder Integrationstest: Client liest mindestens ein Event nach simuliertem Zustandswechsel (oder Flask test client stream read).
- [x] Reconnect-Hinweis in README (Client-seitig).
- [x] Keine Secrets in Event-Payloads.

## Dev lifecycle

1. SSE-Route; Kopplung an Ollama-Lifecycle-Service.
2. Tests.
3. PR.

## Out of scope

- Vollständiger LLM-Stream (Phase 5/6).
