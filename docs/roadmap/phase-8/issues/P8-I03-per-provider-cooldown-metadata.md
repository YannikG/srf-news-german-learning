# [P8-I03] Cooldown-Metadaten pro Provider

## Meta

- **Phase:** 8
- **Issue ID:** P8-I03

## Dependencies

- [P8-I02](./P8-I02-news-refresh-upstream-port-adapter.md)

## Goal

Der Refresh-Cooldown (heute 900 s, Konstante in `app/news/constants.py`) gilt **pro aktivem Ingest-Provider**, nicht global über alle Quellen. Metadaten in `srg_sync_metadata` (Tabellenname kann vorerst bleiben) nutzen **getrennte Keys** pro Provider, z. B. `last_successful_articles_fetch_at:srgssr` und `last_successful_articles_fetch_at:newsapi`.

**Nutzerfolg:** Wechsel von Provider A zu B: B darf sofort einen Upstream-Call starten, wenn für B kein Cooldown aktiv ist, unabhängig davon, wann A zuletzt erfolgreich gezogen hat.

**Migration:** Bestehenden globalen Key `last_successful_articles_fetch_at` in den Key für `srgssr` übernehmen, damit bestehende Deployments keinen zusätzlichen Cooldown erzwingen.

## Testable acceptance criteria

- [ ] `pytest` mit `freezegun`: erfolgreicher Refresh für Provider A setzt nur Key A; danach sofortiger Refresh mit aktivem Provider B führt zu echtem Fetch für B (gemockt), ohne 900 s Wartezeit von A.
- [ ] Zweiter Refresh für **denselben** Provider innerhalb des Cooldown-Fensters löst keinen HTTP-Call aus (`fetched: false`, `next_allowed_fetch_at` konsistent).
- [ ] Dokumentation der Key-Namen in README oder Konstanten-Kommentar.

## Dev lifecycle

1. Key-Schema definieren; Lesen/Schreiben in `NewsRefreshService` anpassen.
2. Tests mit zwei logischen Providern (Mocks).
3. PR.

## Out of scope

- Umbenennung der Tabelle `srg_sync_metadata` (optional späteres Issue).
