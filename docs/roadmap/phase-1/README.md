# Phase 1: Fundament

**Endzustand:** Vom Repository-Root startet der Stack mit `docker compose up` bzw. `docker compose up -d`; der Web-Container liefert einen verifizierbaren Health-Endpoint; lokales Backend-Setup ist mit `venv` und `requirements.txt` dokumentiert; **Ruff** und **Prettier** sind konfiguriert; **GitHub Actions** laufen bei PR und Push auf den Default-Branch und prüfen Format sowie Lint (Quality Gates); **Husky** (mit **lint-staged**) führt vor jedem Commit dieselben Checks auf gestagten Dateien aus.

## DoD

- [ ] `docker-compose.yml` (oder `compose.yaml`) im Projektroot; `docker compose config` ohne Fehler.
- [ ] `docker compose up` zeigt Logs; `docker compose up -d` startet detached; `docker compose down` ohne `-v` erhält Daten-Volumes falls schon definiert.
- [ ] `GET /api/health` (oder gleichwertig) im Web-Image antwortet mit JSON und HTTP 200 in einem Smoke-Test (manuell oder Skript).
- [ ] README-Abschnitt: `python -m venv`, `pip install -r requirements.txt` für das Backend-Verzeichnis.
- [ ] CI-Workflows auf `pull_request` und `push` (Default-Branch): `ruff check` / `ruff format --check` (Backend) und `prettier --check` (TS/JS gemäss Repo-Layout) grün; lokale Befehle im README.
- [ ] Husky-`pre-commit`-Hook mit Ruff und Prettier für gestagte Dateien dokumentiert und nach Standard-Clone-Anleitung aktiv.

## Issues

| ID | Titel | Spec |
|----|--------|------|
| P1-I01 | Monorepo-Layout und Docker Compose | [issues/P1-I01-monorepo-docker-compose.md](./issues/P1-I01-monorepo-docker-compose.md) |
| P1-I02 | Flask App Factory und Health | [issues/P1-I02-flask-venv-health.md](./issues/P1-I02-flask-venv-health.md) |
| P1-I03 | Formatierer, Prettier und GitHub Actions (Quality Gates) | [issues/P1-I03-quality-ci-formatters.md](./issues/P1-I03-quality-ci-formatters.md) |

## Issue-Graph

```mermaid
flowchart TB
  I01[P1-I01]
  I02[P1-I02]
  I03[P1-I03]
  I01 --> I02
  I02 --> I03
```
