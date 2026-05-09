# [P7-I02] Frontend Test Suite

## Meta

- **Phase:** 7
- **Issue ID:** P7-I02

## Dependencies

- [P6-I01](../../phase-6/issues/P6-I01-vue-tooling-shell.md) (Pflicht)
- [P6-I05](../../phase-6/issues/P6-I05-sse-ollama-stream-ux.md) (empfohlen vor Merge dieser Spec, damit SSE- und Stream-Logik abgedeckt sind)

## Goal

**Vitest** + **Vue Test Utils** / **Testing Library** für Stores, SSE-Helfer, kritische Komponenten; Edge Cases: EventSource-Fehler, doppeltes Mount, leere Artikelliste.

## Testable acceptance criteria

- [ ] `npm run test` (oder `pnpm test`) exit 0 im CI oder dokumentiert lokal.
- [ ] Mindestens fünf sinnvolle Tests (oder in Spec festgelegte Zahl) für unterschiedliche Module.

## Dev lifecycle

1. Tests ergänzen.
2. PR.

## Out of scope

- Visuelle Regression.
