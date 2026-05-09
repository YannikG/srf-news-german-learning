# Agenten: SRF News German Learning

## Docs first

Vor grösseren Code- oder Architekturänderungen mindestens lesen:

1. [`docs/roadmap/README.md`](../docs/roadmap/README.md) und [`docs/roadmap/overview.md`](../docs/roadmap/overview.md) (Master-Reihenfolge)
2. README der **betroffenen Phase** unter `docs/roadmap/phase-N/README.md`
3. [`docs/agents-docs/README.md`](../docs/agents-docs/README.md)
4. Bei Fragen zu Spec vs. Tracker: [`docs/zusammenarbeit/README.md`](../docs/zusammenarbeit/README.md) (SSOT); ergänzend [`docs/agents-docs/collaboration.md`](../docs/agents-docs/collaboration.md)
5. Implementierung aus GitHub-Issue: [`.agents/skills/implement-plan-workflow/SKILL.md`](./skills/implement-plan-workflow/SKILL.md); `gh`: [`docs/agents-docs/github-cli.md`](../docs/agents-docs/github-cli.md)

## Code-Sprache

### Für Agenten (verbindlich)

Agents **must** write and keep the following in **English** everywhere in repository source (backend, frontend, scripts the team maintains):

- **Line and block comments** (`#`, `//`, `/* */`, etc.).
- **Docstrings** and module-level file descriptions for Python, and equivalent documentation comments in other languages.
- **Inline documentation** embedded in code (e.g. JSDoc-style blocks where used).

Do **not** add or leave German (or other non-English) comments or docstrings in code; fix existing ones when touching a file. Review feedback should treat violations as blocking for merge.

**Exception messages and log lines** from application code: **English**, unless the product spec explicitly requires a localized user-facing string (then follow that spec). User-visible UI copy follows product language (e.g. Swiss German per product rules).

### Abgrenzung

- **Identifiers** (names of modules, classes, functions, variables): follow existing repo conventions; comments and docstrings stay English.
- **User-visible UI strings** (labels, prose in clients): **German (CH)** where the product requires it; that does not extend to developer-facing comments in source.

## Arbeit an einem Issue

- Tracker-Issue lesen; wenn im Body ein **Permalink** auf `docs/roadmap/.../issues/*.md` steht, ist **diese Markdown-Datei die kanonische Spec**.
- PRs verweisen auf dasselbe Issue (`Fixes #n` / `Closes #n` wo zutreffend).

## PRs

- Titel und Beschreibung sollen die verlinkte Spec oder Phase-README nennen, nicht nur freie Prosa.
