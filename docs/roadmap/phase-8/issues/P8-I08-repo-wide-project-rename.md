# [P8-I08] Repo-weiter Projekt-Rename (letztes Phase-8-Issue)

## Meta

- **Phase:** 8
- **Issue ID:** P8-I08

## Dependencies

- [P8-I01](./P8-I01-env-active-provider-and-article-news-provider.md)
- [P8-I02](./P8-I02-news-refresh-upstream-port-adapter.md)
- [P8-I03](./P8-I03-per-provider-cooldown-metadata.md)
- [P8-I04](./P8-I04-newsapi-org-client-and-mapping.md)
- [P8-I05](./P8-I05-external-id-and-uniqueness.md)
- [P8-I07](./P8-I07-llm-translate-non-german-articles.md)

**Voraussetzung:** Issues **P8-I01 bis P8-I07** sind umgesetzt und stabil. Dieses Issue ist **ein separater, fokussierter Rename-Track** (idealerweise eigener PR ohne neue Feature-Logik).

## Goal

Vollständige Umbenennung des **Produkts und Repos** auf den finalen Namen (**News-Language-Lern** als Arbeitstitel; endgültige Schreibweise in diesem Ticket beim Start fixieren). SRGSSR bleibt nur **News-Provider**, nicht der Projektname.

**Umfang (Checkliste, alles was zutrifft):**

- [ ] `compose.yaml`: Service-Namen, Image-Namen, Netzwerke, Volumes, `container_name` falls verwendet.
- [ ] Dockerfiles: `AS`-Stages, `LABEL`, Image-Referenzen.
- [ ] `package.json` / Lockfile-Metadaten, Vite- und Frontend-Titel.
- [ ] CI unter `.github/workflows`: Pfade, Namen, Anzeige-Strings.
- [ ] Python: User-Agent-Defaults, Paket-README, **interne Importpfade** soweit nicht schon in P8-I02 erledigt.
- [ ] Doku: `docs/roadmap`, Root-README, alle sichtbaren Produkt-Strings.
- [ ] Frontend: verbleibende hardcodierte Produkt-Strings und Fehlertoasts (`frontend/src/news/notifyPostNewsRefresh.ts` etc.).

**Ausnahme (explizit nicht umbenennen):**

- Vendor-**Umgebungsvariablen** und URLs, die die **SRGSSR-API** verlangt (`SRGSSR_CONSUMER_KEY`, Token-URL, Articles-Base-URL, …). Optional nur **zusätzliche** dokumentierte Aliase, wenn es die Ops vereinfacht, ohne die Vendor-Doku zu brechen.

## Testable acceptance criteria

- [ ] `docker compose config` valide; `docker compose build` erfolgreich (lokal oder CI).
- [ ] `pytest` und Frontend-Tests grün nach Rename.
- [ ] Grep- oder Review-Checkliste: keine alten **Produkt**-Namen an dokumentierten Stellen (Ausnahmen Vendor oben).

## Dev lifecycle

1. Finalen Projektnamen und Schreibweise festlegen.
2. Checkliste abarbeiten; ein PR bevorzugt.
3. Review mit Fokus auf CI und Compose.
4. Merge.

## Ausserhalb dieses Issues (manuell durch Projektinhaber)

- **GitHub-Repository umbenennen** und lokales `git remote set-url` anpassen.
- Öffentliche Links, Badges, Deployment-Ziele aktualisieren.

## Out of scope

- Markenrecht, Domains, Rechtsgutachten.
