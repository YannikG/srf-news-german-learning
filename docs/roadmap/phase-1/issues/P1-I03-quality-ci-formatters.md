# [P1-I03] Formatierer, Prettier und GitHub Actions (Quality Gates)

## Meta

- **Phase:** 1
- **Issue ID:** P1-I03

## Dependencies

- [P1-I02](./P1-I02-flask-venv-health.md)

## Goal

Frühe **Quality Gates** im Fundament: einheitliche Formatierung für **Python**, **TypeScript** und **JavaScript**, plus **Prettier** für die üblichen Text- und Konfigurationsformate im Frontend-Bereich; **GitHub Actions**, die bei **Pull Requests** und bei **Push** auf den Default-Branch (z. B. `master`) laufen und bei Verstössen fehlschlagen; lokal ein **`pre-commit`-Hook** mit **Husky** (und üblicherweise **lint-staged**), der dieselben Ruff- und Prettier-Checks auf **gestagte Dateien** ausführt, damit beide Welten vor jedem Commit geprüft werden.

Phase 7 ([P7-I03](../../phase-7/issues/P7-I03-ruff-ci-readme.md)) baut darauf auf (schärfere Ruff-Regeln, README-Vollständigkeit, ggf. erweiterte Jobs), ersetzt diese Basis aber nicht willkürlich.

## Testable acceptance criteria

- [ ] **Python (Backend-Pfad aus P1-I01):** `ruff check` und `ruff format --check` lokal dokumentiert und in CI grün; Konfiguration eingecheckt (`pyproject.toml` und/oder `ruff.toml`).
- [ ] **TypeScript und JavaScript:** Prettier deckt die im Repo vorhandenen TS/JS-Dateien ab (mindestens unter dem Frontend-Pfad oder Platzhalter aus P1-I01); `.prettierrc` (oder gleichwertig) und `.prettierignore` liegen im Repo.
- [ ] **Prettier:** Läuft per `pnpm` oder `npm` (im README genannter Standardbefehl); `prettier --check` in CI für die definierten Pfade.
- [ ] **GitHub Actions:** Unter `.github/workflows/` mindestens ein Workflow mit Triggern **`pull_request`** und **`push`** auf den Default-Branch; Jobs führen die obigen Checks aus (Backend und Frontend getrennt oder Matrix, solange Fehler sichtbar sind).
- [ ] **Husky + `pre-commit`:** Nach `pnpm install` / `npm install` ist der Hook aktiv (`prepare`-Skript oder gleichwertig); bei `git commit` laufen auf **gestagten** Dateien mindestens **Ruff** (check, ggf. format fix) und **Prettier** (check oder write, einheitlich dokumentieren). Konfiguration über **lint-staged** (empfohlen) oder ein schlankes Husky-Shell-Skript, das beide Welten nacheinander aufruft.
- [ ] **README:** Kurzabschnitt „Linting und Formatierung“ mit Copy-Paste-Befehlen für lokal, Verweis auf CI, **einmalige** Husky-Aktivierung nach Clone, und Hinweis zum bewussten Umgehen (`git commit --no-verify` oder dokumentiertes `HUSKY=0`, nur für Ausnahmefälle).

## Dev lifecycle

1. Ruff für Python einführen (Version fixieren); keine unnötige Doppelspur zu Black, falls Ruff Format genutzt wird.
2. Prettier + ggf. `prettier-plugin-tailwindcss` nur wenn Tailwind-Konfiguration schon existiert; sonst ohne Plugin bis Phase 6 nachziehen (dann Issue-Kommentar oder Follow-up in P6-I01 verlinken).
3. Workflows so wählen, dass sie ohne Docker-Secrets und ohne Ollama laufen (reine statische Checks).
4. Husky installieren, `lint-staged` an `package.json` anbinden; Staging-Muster für `*.py` (Ruff) und für TS/JS/JSON/Vue/YAML/Markdown (Prettier) so wählen, dass sie mit dem Repo-Layout aus P1-I01 übereinstimmen.
5. PR verlinkt diese Spec.

## Out of scope

- Volle **mypy**-Strenge (Phase 7 optional).
- **ESLint**-Policy komplett (kann in Phase 6 oder 7 ergänzt werden; hier nur, wenn schon für CI nötig, minimal dokumentieren).
- Das Python-Tool **`pre-commit`** (pre-commit.com) als zweite parallele Hook-Engine zusätzlich zu Husky, ausser Team entscheidet bewusst dafür (ein Mechanismus genügt).
- Release-Pipelines, Deploy-Schlüssel, Codecov-Schwellen.
