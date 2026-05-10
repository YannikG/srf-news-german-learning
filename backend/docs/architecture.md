# Backend-Architektur: Schichten und Wiring

## Überblick

Das Backend trennt **HTTP**, **Anwendungslogik** und **Persistenz**:

| Schicht | Rolle | Beispiel |
|--------|--------|----------|
| **Routes** (Flask-Blueprint) | Request parsen, Statuscodes und JSON; keine Geschäftsregeln | `app/words/routes.py`, `app/articles/routes.py`, `app/settings/routes.py` |
| **Service** | Validierung, Fehler semantisch (z. B. 404), Orchestrierung | `app/words/service.py`, `app/articles/service.py`, `app/settings/service.py` |
| **Repository** | SQL und Tabellen-Mapping; keine HTTP-Kenntnis | `app/words/repository.py`, `app/articles/repository.py`, `app/settings/repository.py` |
| **Datenbank-Hülle** | SQLAlchemy-``Engine`` (Core, kein ORM), ``PRAGMA foreign_keys``, Transaktionen via ``begin()`` | `app/persistence/sqlite_engine.py` (gemeinsame Engine-Erzeugung), `sqlite_db.py` / `vectors_db.py` |

Migrationen und idempotentes Anlegen der Datei bleiben in `app/db/` (stdlib-``sqlite3``, SQL-Dateien; gemeinsame Buchhaltung in ``migration_bookkeeping``, atomare ``executescript``-Läufe in ``migration_tx``) für **``app.db``**. Für **``vectors.db``** (Phase 5, P5-I01) liegen SQL und Bootstrap in ``app/vectors/`` (sqlite-vec ``vec0``). **Repositories** sprechen die jeweilige Datei über **SQLAlchemy 2.0 Core** (`Engine`, `text()`, gebundene Parameter, ``RowMapping`` → ``dict``), ohne Mapper-Klassen für Entitäten.

**Hinweis:** Pro Repository-Operation ``with db.begin() as conn:`` — entspricht einer Transaktion mit Commit bei Erfolg und Rollback bei Fehler (ersetzt das frühere manuelle ``commit()`` auf roher ``sqlite3``-Connection).

## Repository-Pattern

- **`WordsRepositoryPort`** (`app/words/ports.py`): `typing.Protocol` beschreibt die Methoden, die der **WordsService** von der Persistenz erwartet. So bleibt der Service testbar und unabhängig von SQLite-Details.
- **`SqliteWordsRepository`** (`app/words/repository.py`): konkrete Implementierung; erhält `SqlDatabase`, pro Operation ``with db.begin() as conn`` und ``conn.execute(text(...), params)``.
- **`ArticlesRepositoryPort`** / **`SqliteArticlesRepository`** (`app/articles/ports.py`, `app/articles/repository.py`): gleiches Muster für lesende Artikel-API inkl. FTS5-Titelsuche (Migration ``003_articles_fts``).
- **`SettingsRepositoryPort`** / **`SqliteSettingsRepository`** (`app/settings/ports.py`, `app/settings/repository.py`): eine Zeile ``settings`` (``id = 1``); `GET/PATCH /api/settings`.
- **`WordEmbeddingsRepository`** (`app/vectors/repository.py`): Schreiben und KNN auf der virtuellen Tabelle ``word_embeddings`` (sqlite-vec); erhält **`VectorsDatabase`**, kein HTTP.

Neue Tabellen: eigenes `…RepositoryPort` + `Sqlite…Repository`, Service darauf aufbauen.

## Service-Pattern

**`WordsService`** erhält im Konstruktor ein Objekt, das `WordsRepositoryPort` erfüllt. Er validiert Eingaben, wirft bei Regelverletzungen **`WordServiceError`** (mit HTTP-Status), mappt keine SQL-Strings.

**`ArticlesService`** nutzt **`ArticlesRepositoryPort`** und wirft bei Regelverletzungen **`ArticleServiceError`** (analog JSON-Fehlerantwort).

**`SettingsService`** validiert CEFR-Stufen, Übersetzungssprache und optional ``retrieval_top_k`` sowie ``retrieval_context_max_chars``; bei Regelverletzungen **`SettingsServiceError`**.

## Flask-Wiring

1. In **`create_app`** (`app/bootstrap/factory.py`, exportiert über ``app``): sobald `DATABASE_PATH` gesetzt ist, wird **`SqlDatabase`** erzeugt und unter dem Schlüssel aus **`SQL_DATABASE_EXTENSION_KEY`** (aktuell `"sql_database"`) in **`app.extensions`** abgelegt. Zusätzlich wird **`VECTORS_DATABASE_PATH`** standardmässig auf ``vectors.db`` im gleichen Verzeichnis wie ``app.db`` gesetzt; sobald dieser Pfad gesetzt ist, werden **`VectorsDatabase`** und fehlende Datei-Bootstrap (sqlite-vec) unter **`VECTORS_DATABASE_EXTENSION_KEY`** registriert.
2. Routen holen die Instanz mit **`current_app.extensions[…]`** und rufen **`build_words_service(db)`**, **`build_articles_service(db)`** oder **`build_settings_service(db)`** (`app/words/factory.py`, `app/articles/factory.py`, `app/settings/factory.py`) auf. Das sind die **Fabrik-Stellen**, an denen Service und Repository zusammengesteckt werden (kein verstecktes `new` in den Views). Für Vektoren in ``vectors.db`` dient **`build_word_embeddings_repository(vectors_db)`** (`app/vectors/factory.py`). **Phase 5 (P5-I02):** **`OllamaEmbedClient`** (`app/ollama/embeddings.py`) ruft Ollama ``POST /api/embed`` auf; **`LexiconRetrievalService`** (`app/retrieval/service.py`, Fabrik **`build_lexicon_retrieval_service`** in ``app/retrieval/factory.py``) kombiniert Embeddings, KNN über **`WordEmbeddingsRepository`**, und Lexikon-Filter über **`WordsRepositoryPort`** (ohne eigene HTTP-Route).

Tests setzen wie bisher `DATABASE_PATH` im `test_config`; `vectors.db` liegt dann implizit daneben. Beide Extensions werden mitregistriert.

## Fehlerbehandlung in der API

Die Blueprints **`words_bp`**, **`articles_bp`** und **`settings_bp`** registrieren **`errorhandler`** für **`WordServiceError`**, **`ArticleServiceError`** bzw. **`SettingsServiceError`** und antworten mit JSON `{"error": "<Nachricht>"}` und passendem Statuscode.

## Abhängigkeitsrichtung

```text
routes  →  factory / extensions
   ↓
service  →  ports (Protocol)
   ↓
repository  →  SqlDatabase
   ↓
SQLAlchemy Core (Engine, text) → sqlite3 (DBAPI)
```

`app/db` (Migrationen) hängt nicht von `app/words` ab. `app/persistence` hängt nicht von Flask ab. ``app/vectors`` lädt sqlite-vec pro DBAPI-Verbindung (siehe ``vectors_db``); ohne ladbare Extension schlägt das Anlegen von ``vectors.db`` beim Start fehl.

## Source language (Python)

Comments and docstrings in `backend/app` and `backend/tests` are **English**; see [`.agents/AGENTS.md`](../../.agents/AGENTS.md) (section *Code-Sprache*). This document may stay German for contributors; the rule applies to executable source and tests.

**Review note:** Feedback about raw ``sqlite3`` connections not being closed does not apply to the current words stack: persistence uses **SQLAlchemy** ``Engine`` / ``begin()``, which returns connections to the pool (or closes them for SQLite’s default pool) after each transaction.
