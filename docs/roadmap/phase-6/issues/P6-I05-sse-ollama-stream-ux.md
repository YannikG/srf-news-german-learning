# [P6-I05] Realtime Ollama und LLM UX

## Meta

- **Phase:** 6
- **Issue ID:** P6-I05

## Dependencies

- [P6-I01](./P6-I01-vue-tooling-shell.md)
- [P4-I03](../../phase-4/issues/P4-I03-sse-event-stream.md)
- [P5-I03](../../phase-5/issues/P5-I03-simplify-llm-stream.md)

## Goal

Pinia-Store oder Composable für `EventSource`; Spinner wenn Ollama startet oder App „lädt“; PrimeVue **Dialog** bei `shutdown_warning` mit Abbruch-Button; **Go to sleep** Button; unter dem Loader **ausgegraute Box** für `llm_chunk`-Text; Reconnect-Strategie dokumentiert.

## Testable acceptance criteria

- [ ] Vitest mit gemocktem EventSource: Sequenz `shutdown_warning` → Cancel POST.
- [ ] Vitest oder manuell: `llm_chunk` appendet Text in der Box.
- [ ] Manuelle Checkliste: zweiter Tab oder Netzwerk-Flap (kurz dokumentiert).

## Dev lifecycle

1. Store + UI-Komponenten.
2. Tests mit Mocks.
3. PR.

## Out of scope

- Playwright-Pflicht (optional separates Issue).
