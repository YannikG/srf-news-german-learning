# [P6-I06] Optional: PONS-Abfrage und „Übersetzung anzeigen“ auf Knopfdruck

## Meta

- **Phase:** 6
- **Issue ID:** P6-I06
- **Priorität:** optional (nach MVP; Feature-Flag)

## Dependencies

- [P6-I03](./P6-I03-dictionary-ui.md)
- [P2-I02](../../phase-2/issues/P2-I02-words-api.md)
- Kurzreferenz [`docs/pons-dictionary-api.md`](../../../pons-dictionary-api.md)

## Goal

**Keine** automatischen oder periodischen PONS-Aufrufe. Der Nutzer löst **manuell** eine Abfrage aus:

1. **„Definition / Übersetzung holen“** (oder gleichlautender Button) pro Wörterbuchzeile: ein Request ans Backend, Backend ruft PONS **nur für diesen** Suchbegriff auf (Proxy mit `X-Secret` aus der Konfiguration).
2. **„Übersetzung anzeigen“** für Zeilen **ohne** gespeicherte Nutzer-Übersetzung: UI zeigt zuerst keinen externen Text (oder Platzhalter); erst nach Klick wird derselbe On-Demand-Flow ausgeführt und das Ergebnis **angezeigt** (z. B. Popover, Aufklappbereich oder zweite Zeile). Optional zweiter Schritt **„In Feld übernehmen“**, der den Vorschlag in das editierbare Übersetzungsfeld schreibt; **Speichern** bleibt eine bewusste Nutzeraktion (wie beim restlichen CRUD).

Ziel: Kontingente schonen, Secret im Browser vermeiden, Offline-Verhalten klar (Button deaktiviert oder Meldung, wenn Feature aus oder PONS nicht erreichbar).

## Testable acceptance criteria

- [ ] Ohne gesetztes `PONS_API_SECRET` (oder Feature-Flag aus) sind PONS-Buttons **nicht** sichtbar oder klar deaktiviert; **kein** Aufruf zu `api.pons.com` aus dem Frontend.
- [ ] Ein Klick auf „holen“ / „anzeigen“ erzeugt **genau einen** Backend-Request pro Aktion; kein Polling und kein Batch über alle Wörter.
- [ ] HTTP **204** / **403** / **503** aus PONS werden in der UI lesbar gemeldet, ohne Stacktrace zu leaken.
- [ ] `pytest` für die Proxy-Route mit `httpx`-Mock (Erfolg, 204, 403); `vitest` für UI-Zustand (vor Klick / nach Klick / Fehler).
- [ ] Dokumentation in README oder `docs/pons-dictionary-api.md`: Feature-Flag, Env-Variable, gewähltes `l` aus Nutzersprache (`deen`, `deuk`, …) und Fallback-Verhalten.

## Dev lifecycle

1. Backend-Route(n) definieren (z. B. `GET /api/external/pons/dictionary?q=&l=` intern nur mit erlaubtem `l` aus Server-Konfiguration).
2. Wörterbuch-UI erweitern; keine Änderung am Pflicht-CRUD ohne PONS.
3. Tests und Doku.
4. PR; Tracker-Issue mit Permalink zu dieser Spec.

## Out of scope

- Automatisches Befüllen aller fehlenden Übersetzungen im Hintergrund.
- PONS als einzige Quelle der Wahrheit (Nutzerfeld bleibt führend nach Übernahme).
