# [P8-I02] News-Refresh: Upstream-Port und Adapter

## Meta

- **Phase:** 8
- **Issue ID:** P8-I02

## Dependencies

- [P8-I01](./P8-I01-env-active-provider-and-article-news-provider.md)
- [P3-I03](../../phase-3/issues/P3-I03-news-refresh-ingest.md)

## Goal

`NewsRefreshService` und `build_default_news_refresh_service` sind von konkreten SRGSSR-Typen (`SrgOAuthClient`, `SrgArticlesApiClient`) entkoppelt. Es gibt eine **Upstream-Port**-Schnittstelle (z. B. Abruf einer Seite mit Limit und Cursor, Rückgabe normalisierter Upsert-Zeilen für `articles`) plus **Adapter** pro Provider. Die Factory wählt den Adapter anhand von [P8-I01](./P8-I01-env-active-provider-and-article-news-provider.md).

**Parität:** Bestehendes SRGSSR-Verhalten (OAuth, Articles-API, Fehler-Mapping auf `upstream_auth`, `upstream_rate_limited`, `upstream_error`) bleibt für den Adapter `srgssr` erhalten.

## Testable acceptance criteria

- [ ] `pytest` injiziert weiterhin Test-Doubles über `app.config["NEWS_REFRESH_SERVICE"]` oder gleichwertig (siehe bestehende `backend/tests/test_news_refresh.py`).
- [ ] Mit aktivem `srgssr` und gemocktem HTTP: gleiche Cooldown- und Upsert-Semantik wie vor Refactor (Regression gegen [P3-I03](../../phase-3/issues/P3-I03-news-refresh-ingest.md)).
- [ ] Kein Netzwerk im Standard-pytest-Lauf.

## Dev lifecycle

1. Port-Interface und SRGSSR-Adapter extrahieren; Service nur noch gegen Port programmieren.
2. Factory an Settings hängen.
3. Tests anpassen und ergänzen.
4. PR.

## Out of scope

- NewsAPI-Adapter-Implementierung (siehe [P8-I04](./P8-I04-newsapi-org-client-and-mapping.md)); hier nur die Erweiterbarkeit und SRGSSR-Adapter.

## Hinweis

**Paket-Umbenennung** `app/srg_*` → neutralere Pfade ist optional in diesem Issue; sonst Bündelung in [P8-I08](./P8-I08-repo-wide-project-rename.md).
