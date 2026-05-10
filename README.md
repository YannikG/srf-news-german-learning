# srf-news-german-learning

Lokale Lern-App rund um SRF-Nachrichten (Deutsch-Level, Wörterbuch, Vektoren, Ollama).

## Docker Compose (Repository-Root)

Nach dem Klonen liegt `compose.yaml` im Projektroot. Weitere `cd` in Unterordner ist für Compose nicht nötig.

```bash
docker compose config
docker compose up
docker compose up -d
docker compose down
```

Services: `web` (Flask-Backend plus gebautes Vue-Frontend im selben Image, siehe [`backend/README.md`](backend/README.md)), `ollama`, `sidecar` (HTTP-API für Start/Stop/Inspect von Ollama über den Docker-Socket, nur im Sidecar). API und `curl`-Beispiele: [`docs/sidecar-api.md`](docs/sidecar-api.md). Der `web`-Service erhält `OLLAMA_BASE_URL` (Standard in `compose.yaml`: `http://ollama:11434` auf dem Compose-Netzwerk; überschreibbar mit Umgebungsvariable `OLLAMA_BASE_URL`). Persistentes benanntes Volume `app_data` ist unter `/data` im `web`-Container eingehängt; die App legt dort bei Bedarf `app.db` und `vectors.db` an (Details im Backend-README).

Health-Smoketest gegen den laufenden Stack:

```bash
curl -fsS http://localhost:8000/api/health
# {"ok":true}
```

Lokales Backend-Setup (venv, `requirements.txt`, Tests) ist in [`backend/README.md`](backend/README.md) dokumentiert.

**Überblick:** Compose vom Root ([Docker Compose](#docker-compose-repository-root)); Python-venv und Backend-Pakete unter `backend/` (siehe Backend-README); **Tests** unten; **Umgebungsvariablen** für `web` in [`backend/.env.example`](backend/.env.example) und Compose-`environment`; persistente SQLite-Dateien **`/data/app.db`** und **`/data/vectors.db`** im `web`-Container (Volume `app_data`); für LLM und Embeddings **Ollama-Modelle** ziehen, sobald der `ollama`-Container läuft (siehe [Ollama-Modelle](#ollama-modelle-compose)).

## Frontend (Vue, Vite)

Quellcode unter [`frontend/`](frontend/README.md). Node **20** empfohlen (wie CI).

Alle Vue-/Vite-Befehle im Ordner **`frontend/`** ausführen (`npm install` im Repo-Root richtet nur Husky/Prettier ein, nicht die Vue-Abhängigkeiten):

```bash
cd frontend
npm ci
npm run dev
```

`npm run dev` startet den Vite-Dev-Server (Standardport 5173) und leitet `/api` an `http://127.0.0.1:8000` weiter. Flask muss dafür separat laufen (z. B. `docker compose up` oder lokales venv im `backend/`).

```bash
cd frontend
npm run build
npm test
```

Umgebungsvariablen: Beispiel [`frontend/.env.example`](frontend/.env.example). Optional `VITE_API_BASE_URL` für eine absolute API-Origin; leer bleibt gleiche Origin (Compose-`web` oder Proxy).

## Tests (Backend und Frontend)

**Backend** (pytest, aus dem Repo-Root; venv zuerst wie in [`backend/README.md`](backend/README.md)):

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

**Frontend** (Vitest, im Ordner `frontend/`):

```bash
cd frontend
npm ci
npm test
```

## Ollama-Modelle (Compose)

Nach `docker compose up` braucht die App lokal die Default-Modelle aus dem Backend: Embeddings **`nomic-embed-text`** ([`DEFAULT_EMBEDDING_MODEL`](backend/app/ollama/embeddings.py)), Vereinfachen **`gemma4:e2b`** (Konfiguration **`OLLAMA_SIMPLIFY_MODEL`**, Standard in [`backend/app/bootstrap/default_settings.py`](backend/app/bootstrap/default_settings.py)). Einmalig im laufenden Stack:

```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull gemma4:e2b
```

Andere Modellnamen sind über die genannten Umgebungsvariablen möglich; dann die passenden `ollama pull`-Namen verwenden.

## Linting und Formatierung

Statische Checks laufen in GitHub Actions (Workflow [`.github/workflows/quality.yml`](.github/workflows/quality.yml)) bei jedem Pull Request und bei jedem Push auf `master`. Jobs im Workflow:

| Jobname in Actions | Inhalt |
|--------------------|--------|
| Backend (Ruff) | `ruff check .` und `ruff format --check .` im Verzeichnis `backend/` |
| Backend (pytest) | `python -m pytest` in `backend/` |
| Frontend (Vitest) | `npm ci` und `npm test` in `frontend/` |
| Frontend (Prettier, build) | Root `npm ci`, in `frontend/` `npm ci` und `npm run build`, danach Root `npm run format:check` (Prettier auf `frontend/`) |

**Python (Ruff):** Backend-venv wie im [`backend/README.md`](backend/README.md) anlegen und in der Shell aktivieren. Anschliessend:

```bash
cd backend
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
```

**Prettier (Frontend-Ordner `frontend/`), im Repository-Root:**

```bash
npm install
npm run format:check
# optional: gleiche Stileinstellungen anwenden
npm run format
```

**Git-Hooks (Husky, lint-staged):** einmalig nach dem Klonen im Repository-Root `npm install` ausführen. Das `prepare`-Skript richtet Husky ein. Beim Commit prüft lint-staged gestagte Backend-Pythondateien mit **`backend/.venv/bin/python -m ruff`** (Fix und Format) und Frontend-Dateien mit Prettier (Schreibmodus). Dafür muss das Backend-venv wie in [`backend/README.md`](backend/README.md) unter **`backend/.venv`** existieren; ein aktiviertes venv in der Commit-Shell ist für manuelle `ruff`- und `pytest`-Befehle weiterhin sinnvoll.

**Ausnahmen (nur bewusst):** `git commit --no-verify` oder einmalig `HUSKY=0 git commit ...`, wenn ein Hook blockiert und die Ursache bekannt ist.

## Roadmap

Die Roadmap ist unter [`docs/roadmap/README.md`](docs/roadmap/README.md) eingestiegen; die Master-Tabelle steht in [`docs/roadmap/overview.md`](docs/roadmap/overview.md). SRG Articles API v2: [`docs/srg-articles-api.md`](docs/srg-articles-api.md) und OpenAPI unter [`docs/api/`](docs/api/). Optional PONS Wörterbuch-API: [`docs/pons-dictionary-api.md`](docs/pons-dictionary-api.md). Für Agenten: zuerst [`.agents/AGENTS.md`](.agents/AGENTS.md) und [`docs/agents-docs/README.md`](docs/agents-docs/README.md) lesen.
