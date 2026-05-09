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

Services: `web` (Flask Backend, siehe [`backend/README.md`](backend/README.md)), `ollama`, `sidecar` (Stub). Persistentes benanntes Volume `app_data` ist unter `/data` im `web`-Container eingehängt; spätere Phasen legen dort `app.db` und `vectors.db` ab.

Health-Smoketest gegen den laufenden Stack:

```bash
curl -fsS http://localhost:8000/api/health
# {"ok":true}
```

Lokales Backend-Setup (venv, `requirements.txt`, Tests) ist in [`backend/README.md`](backend/README.md) dokumentiert.

## Roadmap

Die Roadmap ist unter [`docs/roadmap/README.md`](docs/roadmap/README.md) eingestiegen; die Master-Tabelle steht in [`docs/roadmap/overview.md`](docs/roadmap/overview.md). SRG Articles API v2: [`docs/srg-articles-api.md`](docs/srg-articles-api.md) und OpenAPI unter [`docs/api/`](docs/api/). Optional PONS Wörterbuch-API: [`docs/pons-dictionary-api.md`](docs/pons-dictionary-api.md). Für Agenten: zuerst [`.agents/AGENTS.md`](.agents/AGENTS.md) und [`docs/agents-docs/README.md`](docs/agents-docs/README.md) lesen.
