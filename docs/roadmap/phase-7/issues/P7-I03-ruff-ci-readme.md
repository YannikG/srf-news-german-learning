# [P7-I03] Ruff CI und README

## Meta

- **Phase:** 7
- **Issue ID:** P7-I03

## Dependencies

- [P7-I01](./P7-I01-pytest-suite.md)
- [P7-I02](./P7-I02-vitest-suite.md) (README soll beide Test-Befehle nennen)

## Goal

**ruff** für Lint und Format auf Backend; optional **mypy** strict subset; GitHub Actions oder dokumentierte Alternative; README: Quickstart Docker vom Root, venv, Tests, Umgebungsvariablen, Datenpfade `app.db` / `vectors.db`, Ollama-Modelle pull.

## Testable acceptance criteria

- [ ] `ruff check .` und `ruff format --check .` (oder format nur in CI-Check) grün im Backend-Paket.
- [ ] CI-Workflow-Datei existiert und läuft auf PR (oder README erklärt bewusstes Fehlen).
- [ ] README enthält alle in den Akzeptanzkriterien genannten Abschnitte.

## Dev lifecycle

1. Konfiguration; CI; README.
2. PR.

## Out of scope

- Deployment auf Kubernetes.
