# [P2-I05] Backend-pytest in CI und Teststrategie

## Meta

- **Phase:** 2
- **Issue ID:** P2-I05

## Dependencies

- [P2-I01](./P2-I01-app-db-schema.md) (stabiles Schema und Migrationspfad für Test-DBs)
- [P1-I03](../../phase-1/issues/P1-I03-quality-ci-formatters.md) (bestehende Quality-Workflows auf PR und Push; Erweiterung ohne Trigger oder Pfade willkürlich zu brechen)

## Goal

**pytest** für das Backend läuft in **GitHub Actions** bei **Pull Requests** und bei **Push** auf den Default-Branch (gleiche Trigger wie der Quality-Workflow aus Phase 1), sichtbar als eigener Job (z. B. Erweiterung von [`.github/workflows/quality.yml`](../../../../.github/workflows/quality.yml) oder klar benannter Zusatzworkflow im selben Stil). Lokaler Standardbefehl ist im **Backend-README** dokumentiert (venv, Arbeitsverzeichnis `backend`).

Die Issue bündelt die **CI-Schicht** und eine knappe **Teststrategie** für Phase 2: bestehende Integrations- und API-Tests bleiben die Basis; wo sinnvoll, **fokussierte Unit-Tests** (z. B. reine Parser, Cursor-Helfer, FTS-Query-Aufbereitung ohne Flask-Client) ergänzen, ohne P7-Umfang vorwegzunehmen.

## Testable acceptance criteria

- [ ] GitHub Actions: Job **Backend (pytest)** (oder gleichwertiger Name) mit `python-version` passend zum Docker-Backend (z. B. 3.12), Installation aus `backend/requirements.txt` und `backend/requirements-dev.txt`, dann `pytest` aus dem Verzeichnis `backend`; Pipeline bei rotem Test rot.
- [ ] Kein bewusster Netzwerkzugriff für den Standardlauf (keine SRG-/Ollama-Aufrufe; bestehende Tests bleiben offline).
- [ ] README-Abschnitt oder bestehender „Local setup“-Block: Copy-Paste für `pytest` und Verweis, dass dieselbe Suite in CI läuft.
- [ ] Kurz in der PR-Beschreibung oder im Issue-Kommentar vermerkbar: welche Schichten Phase-2-Tests abdecken (API-Integration vs. kleine Unit-Helfer).

## Dev lifecycle

1. Workflow und Abhängigkeiten (Cache optional, analog Ruff-Job).
2. README und ggf. minimale Unit-Tests ergänzen, wo Risiko ohne CI wieder einbricht.
3. PR.

## Out of scope

- Vitest und Frontend-Testjobs (eigene Phase-6/7-Stories).
- Volle Edge-Case-Matrix und Coverage-Schwellen: [P7-I01](../../phase-7/issues/P7-I01-pytest-suite.md).
- `pytest-cov`-Pflicht oder mypy strict (optional später, z. B. [P7-I03](../../phase-7/issues/P7-I03-ruff-ci-readme.md)).

## Hinweis zur Roadmap

Phase 7 [P7-I01](../../phase-7/issues/P7-I01-pytest-suite.md) baut auf einem **reifen Feature-Stand** auf und vertieft Abdeckung und Grenzfälle. **P2-I05** liefert das frühe **Sicherheitsnetz in CI**, damit Phase-2-Änderungen nicht nur lokal per pytest laufen.
