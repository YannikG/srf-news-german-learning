# Backend-Architektur: Schichten und Wiring

## Überblick

Das Backend trennt **HTTP**, **Anwendungslogik** und **Persistenz**:

| Schicht | Rolle | Beispiel |
|--------|--------|----------|
| **Routes** (Flask-Blueprint) | Request parsen, Statuscodes und JSON; keine Geschäftsregeln | `app/words/routes.py` |
| **Service** | Validierung, Fehler semantisch (z. B. 404), Orchestrierung | `app/words/service.py` |
| **Repository** | SQL und Tabellen-Mapping; keine HTTP-Kenntnis | `app/words/repository.py` |
| **Datenbank-Hülle** | SQLAlchemy-``Engine`` (Core, kein ORM), ``PRAGMA foreign_keys``, Transaktionen via ``begin()`` | `app/persistence/sqlite_db.py` |

Migrationen und idempotentes Anlegen der Datei bleiben in `app/db/` (stdlib-``sqlite3``, SQL-Dateien). **Repositories** sprechen dieselbe Datei über **SQLAlchemy 2.0 Core** (`Engine`, `text()`, gebundene Parameter, ``RowMapping`` → ``dict``), ohne Mapper-Klassen für Entitäten.

**Hinweis:** Pro Repository-Operation ``with db.begin() as conn:`` — entspricht einer Transaktion mit Commit bei Erfolg und Rollback bei Fehler (ersetzt das frühere manuelle ``commit()`` auf roher ``sqlite3``-Connection).

## Repository-Pattern

- **`WordsRepositoryPort`** (`app/words/ports.py`): `typing.Protocol` beschreibt die Methoden, die der **WordsService** von der Persistenz erwartet. So bleibt der Service testbar und unabhängig von SQLite-Details.
- **`SqliteWordsRepository`** (`app/words/repository.py`): konkrete Implementierung; erhält `SqlDatabase`, pro Operation ``with db.begin() as conn`` und ``conn.execute(text(...), params)``.

Neue Tabellen: eigenes `…RepositoryPort` + `Sqlite…Repository`, Service darauf aufbauen.

## Service-Pattern

**`WordsService`** erhält im Konstruktor ein Objekt, das `WordsRepositoryPort` erfüllt. Er validiert Eingaben, wirft bei Regelverletzungen **`WordServiceError`** (mit HTTP-Status), mappt keine SQL-Strings.

## Flask-Wiring

1. In **`create_app`** (`app/__init__.py`): sobald `DATABASE_PATH` gesetzt ist, wird **`SqlDatabase`** erzeugt und unter dem Schlüssel aus **`SQL_DATABASE_EXTENSION_KEY`** (aktuell `"sql_database"`) in **`app.extensions`** abgelegt.
2. Routen holen die Instanz mit **`current_app.extensions[…]`** und rufen **`build_words_service(db)`** (`app/words/factory.py`) auf. Das ist die **einzige** Fabrik-Stelle, an der Service und Repository zusammengesteckt werden (kein verstecktes `new` in den Views).

Tests setzen wie bisher `DATABASE_PATH` im `test_config`; die Extension wird automatisch mitregistriert.

## Fehlerbehandlung in der API

Der Blueprint **`words_bp`** registriert einen **`errorhandler`** für **`WordServiceError`** und antwortet mit JSON `{"error": "<Nachricht>"}` und passendem Statuscode.

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

`app/db` (Migrationen) hängt nicht von `app/words` ab. `app/persistence` hängt nicht von Flask ab.

## Source language (Python)

Comments and docstrings in `backend/app` and `backend/tests` are **English**; see [`.agents/AGENTS.md`](../../.agents/AGENTS.md) (section *Code-Sprache*). This document may stay German for contributors; the rule applies to executable source and tests.

**Review note:** Feedback about raw ``sqlite3`` connections not being closed does not apply to the current words stack: persistence uses **SQLAlchemy** ``Engine`` / ``begin()``, which returns connections to the pool (or closes them for SQLite’s default pool) after each transaction.
