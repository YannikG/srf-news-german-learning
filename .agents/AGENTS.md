# Agenten: SRF News German Learning

## Docs first

Vor grösseren Code- oder Architekturänderungen mindestens lesen:

1. [`docs/roadmap/README.md`](../docs/roadmap/README.md) und [`docs/roadmap/overview.md`](../docs/roadmap/overview.md) (Master-Reihenfolge)
2. README der **betroffenen Phase** unter `docs/roadmap/phase-N/README.md`
3. [`docs/agents-docs/README.md`](../docs/agents-docs/README.md)
4. Bei Fragen zu Spec vs. Tracker: [`docs/zusammenarbeit/README.md`](../docs/zusammenarbeit/README.md) (SSOT); ergänzend [`docs/agents-docs/collaboration.md`](../docs/agents-docs/collaboration.md)
5. Implementierung aus GitHub-Issue: [`.agents/skills/implement-plan-workflow/SKILL.md`](./skills/implement-plan-workflow/SKILL.md); `gh`: [`docs/agents-docs/github-cli.md`](../docs/agents-docs/github-cli.md)

## Code-Sprache

- **Quellcode und Code-Kommentare** (inkl. Docstrings und API-Doku im Code, z. B. JSDoc): **Englisch**.
- Nutzer-sichtbare Texte in der App dürfen weiterhin **Deutsch** (Schweizer Konvention) sein, wo das Produkt es verlangt.

## Arbeit an einem Issue

- Tracker-Issue lesen; wenn im Body ein **Permalink** auf `docs/roadmap/.../issues/*.md` steht, ist **diese Markdown-Datei die kanonische Spec**.
- PRs verweisen auf dasselbe Issue (`Fixes #n` / `Closes #n` wo zutreffend).

## PRs

- Titel und Beschreibung sollen die verlinkte Spec oder Phase-README nennen, nicht nur freie Prosa.
