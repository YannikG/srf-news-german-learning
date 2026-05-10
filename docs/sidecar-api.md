# Docker sidecar HTTP API (Ollama control)

The `sidecar` Compose service exposes a small HTTP API on port **8090** inside the stack. It is the only service that mounts the Docker socket; the `web` service calls it over HTTP.

## Base URL

- From the `web` container: `http://sidecar:8090`
- From the host (optional port mapping): `http://localhost:8090`

## Authentication

If `SIDECAR_SHARED_SECRET` is set for the sidecar (recommended), every request below except `GET /health` must include the same value in the header:

- `X-Sidecar-Token: <secret>`

If the secret is not set (development only), the sidecar does not enforce this header.

## Endpoints

### `GET /health`

Liveness probe. **No authentication.**

**Response:** `200` with body `{"ok": true}`.

### `GET /ollama/inspect`

Returns the Docker metadata for the Ollama service container in this Compose project (matched by label `com.docker.compose.service=ollama`, same network as the sidecar when possible).

**Response:** `200` with body shaped like:

```json
{
  "ollama": {
    "id": "…",
    "name": "/…-ollama-1",
    "state": "running",
    "labels": {
      "com.docker.compose.project": "…",
      "com.docker.compose.service": "ollama"
    }
  }
}
```

Errors: `401` if the secret is wrong; `404` if no container matched; `502` / `503` on Docker API failures.

### `POST /ollama/start`

Starts the Ollama container if it is not running.

**Response:** `200` with `{"ok": true, "ollama": { … }}` (same `ollama` object as inspect).

### `POST /ollama/stop`

Stops the Ollama container (`docker stop` semantics, 30 s timeout).

**Response:** `200` with `{"ok": true, "ollama": { … }}`.

## Examples

From the host (default dev secret; set `SIDECAR_SHARED_SECRET` in the environment if you override it):

```bash
curl -fsS http://localhost:8090/health
curl -fsS -H "X-Sidecar-Token: dev-sidecar-secret" http://localhost:8090/ollama/inspect
curl -fsS -X POST -H "X-Sidecar-Token: dev-sidecar-secret" http://localhost:8090/ollama/stop
curl -fsS -X POST -H "X-Sidecar-Token: dev-sidecar-secret" http://localhost:8090/ollama/start
```

From inside `web`:

```bash
docker compose exec web sh -c 'wget -qO- http://sidecar:8090/health'
```

## Compose environment

| Variable | Service | Purpose |
|----------|---------|---------|
| `SIDECAR_SHARED_SECRET` | `web`, `sidecar` | Shared token for `X-Sidecar-Token` |
| `SIDECAR_BASE_URL` | `web` | Base URL used by the app (e.g. health probe) |
| `DOCKER_COMPOSE_PROJECT` | `sidecar` | Optional fallback when matching the Ollama container by Compose project label |

Default Ollama state on `docker compose up`: the Ollama container **runs** (same as before the sidecar). To exercise `start`, stop it first, for example `docker compose stop ollama`, then call `POST /ollama/start`.
