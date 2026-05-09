# Phasen und Issues für Agenten

## Reihenfolge

Die autoritative Reihenfolge steht in [`../roadmap/overview.md`](../roadmap/overview.md).

## Pro Phase

1. **Endzustand** in einem Satz (in `phase-N/README.md`).
2. **DoD**: nur checkbare Punkte (Befehl, Datei existiert, Verhalten beschreibbar).
3. **Issues**: eine Spec-Datei pro Issue unter `issues/`; Abhängigkeiten als relative Links zu anderen Specs.

## Pro Issue-Spec

- Ziel messbar formulieren.
- Akzeptanzkriterien mit Checkboxen: Verb + Nachweis (pytest-Pfad, Endpoint, manueller Schritt mit erwartetem Resultat).
- **Out of scope** explizit, um Scope-Creep zu vermeiden.
