# SRGSSR Articles API v2 (Kurzreferenz)

Vollständige Maschinenlesbare Spezifikation: [`api/srgssr-articles-v2-openapi.yaml`](./api/srgssr-articles-v2-openapi.yaml) (OpenAPI 3.0.3, Version **2.0.0**). Quelle: vom Entwicklerportal exportierte OpenAPI-Datei.

## Basis

| Aspekt | Wert |
|--------|------|
| Server (laut Spec) | `https://api.srgssr.ch/srgssr-articles/v2` |
| Liste Artikel | `GET /articles` → vollständige URL `https://api.srgssr.ch/srgssr-articles/v2/articles` |
| Sicherheit | OAuth2 **clientCredentials** |
| Token-URL | `https://api.srgssr.ch/oauth/v1/accesstoken?grant_type=client_credentials` (wie in `components.securitySchemes.auth`) |

`GET /articles` erfordert laut Spec globale `security: [ auth: [] ]` (Bearer nach Token).

## Query-Parameter

| Parameter | Typ | Beschreibung |
|-----------|-----|----------------|
| `cursor` | `string \| null` | Cursor der vorherigen Antwort; weglassen für erste Seite; nur mit gleichen Filterkriterien gültig |
| `limit` | `integer` 1–10, Default 10 | Seitengrösse |
| `publisher` | `SRF` \| `RTS` \| `RSI` \| `RTR` \| `SWI` \| null | Filter nach Publisher; für SRF-News typischerweise `SRF` |

## Antwort 200 (`ArticlePage`)

- `cursor` (`string \| null`): für nächste Seite
- `results`: Array von `Article`-Objekten (siehe OpenAPI `components.schemas.Article`)

Wichtige Felder für die App (Mapping nach `app.db` / Markdown, ohne Bilder):

- **`id`**: PDP-Artikel-ID (externer Schlüssel)
- **`publisher`**, **`provenance`**
- **`title`**: Array von `Text` (`content`, `language`) → Titel für Anzeige und FTS
- **`lead`**: Array von `Text` → Teaser
- **`content.text`**: Array von Strings → Fliesstext (für `markdown_original` normalisieren)
- **`releaseDate`**, **`modificationDate`**: ISO-8601
- **`resources`**: kann `Picture`, `Document`, `Link` enthalten → **für v1 keine Bilder ausliefern**; URLs aus `Picture`/`Document` ignorieren oder strippen (Produktregel)

Weitere Felder (`contributors`, `genres`, `keywords`, `relatedArticles`, `accessConditions`, …) siehe YAML.

## Fehlercodes

- `401` Not Authorized  
- `403` Not Allowed  

## Hinweis zu Scopes

Die eingecheckte OpenAPI listet unter `clientCredentials` `scopes: {}`. Im Developer Portal können dennoch Scopes wie **Articles** gebunden sein. Vor Produktion mit echten Keys prüfen, ob zusätzliche Scope-Parameter am Token-Endpoint nötig sind.

## Nächster Schritt (Implementierung)

Parser und Fixtures gemäss Issue [P3-I02](../roadmap/phase-3/issues/P3-I02-articles-api-mapping.md); Ingest in [P3-I03](../roadmap/phase-3/issues/P3-I03-news-refresh-ingest.md).
