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
- **Lexikon-Retrieval:** Läuft auf `markdown_original`; bei Fremdsprache schwach — im Ticket eine Lösung festlegen (z. B. ein kombinierter LLM-Schritt Übersetzung+Vereinfachung+Vorschläge, oder zweistufig; Latenz/Kosten kurz dokumentieren).

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
