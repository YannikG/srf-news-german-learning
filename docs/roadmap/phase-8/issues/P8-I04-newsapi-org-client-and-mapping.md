# [P8-I04] NewsAPI.org Client und Mapping

## Meta

- **Phase:** 8
- **Issue ID:** P8-I04

## Dependencies

- [P8-I02](./P8-I02-news-refresh-upstream-port-adapter.md)
- [P8-I05](./P8-I05-external-id-and-uniqueness.md) (Konvention für `external_id` und `news_provider` beim Upsert)

## Goal

Implementierung eines **NewsAPI.org**-Adapters für den News-Refresh-Port:

- **HTTP:** Eigener schlanker Client mit **`httpx`** (wie SRGSSR), **kein** zusätzliches Pflicht-Dependency auf das inoffizielle Paket `newsapi-python` ([Python client library](https://newsapi.org/docs/client-libraries/python)), ausser im Ticket bewusst anders dokumentiert.
- **Authentifizierung:** API-Key über **`X-Api-Key`-Header** ([Authentication](https://newsapi.org/docs/authentication)), nicht als `apiKey`-Querystring (weniger Leak-Risiko in Logs).
- **Endpunkte:** Spec wählt `everything` und/oder `top-headlines` inkl. sinnvoller Default-Parameter (Sprache, Land, Query) über `.env` (z. B. `NEWSAPI_DEFAULT_LANGUAGE=de`).
- **`/v2/everything`:** Laut NewsAPI-Dokumentation ist mindestens eines von **`q`**, **`sources`** oder **`domains`** erforderlich; sonst droht HTTP **400**. Die Spec muss daher für den Endpoint `everything` eine **Default-Suchbedingung** vorsehen, z. B. Umgebungsvariable **`NEWSAPI_DEFAULT_QUERY`** (nicht-leer nach Trim) oder verbindliche `NEWSAPI_DOMAINS` / `NEWSAPI_SOURCES`. Beim App-Start validieren: ist `everything` aktiv, fehlen alle drei → klare Konfigurationsfehlermeldung statt stummer 400 vom Upstream.
- **Mapping:** Antwort-Artikel → SQLite-Spalten inkl. `news_provider = newsapi`, Titel, Teaser/Lead, Fliesstext als Markdown-kompatibel, Daten; SRGSSR-Mapping als Qualitätsreferenz (`map_article_to_app_db_fields`).
- **Feld `language`:** Pro Artikel wo vorhanden persistieren (Synergie mit [P8-I07](./P8-I07-llm-translate-non-german-articles.md)).
- **Fehler:** 401, 429 und sonstige HTTP-Fehler nutzer- bzw. API-tauglich mappen (analog zu SRGSSR-Codes).

## Testable acceptance criteria

- [ ] pytest mit `httpx`-Mock oder `respx`: erfolgreiche Seite, 401, 429.
- [ ] Fixture-JSON (redigiert) für Response-Shape; Mapper-Tests.
- [ ] Kein Netzwerk im Default-Lauf.

## Dev lifecycle

1. Settings-Modell (`NEWSAPI_API_KEY`, Basis-URL optional, Query-Defaults).
2. Client + Adapter am Port.
3. Mapper + Tests.
4. README und `.env.example`.
5. PR.

## Out of scope

- Rechtliche oder kommerzielle Bewertung der NewsAPI-Nutzung (nur Link in README).
- UI-Badge (siehe [P8-I01](./P8-I01-env-active-provider-and-article-news-provider.md)).
