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

Services: `web` (Flask-Backend plus gebautes Vue-Frontend im selben Image, siehe [`backend/README.md`](backend/README.md)), `ollama`, `sidecar` (HTTP-API für Start/Stop/Inspect von Ollama über den Docker-Socket, nur im Sidecar). API und `curl`-Beispiele: [`docs/sidecar-api.md`](docs/sidecar-api.md). Der `web`-Service erhält `OLLAMA_BASE_URL` (Standard in `compose.yaml`: `http://ollama:11434` auf dem Compose-Netzwerk; überschreibbar mit Umgebungsvariable `OLLAMA_BASE_URL`). Persistentes benanntes Volume `app_data` ist unter `/data` im `web`-Container eingehängt; spätere Phasen legen dort `app.db` und `vectors.db` ab.

Health-Smoketest gegen den laufenden Stack:

```bash
curl -fsS http://localhost:8000/api/health
# {"ok":true}
```

Lokales Backend-Setup (venv, `requirements.txt`, Tests) ist in [`backend/README.md`](backend/README.md) dokumentiert.

## Frontend (Vue, Vite)

Quellcode unter [`frontend/`](frontend/README.md). Node **20** empfohlen (wie CI).

**Variante A (Repo-Root):** einmalig Frontend-Abhängigkeiten installieren, danach:

```bash
npm ci --prefix frontend
npm run dev
```

(`npm install` im Root richtet nur Husky/Prettier ein, nicht die Vue-Abhängigkeiten.)

**Variante B:** im Ordner `frontend/`:

```bash
cd frontend
npm ci
npm run dev
```

`npm run dev` startet den Vite-Dev-Server (Standardport 5173) und leitet `/api` an `http://127.0.0.1:8000` weiter. Flask muss dafür separat laufen (z. B. `docker compose up` oder lokales venv im `backend/`).

```bash
npm run build
npm test
```

(Entweder im Root wie oben, oder in `frontend/` dieselben Skriptnamen.)

Umgebungsvariablen: Beispiel [`frontend/.env.example`](frontend/.env.example). Optional `VITE_API_BASE_URL` für eine absolute API-Origin; leer bleibt gleiche Origin (Compose-`web` oder Proxy).

## Linting und Formatierung

Statische Checks laufen in GitHub Actions (Workflow [`.github/workflows/quality.yml`](.github/workflows/quality.yml)) bei jedem Pull Request und bei jedem Push auf `master` (Jobs Backend Ruff, Backend pytest, Frontend mit Prettier, Vite-Build und Vitest).

**Python (Ruff):** Backend-venv wie im [`backend/README.md`](backend/README.md) anlegen und in der Shell aktivieren. Anschliessend:

```bash
cd backend
pip install -r requirements-dev.txt
ruff check app tests wsgi.py
ruff format --check app tests wsgi.py
```

**Prettier (Frontend-Ordner `frontend/`), im Repository-Root:**

```bash
npm install
npm run format:check
# optional: gleiche Stileinstellungen anwenden
npm run format
```

**Git-Hooks (Husky, lint-staged):** einmalig nach dem Klonen im Repository-Root `npm install` ausführen. Das `prepare`-Skript richtet Husky ein. Beim Commit prüft lint-staged gestagte Backend-Pythondateien mit Ruff und Frontend-Dateien mit Prettier (Schreibmodus). Dafür muss in der Shell, in der `git commit` läuft, dasselbe **aktivierte Backend-venv** gelten wie oben, damit `ruff` im `PATH` liegt.

**Ausnahmen (nur bewusst):** `git commit --no-verify` oder einmalig `HUSKY=0 git commit ...`, wenn ein Hook blockiert und die Ursache bekannt ist.

## Roadmap

Die Roadmap ist unter [`docs/roadmap/README.md`](docs/roadmap/README.md) eingestiegen; die Master-Tabelle steht in [`docs/roadmap/overview.md`](docs/roadmap/overview.md). SRG Articles API v2: [`docs/srg-articles-api.md`](docs/srg-articles-api.md) und OpenAPI unter [`docs/api/`](docs/api/). Optional PONS Wörterbuch-API: [`docs/pons-dictionary-api.md`](docs/pons-dictionary-api.md). Für Agenten: zuerst [`.agents/AGENTS.md`](.agents/AGENTS.md) und [`docs/agents-docs/README.md`](docs/agents-docs/README.md) lesen.
