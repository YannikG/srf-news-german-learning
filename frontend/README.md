# Frontend

Vue 3, Vite, TypeScript, Tailwind 4, PrimeVue mit Aura-Preset aus `@primeuix/themes`. Router-Grundgerüst und mobile-first App-Shell; News-Logik folgt in späteren Issues.

## Voraussetzungen

- Node 20+ (siehe GitHub Actions `quality.yml`)
- Für API-Aufrufe im Dev-Modus: laufendes Backend auf Port 8000 (oder `VITE_DEV_API_PROXY_TARGET` setzen)

## Befehle

```bash
npm ci
npm run dev
npm run build
npm test
```

`npm run build` führt `vue-tsc --noEmit` und `vite build` aus; Ausgabe liegt in `dist/`.

## Konfiguration

Siehe [`.env.example`](.env.example). `VITE_API_BASE_URL` ist optional (leer = gleiche Origin, z. B. im `web`-Container mit eingebettetem `dist`).

## SSE (`GET /api/events/stream`)

Die App-Shell öffnet einen Browser-`EventSource` auf `/api/events/stream` (über denselben API-Base-Mechanismus wie `fetch`). Ereignisse: `ollama_state`, `shutdown_warning`, `shutdown_cancelled`, `llm_chunk`, `llm_done` (siehe Backend-README).

**Reconnect:** Nach Verbindungsabbruch verbindet `EventSource` automatisch erneut. Bei dauerhaftem Fehler (z. B. 503) bleibt der Kanal zu; für REST-Aufrufe bei instabilem Netz kurze Wartezeit oder exponentielles Backoff anwenden.

**Manuelle Checks:**

- Zweiter Browser-Tab: zwei parallele SSE-Verbindungen zum selben Hub sind unkritisch.
- Netzwerk-Flap: DevTools → Offline kurz schalten, wieder Online; erwarten, dass der Stream wieder aufbaut (ggf. kurze Verzögerung).

## Docker

Das `web`-Image baut den Client im Multi-Stage-Build und legt die Dateien unter `app/static/spa` im Backend-Paket ab. Details: [`../backend/README.md`](../backend/README.md) (Abschnitt Docker).
