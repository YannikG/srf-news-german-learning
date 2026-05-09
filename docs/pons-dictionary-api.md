# PONS Dictionary API (Kurzreferenz)

Öffentliche Doku-Kernpunkte, normalisierte URLs (ohne Leerzeichen). **Nutzung in dieser App: optional** (siehe Abschnitt „Eignung“).

## Offizielle Dokumentation

Vollständige API-Beschreibung (Parameter, Antwortschemata, Beispiele) als PDF:

- [PONS Dictionary API (PDF)](https://en.pons.com/assets/docs/api_dict.pdf)

## Endpunkte

| Zweck | Methode | URL |
|--------|---------|-----|
| Verfügbare Wörterbücher | `GET` | `https://api.pons.com/v1/dictionaries` |
| Abfrage / Suche | `GET` | `https://api.pons.com/v1/dictionary` |

## `GET /v1/dictionaries`

**Query**

- `language` (ISO 639-1): Ausgabesprache der Labels, z. B. `de`, `en`, …; unsupported → Default Englisch.

**Antwort (JSON):** Array von Objekten mit u. a.:

- `key`: interner Name (zwei Sprachen oft alphabetisch, z. B. `deen`)
- `simple_label`, `directed_label` (Richtung z. B. `de » en`)
- `languages`: Liste der Sprachen

## `GET /v1/dictionary`

**Header**

- `X-Secret`: API-Secret (nicht im Repo speichern; nur `.env` / Secrets-Store).

**Query**

| Parameter | Pflicht | Beschreibung |
|-----------|---------|--------------|
| `q` | ja | Suchbegriff (UTF-8, URL-escaped) |
| `l` | ja | Wörterbuch-Key (z. B. `deen`, `dees`; siehe PONS-Web-Suche) |
| `in` | nein | Quellsprache des Suchterms (Richtung) |
| `fm` | nein | `fm=1` → fuzzy matching |
| `ref` | nein | `ref=true` → Referenzen (siehe Doku „References“) |
| `language` | nein | Ausgabesprache der Metadaten (wie bei dictionaries) |

**Beispiel**

```http
GET https://api.pons.com/v1/dictionary?q=Haus&l=deen
X-Secret: <dein-secret>
```

## HTTP-Status (Auszug)

| Code | Bedeutung |
|------|------------|
| 200 | OK (Treffer möglich) |
| 204 | Kein Treffer |
| 404 | Wörterbuch `l` existiert nicht |
| 403 | Secret ungültig oder Dictionary nicht erlaubt |
| 500 | Serverfehler |
| 503 | Tageslimit erreicht |

## Antwortstruktur (vereinfacht)

- Treffer in `hits`: u. a. `type: "entry"` mit `roms[]` → `arabs[]` → `translations[]` mit `source` / `target`; oder `type: "translation"` mit `source` / `target`.
- Mit `ref=true`: u. a. `entry_with_secondary_entries` mit `primary_entry` und `secondary_entries`.

Details und Beispiele: [PONS Dictionary API (PDF)](https://en.pons.com/assets/docs/api_dict.pdf).

## Eignung für diese Projekt-Roadmap

| Aspekt | Bewertung |
|--------|------------|
| **MVP Wörterbuch** | **Nicht nötig:** Nutzer trägt Übersetzungen selbst ein (Spec Phase 2/6). |
| **Mehrwert** | **Ja:** **Nur auf Knopfdruck** (kein Dauerabruf): z. B. **„Übersetzung anzeigen“** wenn noch keine Nutzer-Übersetzung gespeichert ist, plus **„Definition holen“** / PONS-Vorschlag; passende `l`-Keys zu Einstellungen (`deen`, `deuk`, …), optional Fuzzy (`fm=1`); **„In Feld übernehmen“** optional getrennt vom Speichern. |
| **Architektur** | Nur über **Backend-Proxy** (Secret nie an den Browser); Rate Limits und **503** sauber behandeln; Feature-Flag. |
| **„Alles lokal“** | PONS ist **extern**; ohne Netzwerk oder bei strikt offline-only **deaktivieren**. |

## Rechtliches und Betrieb

Nutzungsbedingungen, Schlüsselvergabe und Kontingente **bei PONS** klären; Secret nur in Umgebungsvariablen (z. B. `PONS_API_SECRET`).

## Roadmap

Umgesetzt als **optionales** Issue [P6-I06](../roadmap/phase-6/issues/P6-I06-optional-pons-on-demand.md): On-Demand-Proxy, UI **„Übersetzung anzeigen“** für leere Felder, kein Batch.
