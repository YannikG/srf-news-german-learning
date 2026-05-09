---
name: github-issue-anlegen
description: >-
  User: Skill + Pfad zu docs/roadmap/phase-N/issues/*.md. Agent: Phase-README-Tabelle
  → Titel; Body = Kurztext + ein Permalink; Abhängigkeiten aus MD parsen, per
  gh issue list auf # mappen, gh issue create; Verknüpfung per gh/api oder Hinweis
  UI. SSOT: docs/zusammenarbeit/README.md.
disable-model-invocation: true
---

# GitHub-Issue anlegen

SSOT: `docs/zusammenarbeit/README.md`.

**Input:** dieses Skill-Dok + **Pfad** `docs/roadmap/phase-N/issues/….md`. Fehlt → einmal nach Pfad fragen.

**Flow**

1. `issues/*.md` lesen (ID: Dateiname / Kopfblock).
2. `docs/roadmap/phase-N/README.md` Tabelle → **GitHub-Titel** exakt aus Spalte.
3. Permalink: `https://github.com/<org>/<repo>/blob/<default>/docs/roadmap/phase-N/issues/<file>.md` — org/repo/branch via `git remote` / `gh repo view` (meist `main`).
4. Body = **ein** Kontextsatz + **eine** Permalink-Zeile. Kein Spez-Copy aus `.md`.

5. **Dep-IDs** aus `.md` parsen (kein User-Fragen wenn eindeutig): Links unter `## Abhängigkeiten` → `./…md` gleicher Ordner; `## Meta` **Blockiert von**; Kopfblock `Blockiert von:`. IDs `P4-Iyy` sammeln, **aktuelle** Datei raus, Dedupe.

6. Pro ID: Tabellentitel gleiche README → `gh issue list --json number,title --state all` (Limit / `--search [P4-Iyy]`). `title` enthält `[P4-Iyy]` oder match Tabellentitel → eine `#`. 0 oder mehrere gleich gut → Chat kurz + Begründung oder einmal nachfragen.

7. `gh issue create` wenn Netz+Auth (Body mehrzeilig → `--body-file`). Sonst Titel+Body+Kommando ausgeben. Neue Nummer **N** merken.

8. Deps auf GitHub: `gh issue create`/`gh issue edit --help` → Flags für Links/Block wenn da; sonst `gh api` nur wenn Mutation sicher bekannt; sonst Chat: `N` + `#`-Liste → User kurz Web-UI.

9. Output: Link `#N` + welche Deps erkannt + welche `#` + Schritt 8 auto oder manuell.

**Inhalt (nicht verletzen)**

- Titel = Tabelle Phase-README.
- Body = Kurz + **ein** Permalink `…/issues/….md` (org/repo/branch real).
- Deps = Schritte 5–6 + 8.
