# Backend

Flask backend for the SRF News German Learning app. Phase 1 ships the application factory plus a health endpoint at `GET /api/health`. Later phases extend the same factory with real blueprints.

## Layout

```
backend/
  app/
    __init__.py        # create_app() factory
    health.py          # /api/health blueprint
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
pip install -r backend/requirements-dev.txt      # adds pytest
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

Zum Anwenden der Formatter-Ausgabe: `ruff format app tests wsgi.py`. Details und Prettier-Hooks stehen im Root-[`README.md`](../README.md) im Abschnitt „Linting und Formatierung“.

## Docker

The image is built by Compose at the repository root (see root `compose.yaml` and the root `README.md`). After `docker compose up -d` the same endpoint is reachable on the mapped port:

```bash
curl -fsS http://localhost:8000/api/health
```
