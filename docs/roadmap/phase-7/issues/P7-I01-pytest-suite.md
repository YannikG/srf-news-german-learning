# [P7-I01] Backend Test Suite und Edge Cases

## Meta

- **Phase:** 7
- **Issue ID:** P7-I01

## Dependencies

- Kernfeatures aus [Phase 2](../../phase-2/README.md), [Phase 3](../../phase-3/README.md), [Phase 4](../../phase-4/README.md) und [Phase 5](../../phase-5/README.md) sind im Repo gemerged (diese Issue schliesst Testlücken und Edge Cases, nicht der erste Code).

## Goal

Breite **pytest**-Abdeckung für Domänenlogik und HTTP-Schicht mit Fokus auf **Edge Cases**: Cooldown-Grenzen, Idle-Timer, Cancel, leere Daten, fehlerhafte LLM-Antworten, FTS-Grenzen, doppelter Refresh.

## Testable acceptance criteria

- [ ] `pytest` im CI oder lokal mit einem dokumentierten Befehl ohne Netzwerk (Marker `not integration` falls nötig) ist grün.
- [ ] `pytest-cov` optional: Schwellenwert in Spec oder „Report only“ dokumentiert.
- [ ] Liste der abgedeckten Edge Cases in PR-Beschreibung oder `docs/testing-backend.md` (kurz).

## Dev lifecycle

1. Tests sammeln und Lücken schliessen.
2. PR.

## Out of scope

- E2E-Browser (Phase 7 optional separat).
