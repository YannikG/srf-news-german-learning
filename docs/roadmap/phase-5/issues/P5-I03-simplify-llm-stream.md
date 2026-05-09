# [P5-I03] Vereinfachen LLM Stream und Persistenz

## Meta

- **Phase:** 5
- **Issue ID:** P5-I03

## Dependencies

- [P5-I02](./P5-I02-embeddings-retrieval.md)
- [P4-I03](../../phase-4/issues/P4-I03-sse-event-stream.md)
- [P2-I03](../../phase-2/issues/P2-I03-articles-read-fts.md)

## Goal

`POST /api/articles/{id}/simplify` mit CEFR-Level: Retrieval, Prompt, Ollama `gemma4:e2b` mit **Stream**; Chunks über **SSE** (`llm_chunk`); abschliessend validiertes JSON mit vereinfachtem Markdown, verwendeten Wörtern, 3–4 neuen Vorschlägen; Persistenz in `app.db` und neue Embeddings in `vectors.db`.

## Testable acceptance criteria

- [ ] `pytest` mit Stream-Fixture: unvollständiger Stream → definierter Fehler; gültiger Stream → DB-Zeilen wie erwartet.
- [ ] SSE-Events `llm_chunk` und `llm_done` sichtbar in einem Test oder dokumentiertem manuellen Protokoll.
- [ ] Bilder erscheinen nicht im gespeicherten Markdown.

## Dev lifecycle

1. Use-Case-Service; Pydantic-Output-Modelle.
2. Tests und SSE-Anbindung.
3. PR.

## Out of scope

- Vue-Darstellung (Phase 6).
