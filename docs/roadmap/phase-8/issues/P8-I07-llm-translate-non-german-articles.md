# [P8-I07] LLM: nicht-deutsche Artikel → Deutsch + CEFR

## Meta

- **Phase:** 8
- **Issue ID:** P8-I07

## Dependencies

- [P8-I04](./P8-I04-newsapi-org-client-and-mapping.md) (fremdsprachige Quellen typisch über NewsAPI)
- [P8-I05](./P8-I05-external-id-and-uniqueness.md)
- [P5-I03](../../phase-5/issues/P5-I03-simplify-llm-stream.md) (bestehende Vereinfachen-Pipeline)

## Goal

`ArticleSimplifyService` und `_build_prompts` in `backend/app/articles/simplify_service.py` gehen heute von **deutschsprachigen Schweizer News** aus. Für Artikel mit **Quellsprache ausserhalb** der Zielmenge (z. B. nicht `de` / `gsw`) muss die Pipeline **ins Deutsche übersetzen** und anschliessend auf das gewählte **CEFR** vereinfachen, strukturierte JSON-Ausgabe unverändert.

- **Persistenz:** Spalte oder zuverlässig ableitbare Metadaten `article_source_language` (NewsAPI-Feld `language`; SRGSSR aus Metadaten der Textblöcke).
- **Lexikon-Retrieval:** Läuft heute auf `markdown_original`; bei **fremdsprachigem** Text liefert ein deutsch ausgerichtetes Lexikon oder Embedding-Raum oft **keine** sinnvollen Treffer. Im Ticket mindestens eine Strategie festlegen und begründen, zum Beispiel: **(a)** Retrieval auf **zwischenübersetztem** deutschen Text (nach erstem LLM-Schritt oder Zwischenspeicherung); **(b)** für konfigurierte Nicht-Deutsch-Sprachen **kein** Lexikon-Retrieval, stattdessen **nur** LLM-generierte Vorschläge aus dem Kontext im Prompt (ohne `used_word_ids` aus der DB, oder mit leerem Lexikon-Snippet und klaren Prompt-Regeln); **(c)** zweistufiger Aufruf mit dokumentierter Latenz- und Kostenfolge. Tradeoffs kurz in der Spec oder im PR beschreiben.

## Testable acceptance criteria

- [ ] pytest: Artikel mit `article_source_language=en` (oder Fixture) erzeugt erwartetes Verhalten (Mock für LLM-Stream mit validem JSON-Output).
- [ ] **Keine Regression:** rein deutschsprachiger SRGSSR-Artikel verhält sich wie vorher (bestehende Tests grün).

## Dev lifecycle

1. Schema/API falls nötig für Quellsprache.
2. Prompt- und Service-Anpassung.
3. Tests mit Mocks.
4. PR.

## Out of scope

- Automatische Spracherkennung ohne Upstream-Signal (optional später).
