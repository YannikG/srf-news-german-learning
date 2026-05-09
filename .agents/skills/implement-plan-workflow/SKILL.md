---
name: implement-plan-workflow
description: >-
  Immer GitHub-Issue URL oder #. Body enthält blob-URL zu docs/roadmap/…/issues/*.md
  → diese MD im Workspace = Spez, nicht im Impl-PR editieren. Kein Permalink
  → Spez = Issue-Titel+Body (+optional gh issue view --comments). Kein gh issue
  create. Branch: gh issue develop. Während Code: caveman; danach: review-and-fix.
disable-model-invocation: true
---

# Implement plan workflow

**Immer** GitHub-Issue (URL oder #). Kein `gh issue create` zum Start.

**Spez zwei Wege**

| Fall | Wann | Spez |
|------|------|------|
| Roadmap | Body hat URL mit `…/docs/roadmap/…/issues/….md` (blob/raw) | Pfad im Checkout **Read** komplett. **Kein** Patch auf `docs/roadmap/**/issues/**/*.md` im Impl-PR, ausser User will explizit Planänderung dort. Code/Tests/Config ja. Plan-Edits nur sachlich, kein gh-Blabla in MD (`.agents/AGENTS.md`). |
| Nur Issue | kein solcher Link | Titel + Body; nötig `gh issue view <n> --comments`. Keine fake Roadmap-`.md`. |

Repo: `.agents/AGENTS.md`, `docs/agents-docs/README.md`, `docs/zusammenarbeit/README.md`.

**Companion:** impl → [`.agents/skills/caveman/SKILL.md`](./caveman/SKILL.md); Ende → [`.agents/skills/review-and-fix/SKILL.md`](./review-and-fix/SKILL.md).

**Pre:** working tree clean sonst stop+fragen; `gh` login; Issue URL/# Pflicht sonst einmal nachfragen — **nie** Ersatz-Issue selbst anlegen.

**S1 — Spec locken**

1. `gh issue view` (URL parsen) → Titel, Body.
2. Body scannen: `…/docs/roadmap/…/issues/….md` → wenn ja: Pfad im Checkout laden (**Read**), = Roadmap-Fall.
3. Roadmap: nur diese MD als Plan/Aks. Nur-Issue: Spec = Text (+Comments).
4. **Beide:** kein `gh issue edit` mit riesigem Plan/Impl-Text aus Chat drüberpinseln. Kurz-Status nur wenn User will.

**S2 — Branch:** `git fetch`, default checkout, `pull` → `gh issue develop <n> --checkout` (`-n name` siehe `docs/agents-docs/github-cli.md`). Nicht auf default branch coden.

**S3 — Impl:** gegen Spec aus S1. Produkt ausserhalb `docs/roadmap/**/issues/` ausser Team will anders.

**S4 — Exit:** `review-and-fix`; Findings gegen gleiche Spec wie S1; Exit laut review-and-fix Skill.

**Trigger:** «implement … issue …»; start implementing + # im Kontext; execute plan + ref; `/implement-plan` + ref. Ohne ref → # holen, kein fake issue.
