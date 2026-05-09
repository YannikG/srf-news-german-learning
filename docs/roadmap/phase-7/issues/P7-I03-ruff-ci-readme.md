# [P7-I03] Ruff CI und README

## Meta

- **Phase:** 7
- **Issue ID:** P7-I03

## Dependencies

- [P7-I01](./P7-I01-pytest-suite.md)
- [P7-I02](./P7-I02-vitest-suite.md) (README soll beide Test-Befehle nennen)
- [P1-I03](../../phase-1/issues/P1-I03-quality-ci-formatters.md) (Quality-Gates-Basis aus Phase 1 erweitern, nicht parallel zerstören)

## Goal

**ruff** für Lint und Format auf Backend **verschärfen und vervollständigen** (inkl. Regelset, ggf. CI-Cache, gleicher Workflow-Stil wie in Phase 1); optional **mypy** strict subset; GitHub Actions **ergänzen** (z. B. Vitest-Job, Artefakte), ohne die P1-I03-Triggers zu brechen; README: Quickstart Docker vom Root, venv, Tests, Umgebungsvariablen, Datenpfade `app.db` / `vectors.db`, Ollama-Modelle pull.

## Testable acceptance criteria

- [ ] `ruff check .` und `ruff format --check .` (oder format nur in CI-Check) grün im Backend-Paket; Konfig baut auf [P1-I03](../../phase-1/issues/P1-I03-quality-ci-formatters.md) auf (keine widersprüchlichen Doppelpipelines ohne Begründung im PR).
- [ ] CI-Workflow-Dateien laufen auf PR und auf Push zum Default-Branch (wie in Phase 1); zusätzliche Jobs (Vitest, ggf. Matrix) sind dokumentiert.
- [ ] README enthält alle in den Akzeptanzkriterien genannten Abschnitte.

## Dev lifecycle

1. Konfiguration; CI; README.
2. PR.

## Out of scope

- Deployment auf Kubernetes.
