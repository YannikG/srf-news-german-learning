# Backend

Flask backend for the SRF News German Learning app. Phase 1 ships the application factory plus a health endpoint at `GET /api/health`. Later phases extend the same factory with real blueprints.

Architektur (Schichten, Repository- und Service-Pattern, Flask-Wiring): [`docs/architecture.md`](docs/architecture.md).

## Layout

```
backend/
  app/
    __init__.py        # create_app() factory
    db/                # SQLite: Migrationen, Runner, init_database()
    persistence/       # SqlDatabase (SQLAlchemy Core engine for SQLite)
    health.py          # /api/health blueprint
    words/             # dictionary API: routes, service, repository, ports, factory
  docs/
    architecture.md    # Schichtenmodell und Wiring
  tests/
    conftest.py        # Flask test client fixture
    test_health.py
  wsgi.py              # gunicorn entry: `gunicorn wsgi:app`
  requirements.txt
  requirements-dev.txt
  pyproject.toml       # pytest + Ruff-Konfiguration
  Dockerfile
  .dockerignore
```

## Local setup (relative to repo root)

```bash
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt          # runtime only
pip install -r backend/requirements-dev.txt      # adds pytest and Ruff
```

On Windows PowerShell use `backend\.venv\Scripts\Activate.ps1` instead of `source ...`.

## Run the dev server

```bash
cd backend
flask --app wsgi run --host 0.0.0.0 --port 8000
# or, with gunicorn (matches the Docker image):
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

Smoke test:

```bash
curl -fsS http://localhost:8000/api/health
# {"ok":true}
```

## Datenbank (`app.db`)

Schema und idempotente Initialisierung (Phase 2, P2-I01): Tabellen `articles`, `words`, `article_words`, `settings`, `srg_sync_metadata` plus Buchhaltung in `_migrations` (numerische `id`, `migration_id`, `applied_at`).

- **Pfad:** fest `/data/app.db` (gleicher Mount wie in `compose.yaml` unter `/data` im `web`-Service). `pytest` setzt `DATABASE_PATH` auf eine temporäre Datei.
- **Beim Start:** Existiert die Datei unter `DATABASE_PATH` noch nicht, legt `create_app()` sie inklusive Schema an. Existiert sie schon, bleibt sie unangetastet (kein automatisches Nachziehen neuer Migrationen bei jedem Start; das wäre mehrfach bei mehreren Workern und verdeckt Deploy-Schritte). Nach einem Deploy mit neuen SQL-Dateien: `flask init-db` ausführen.
- **Migrationen:** SQL-Dateien unter `app/db/sql/`, lexikographisch nach Dateiname (z. B. `001_initial.sql`, dann `002_….sql`). Pro erfolgreicher Datei eine Zeile in `_migrations` (`migration_id` entspricht dem Dateistamm ohne `.sql`). Neue Datei immer **anhängen**, bestehende Dateien nicht ändern.
- **Foreign Keys:** `PRAGMA foreign_keys = ON` gilt nur auf der Verbindung im Migrations-Runner. Sobald die App eigene DB-Verbindungen öffnet, dieselbe Pragma-Zeile pro neuer Connection setzen (z. B. in einem zentralen DB-Helfer oder `before_request`).
- **CLI:** `flask --app wsgi init-db` wendet alle ausstehenden Migrationen an (auch auf einer bestehenden Datei, z. B. nach einem Deploy).

```bash
cd backend
source .venv/bin/activate   # wie oben
flask --app wsgi init-db
```

## Tests

Run from the `backend/` directory so pytest picks up `pyproject.toml` and the `app` package:

```bash
cd backend
pytest
```

The health test uses Flask's test client and does not require a running container.

## Ruff (Lint und Format)

Nach `pip install -r requirements-dev.txt` (enthält eine fixierte Ruff-Version):

```bash
cd backend
ruff check app tests wsgi.py
ruff format --check app tests wsgi.py
```

Zum Anwenden der Formatter-Ausgabe: `ruff format app tests wsgi.py`. Der Pre-Commit-Hook ruft `ruff` direkt auf, mit **aktiviertem Backend-venv** (wie oben bei `pip install`). Details und Prettier stehen im Root-[`README.md`](../README.md) im Abschnitt „Linting und Formatierung“.

## Docker

The image is built by Compose at the repository root (see root `compose.yaml` and the root `README.md`). After `docker compose up -d` the same endpoint is reachable on the mapped port:

```bash
curl -fsS http://localhost:8000/api/health
```
