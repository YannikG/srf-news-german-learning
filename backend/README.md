# Backend

Flask backend for the SRF News German Learning app. Phase 1 ships the application factory plus a health endpoint at `GET /api/health`. Later phases extend the same factory with real blueprints.

Architektur (Schichten, Repository- und Service-Pattern, Flask-Wiring): [`docs/architecture.md`](docs/architecture.md).

## Layout

```
backend/
  app/
    bootstrap/         # create_app() wiring (factory, defaults, DB, blueprints, CLI)
    db/                # SQLite: Migrationen, Runner, init_database()
    persistence/       # SqlDatabase (SQLAlchemy Core engine for SQLite)
    health.py          # /api/health blueprint
    articles/          # Artikel-API: routes, service, repository, ports, factory
    news/              # POST /api/news/refresh (SRG ingest + Cooldown)
    words/             # Wörterbuch-API: routes, service, repository, ports, factory
    settings/          # Einstellungen-API: routes, service, repository, ports, factory
    srg_oauth/         # SRG SSR OAuth2 Client Credentials (defaults, settings, client)
    srg_articles/      # Articles API v2: models, mapping, HTTP client (Bearer GET /articles)
    sidecar/           # HTTP client for Docker sidecar (Ollama lifecycle); optional env below
    ollama/            # Idle shutdown service, poll thread, POST /api/ollama/* routes (Phase 4)
    events/            # SSE hub and GET /api/events/stream (Phase 4, P4-I03)
  docs/
    architecture.md    # Schichtenmodell und Wiring
  tests/
    conftest.py        # Flask test client fixture
    test_*_api.py      # API-Integration; test_db_schema, test_migration_runner, test_health
  wsgi.py              # gunicorn entry: `gunicorn wsgi:app`
  requirements.txt
  requirements-dev.txt
  pyproject.toml       # requires-python >=3.12, pytest, Ruff
  Dockerfile
  .dockerignore
```

## Local setup (relative to repo root)

**Python:** Mindestens **3.12** (siehe ``requires-python`` in ``pyproject.toml``; gleiche Version wie CI und Docker). Venv mit dieser Version anlegen, z. B. ``python3.12 -m venv backend/.venv``.

```bash
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt          # runtime only
pip install -r backend/requirements-dev.txt      # adds pytest and Ruff
```

On Windows PowerShell use `backend\.venv\Scripts\Activate.ps1` instead of `source ...`.

## Run the dev server

```bash
cd backend
flask --app wsgi run --host 0.0.0.0 --port 8000
# or, with gunicorn (align with Docker: ``-k gthread`` so SSE does not monopolize a whole worker,
# plus ``--timeout 0`` for long-lived streams):
gunicorn --bind 0.0.0.0:8000 -k gthread --workers 2 --threads 16 --timeout 0 wsgi:app
```

Smoke test:

```bash
curl -fsS http://localhost:8000/api/health
# {"ok":true}
```

## SRG SSR OAuth (Client Credentials, Phase 3)

Der Token-Client in `app/srg_oauth/` ruft per Default den SRG-Endpoint **`https://api.srgssr.ch/oauth/v1/accesstoken`** auf: **POST** mit leerem Body, **HTTP Basic** (Consumer Key und Secret), und **`grant_type=client_credentials` in der Query** der URL (SRG erwartet dieses Format; ein Form-Body führt typischerweise zu HTTP 400). Token-URL und User-Agent sind über Umgebungsvariablen oder Konstruktor-Argumente überschreibbar (siehe Tabelle); sinnvoll z. B. für Tests mit einem Mock-Server.

**Konfiguration (Umgebungsvariablen):**

| Variable | Bedeutung |
|----------|-----------|
| `SRGSSR_CONSUMER_KEY` | Consumer Key für Basic Auth (Pflicht, wenn Settings aus der Umgebung gebaut werden) |
| `SRGSSR_CONSUMER_SECRET` | Consumer Secret für Basic Auth (ebenfalls Pflicht in dem Fall) |
| `SRGSSR_TOKEN_URL` | Token-Endpoint-URL; Standard: `https://api.srgssr.ch/oauth/v1/accesstoken` |
| `SRGSSR_USER_AGENT` | User-Agent-Header auf Token-POSTs; Standard: `srf-news-german-learning` |

`SRGSSR_CONSUMER_KEY` und `SRGSSR_CONSUMER_SECRET` müssen gesetzt sein, sobald Code einen Client über `SrgSsrOAuthSettings()` oder `build_srg_oauth_client()` ohne explizites Settings-Objekt baut (sonst Validierungsfehler von pydantic-settings beim Start des Aufrufs). Direkt instanziiert man `SrgOAuthClient` mit `token_url=` / `user_agent=` und umgeht damit die Settings-Schicht.

**Programm-API:** `from app.srg_oauth import SrgOAuthClient`, `SrgSsrOAuthSettings`, `build_srg_oauth_client`; Zugriffstoken über `get_access_token()`. Token wird im Speicher gecacht und etwa 60 Sekunden vor Ablauf der vom Server gemeldeten Gültigkeit erneuert. Bei HTTP-Fehlern wirft `SrgOAuthHttpError` den Response-Text zusätzlich in `body`; Verbindungs- und Timeoutfehler von httpx erscheinen als `SrgOAuthClientError` mit verketteter Ursache (`__cause__`).

Für Compose oder lokale Shell: Variablen in `.env` bzw. in der Service-Umgebung setzen (keine Secrets ins Git).

## SRG News Refresh (Phase 3, P3-I03)

**Active ingest provider (Phase 8, P8-I01):** `NEWS_ACTIVE_PROVIDER` selects which upstream implementation is wired for refresh (default `srgssr` when unset). Allowed values: `srgssr`, `newsapi`; `newsapi` is reserved and fails startup until P8-I04. Each article row stores a `news_provider` slug set on upsert; `GET /api/articles` and `GET /api/settings` expose it for the UI.

`POST /api/news/refresh` holt bei freiem **Cooldown** eine Seite der SRGSSR Articles API (`publisher=SRF`, `limit=10`), mappt die Ergebnisse nach SQLite und aktualisiert `srg_sync_metadata`. Nach jedem **erfolgreichen** Abruf gilt **900 Sekunden** Sperre gegenüber weiteren Upstream-Calls; innerhalb dieses Fensters liefert die Route `fetched: false` und `next_allowed_fetch_at` (ISO-8601 mit `Z`). Der Wert **900** ist in `app/news/constants.py` als `REFRESH_COOLDOWN_SECONDS` definiert und in Tests gegen `freezegun` abgesichert.

`GET /api/articles` liest ausschliesslich aus der lokalen Datenbank und ruft SRG nicht auf.

**Zusätzliche Umgebungsvariablen (optional):**

| Variable | Bedeutung |
|----------|-----------|
| `NEWS_ACTIVE_PROVIDER` | Ingest-Slug für Refresh und `articles.news_provider`; Standard `srgssr`; `newsapi` noch nicht implementiert (P8-I04). |
| `SRGSSR_ARTICLES_BASE_URL` | Basis-URL der Articles API; Standard: `https://api.srgssr.ch/srgssr-articles/v2` |
| `SRGSSR_ARTICLES_USER_AGENT` | User-Agent für `GET /articles`; Standard: `srf-news-german-learning` |

**Tests:** In `pytest` kann ein eigener `NewsRefreshService` über `app.config["NEWS_REFRESH_SERVICE"]` injiziert werden (siehe `tests/test_news_refresh.py`).

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

## Datenbank ``vectors.db`` (Phase 5, P5-I01)

Liegt standardmässig **neben** ``app.db`` (gleiches Verzeichnis, z. B. unter ``/data`` in Compose). Beim ersten Start legt ``create_app()`` die Datei an; Schema ist ausschliesslich **sqlite-vec** (virtuelle Tabelle ``vec0``). Ohne ladbare Extension schlägt die Initialisierung mit einer klaren Fehlermeldung fehl (kein Anwendungs-Fallback). **Docker:** das Backend-Image nutzt ``python:3.12-slim-bookworm`` und das PyPI-Paket ``sqlite-vec``; lokal braucht es eine Python-Build mit SQLite-Extension-Support (oder Tests im Container).

```bash
flask --app wsgi init-vectors-db
```

## Tests

**Phase-2 layers:** API integration tests use Flask's test client (`client` in `tests/conftest.py`) against a temporary SQLite database; schema and migration tests assert SQL and the migration runner; small unit tests target pure helpers (for example migration bookkeeping validation) without HTTP.

**P7-I01 (markers, coverage, edge-case map):** see [`docs/testing-backend.md`](../docs/testing-backend.md).

**CI:** the same suite runs in GitHub Actions in [`.github/workflows/quality.yml`](../.github/workflows/quality.yml) under the job **Backend (pytest)** on pull requests and on pushes to `master` (Python 3.12, `pip install -r requirements.txt` and `-r requirements-dev.txt`, then `pytest` in `backend/`). The **Frontend** job in that workflow runs `npm ci`, `npm run build`, and `npm test` under `frontend/` plus root Prettier. No external services are required for the default test run.

Run locally from the **repository root** (parent of `backend/`) so `cd backend` is correct; then `pytest` picks up `pyproject.toml` and the `app` package.

```bash
cd backend
source .venv/bin/activate   # Unix: venv created as backend/.venv from repo root
pytest
```

On Windows PowerShell, from the repository root: `cd backend`, then `.venv\Scripts\Activate.ps1` if the venv was created as `backend/.venv` (or activate your own venv path), then run `pytest`.

If the virtual environment lives elsewhere, activate it first, then `cd backend` from the repository root and run `pytest`. Install dependencies once per [Local setup](#local-setup-relative-to-repo-root).

The health test uses Flask's test client and does not require a running container.

## Ruff (Lint und Format)

Nach `pip install -r requirements-dev.txt` (enthält eine fixierte Ruff-Version):

```bash
cd backend
ruff check .
ruff format --check .
```

Zum Anwenden der Formatter-Ausgabe: `ruff format .` Der Pre-Commit-Hook nutzt fest **`backend/.venv/bin/python -m ruff`** (siehe `lint-staged` im Root-`package.json`); das venv muss also unter `backend/.venv` liegen. Details und Prettier stehen im Root-[`README.md`](../README.md) im Abschnitt „Linting und Formatierung“.

## Docker

The `web` image is built from the **repository root** (`compose.yaml` uses `context: .` and `dockerfile: backend/Dockerfile`). A **Node** stage runs `npm ci` and `npm run build` in `frontend/`, then copies `dist/` into `app/static/spa/` inside the Python image. Flask serves `GET /` and client-side routes when `index.html` is present there; `/api/*` is unchanged.

The image entrypoint (`docker-entrypoint-web.sh`) ensures the Compose volume mount **`/data`** is writable by the non-root app user before starting Gunicorn (named volumes are often root-owned on first mount).

Override the on-disk SPA directory with **`STATIC_SPA_DIR`** (absolute path). When `index.html` is missing (typical local `pytest` tree), no SPA routes are registered and `GET /` returns `404`.

The runtime image is **Debian slim (glibc)** so the ``sqlite-vec`` wheel from PyPI loads; Alpine/musl is not used here. After `docker compose up -d` the health endpoint is reachable on the mapped port:

```bash
curl -fsS http://localhost:8000/api/health
```

**Docker sidecar (Phase 4, P4-I01):** Compose sets `SIDECAR_BASE_URL` and `SIDECAR_SHARED_SECRET` on `web`. When `SIDECAR_BASE_URL` is non-empty, `GET /api/health` adds a `sidecar` field (`status` `ok` / `error` against `GET …/ollama/inspect`). On success, `sidecar.ollama` may include `state` and `name` from the sidecar inspect JSON (Docker container status, safe for the UI). Local `pytest` leaves these unset unless a test passes `test_config`, so the default JSON stays `{"ok": true}`. API reference: [`docs/sidecar-api.md`](../docs/sidecar-api.md).

**Embeddings and retrieval (Phase 5, P5-I02):** set **`OLLAMA_BASE_URL`** in the environment to the Ollama HTTP origin your process can reach (Compose sets this on `web` to the stack-internal service, see root `compose.yaml`; local tests use `test_config`). There is no hardcoded default in application code. `build_lexicon_retrieval_service(app)` raises if it is missing when you build the service. The factory caches one `LexiconRetrievalService` per Flask app (see `LEXICON_RETRIEVAL_SERVICE_KEY` in `app/retrieval/factory.py`) so the Ollama `httpx` client is reused. It optionally triggers `POST …/ollama/start` on the sidecar when `SIDECAR_BASE_URL` is set, then wraps the call in `OllamaIdleService.begin_request` / `end_request`. Settings include `retrieval_top_k` and `retrieval_context_max_chars` (API `GET/PATCH /api/settings`). There is no dedicated REST route for retrieval yet; callers use the service from application code.

**Article simplify (Phase 5, P5-I03):** `POST /api/articles/{id}/simplify` with JSON body `{"cefr_level":"B1"}` runs lexicon retrieval, streams the simplify model over Ollama `/api/chat`, publishes **`llm_chunk`** and **`llm_done`** on `GET /api/events/stream`, and persists rows in `app.db` plus embeddings for new suggested words in `vectors.db`. Override the chat model with **`OLLAMA_SIMPLIFY_MODEL`** (default `gemma4:e2b` in `apply_default_config`).

**Ollama idle shutdown (Phase 4, P4-I02):** When `SIDECAR_BASE_URL` is set, the app arms an idle timer after the last tracked Ollama request ends (`OllamaIdleService.end_request`, used by the retrieval service and any future Ollama traffic). Defaults: `OLLAMA_IDLE_SHUTDOWN_SECONDS=600`, `OLLAMA_SHUTDOWN_WARNING_SECONDS=60`. Non-integer or missing values fall back to those defaults; idle duration is at least 1 second; the warning offset is clamped between `0` and the idle duration (inclusive). A background thread calls `poll()` about once per second (disabled when `TESTING` is true, or set `OLLAMA_IDLE_START_POLL_THREAD` explicitly). Listeners on the warning moment are for internal use (SSE in P4-I03). REST: `POST /api/ollama/cancel-idle-shutdown` clears the idle deadline; `POST /api/ollama/go-to-sleep` calls `POST …/ollama/stop` on the sidecar immediately; `POST /api/ollama/start` calls `POST …/ollama/start` on the sidecar to start the Ollama container again (for example after go-to-sleep) and publishes an `ollama_state` SSE snapshot on success. If `go-to-sleep` is invoked while a request is still tracked as active, this is a **hard stop**: the container is stopped and in-flight work fails. Without `SIDECAR_BASE_URL`, cancel still returns `200`; go-to-sleep returns `503` with `sidecar_not_configured`.

**SSE event stream (Phase 4, P4-I03):** `GET /api/events/stream` returns `text/event-stream`. Events include `ollama_state` (JSON snapshot: `idle_enabled`, `refcount`, `idle_shutdown_armed`, `idle_warning_issued`, no secrets), `shutdown_warning` with `warning_seconds`, and `shutdown_cancelled` when `POST /api/ollama/cancel-idle-shutdown` runs. During `POST /api/articles/{id}/simplify`, the hub also emits **`llm_chunk`** (payload includes `article_id`, `delta`) and **`llm_done`** (`article_id`, `cefr_level`, `simplification_id`). After a successful **`POST /api/ollama/start`**, a short-lived background loop publishes **`ollama_container`** with Docker ``state`` / ``name`` from sidecar inspect until the container is ``running`` or the loop ends (so clients can refresh without WebSockets). The hub sends a periodic SSE comment line ``: ping`` as a keepalive (default interval 15s). **Clients:** the browser `EventSource` API reconnects automatically after a dropped connection; for flaky networks or error responses, apply a short delay or exponential backoff before retrying non-SSE calls. **Gunicorn:** long-lived SSE ties up a sync worker; the default worker ``timeout`` (30s) can kill the worker during an idle stretch and log ``WORKER TIMEOUT``. The Docker image runs Gunicorn with ``--timeout 0``; for ad-hoc ``gunicorn wsgi:app``, pass ``--timeout 0`` or set ``timeout`` higher than the ping interval. **CORS:** when a global CORS policy is added for REST, apply the same rules to this path (today there is no Flask CORS middleware; same-origin usage is the default).

**Multi-process (Gunicorn workers):** Idle state lives in process memory. Each worker has its own refcount and timer, so one worker can idle-stop Ollama while another worker still serves traffic. For accurate cross-traffic idle behavior, run **one** worker (`--workers 1`) until a shared coordinator (for example in the sidecar) exists. Within one worker, ``poll`` calls the sidecar stop while holding the idle service lock after re-checking refcount and an internal epoch, so ``begin_request`` cannot interleave between the check and the stop; new callers block until the stop HTTP call finishes.
